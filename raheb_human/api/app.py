"""RaheB Human web/API application. Development reference; not production-hardened."""
from __future__ import annotations
import hashlib,hmac,json,os,secrets,sqlite3
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from fastapi import Depends,FastAPI,HTTPException,Request,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field

APP_ROOT=Path(__file__).resolve().parents[2]
WEB_ROOT=APP_ROOT/"web"
DB_PATH=Path(os.environ.get("RAHEB_DB_PATH",APP_ROOT/"var"/"raheb-dev.sqlite3"))
SESSION_COOKIE="raheb_session"
SESSION_TTL=timedelta(hours=12)
COOKIE_SECURE=os.environ.get("RAHEB_COOKIE_SECURE","0")=="1"
AGREEMENT_PATH=Path(os.environ.get("RAHEB_AGREEMENT_PATH",APP_ROOT/"legal"/"service-agreement.md"))
PRIVACY_PATH=Path(os.environ.get("RAHEB_PRIVACY_PATH",APP_ROOT/"legal"/"privacy-notice.md"))
SESSION_PEPPER=os.environ.get("RAHEB_SESSION_PEPPER","development-only-change-before-deployment")
PRODUCTION_CONFIGURED=SESSION_PEPPER!="development-only-change-before-deployment"
app=FastAPI(title="RaheB Human API",version="0.1.0",description="Human-owned professional representative application API. No external agent actions are enabled.",docs_url="/api/docs",redoc_url=None)

@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB_PATH,timeout=10,isolation_level=None);con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON");con.execute("PRAGMA journal_mode=WAL")
    try: yield con
    finally: con.close()

def utcnow(): return datetime.now(timezone.utc)
def iso_now(): return utcnow().isoformat()
def digest(value:str)->str: return hashlib.sha256(value.encode()).hexdigest()

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,created_at TEXT NOT NULL,disabled INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,expires_at TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS consent(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,purpose TEXT NOT NULL,granted INTEGER NOT NULL,document_version TEXT NOT NULL,document_hash TEXT NOT NULL,recorded_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS representatives(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,label TEXT NOT NULL,profession TEXT NOT NULL,version INTEGER NOT NULL,state TEXT NOT NULL,ai_disclosure TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS knowledge(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,representative_id TEXT NOT NULL REFERENCES representatives(id) ON DELETE CASCADE,title TEXT NOT NULL,source_type TEXT NOT NULL,source_origin TEXT NOT NULL,content TEXT NOT NULL,content_digest TEXT NOT NULL,data_scope TEXT NOT NULL,version INTEGER NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL,reviewed_at TEXT);
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,representative_id TEXT NOT NULL REFERENCES representatives(id) ON DELETE CASCADE,task_type TEXT NOT NULL,request_text TEXT NOT NULL,draft_json TEXT NOT NULL,source_ids_json TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL,reviewed_at TEXT,review_note TEXT);
        CREATE TABLE IF NOT EXISTS evidence(seq INTEGER PRIMARY KEY AUTOINCREMENT,owner_id TEXT NOT NULL,event_type TEXT NOT NULL,subject_id TEXT NOT NULL,payload_json TEXT NOT NULL,occurred_at TEXT NOT NULL,previous_digest TEXT NOT NULL,record_digest TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_owner_state ON knowledge(owner_id,state);
        CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner_id,created_at);
        CREATE INDEX IF NOT EXISTS idx_evidence_owner_seq ON evidence(owner_id,seq);
        """)

def audit(con,owner_id,event,subject,payload):
    row=con.execute("SELECT record_digest FROM evidence WHERE owner_id=? ORDER BY seq DESC LIMIT 1",(owner_id,)).fetchone()
    previous=row["record_digest"] if row else "GENESIS";occurred=iso_now()
    body={"owner_id":owner_id,"event_type":event,"subject_id":subject,"payload":payload,"occurred_at":occurred,"previous_digest":previous}
    record_digest=digest(json.dumps(body,sort_keys=True,separators=(",",":")))
    con.execute("INSERT INTO evidence(owner_id,event_type,subject_id,payload_json,occurred_at,previous_digest,record_digest) VALUES(?,?,?,?,?,?,?)",
                (owner_id,event,subject,json.dumps(payload,sort_keys=True),occurred,previous,record_digest))

def verify_evidence(con,owner_id):
    previous="GENESIS"
    for row in con.execute("SELECT * FROM evidence WHERE owner_id=? ORDER BY seq",(owner_id,)).fetchall():
        body={"owner_id":row["owner_id"],"event_type":row["event_type"],"subject_id":row["subject_id"],"payload":json.loads(row["payload_json"]),"occurred_at":row["occurred_at"],"previous_digest":row["previous_digest"]}
        expected=digest(json.dumps(body,sort_keys=True,separators=(",",":")))
        if row["previous_digest"]!=previous or not hmac.compare_digest(expected,row["record_digest"]): return False
        previous=row["record_digest"]
    return True

def password_hash(password,salt=None):
    salt=salt or secrets.token_bytes(16);derived=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return f"pbkdf2_sha256$310000$\\{salt.hex()}$\\{derived.hex()}"

def password_matches(password,stored):
    try:
        algorithm,rounds,salt_hex,expected=stored.split("$")
        if algorithm!="pbkdf2_sha256" or int(rounds)!=310000:return False
        actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),int(rounds)).hex()
        return hmac.compare_digest(actual,expected)
    except (ValueError,TypeError):return False

def legal_status():
    agreement=AGREEMENT_PATH.is_file();privacy=PRIVACY_PATH.is_file()
    return {"published":agreement and privacy,"agreement_available":agreement,"privacy_notice_available":privacy,"account_creation_enabled":False,"reason":"The approved service agreement and privacy notice have not been supplied and published."}

def session_user(request:Request):
    token=request.cookies.get(SESSION_COOKIE)
    if not token:raise HTTPException(status_code=401,detail="Authentication required")
    with db() as con:
        row=con.execute("SELECT u.id,u.email,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND u.disabled=0",(digest(token),)).fetchone()
    if not row or datetime.fromisoformat(row["expires_at"])<=utcnow():raise HTTPException(status_code=401,detail="Session expired or invalid")
    return {"id":row["id"],"email":row["email"]}

class RegisterIn(BaseModel):
    email:str=Field(min_length=5,max_length=254)
    password:str=Field(min_length=12,max_length=128)
class LoginIn(BaseModel):
    email:str
    password:str
class RepresentativeIn(BaseModel):
    label:str=Field(min_length=2,max_length=80)
    profession:str=Field(min_length=2,max_length=100)
class KnowledgeIn(BaseModel):
    representative_id:str
    title:str=Field(min_length=2,max_length=160)
    source_type:str=Field(min_length=2,max_length=50)
    source_origin:str=Field(min_length=2,max_length=160)
    content:str=Field(min_length=1,max_length=100000)
    data_scope:str=Field(min_length=2,max_length=100)
class TaskIn(BaseModel):
    representative_id:str
    task_type:str=Field(pattern="^(reconciliation_checklist|management_report_outline|control_summary)$")
    request_text:str=Field(min_length=4,max_length=2000)
class ReviewIn(BaseModel):
    decision:str=Field(pattern="^(approve_draft|reject_draft)$")
    note:str=Field(default="",max_length=1000)

@app.on_event("startup")
def startup():init_db()

@app.get("/api/health")
def health():return {"status":"ok","service":"raheb-human-api","version":"0.1.0","mode":"development-reference" if not PRODUCTION_CONFIGURED else "configured-reference","external_actions_enabled":False}
@app.get("/api/public-config")
def public_config():return {"product":"RaheB Human","ai_disclosure":"This is an AI representative, not the human owner.","legal":legal_status(),"account_creation_enabled":False,"personal_data_upload_enabled":False,"external_actions_enabled":False}
@app.get("/api/legal-status")
def get_legal_status():return legal_status()
@app.post("/api/auth/register",status_code=403)
def register(_:RegisterIn):raise HTTPException(status_code=403,detail="Account creation is disabled until the approved service agreement and privacy notice are published and reviewed.")
@app.post("/api/auth/login")
def login(body:LoginIn,response:Response):
    with db() as con:
        row=con.execute("SELECT * FROM users WHERE email=? AND disabled=0",(body.email.strip().lower(),)).fetchone()
        if not row or not password_matches(body.password,row["password_hash"]):raise HTTPException(status_code=401,detail="Email or password is incorrect")
        token=secrets.token_urlsafe(48);expires=utcnow()+SESSION_TTL
        con.execute("INSERT INTO sessions(token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?)",(digest(token),row["id"],expires.isoformat(),iso_now()))
    response.set_cookie(SESSION_COOKIE,token,httponly=True,secure=COOKIE_SECURE,samesite="strict",max_age=int(SESSION_TTL.total_seconds()),path="/")
    return {"authenticated":True,"user":{"id":row["id"],"email":row["email"]},"expires_at":expires.isoformat()}
@app.post("/api/auth/logout")
def logout(request:Request,response:Response):
    token=request.cookies.get(SESSION_COOKIE)
    if token:
        with db() as con:con.execute("DELETE FROM sessions WHERE token_hash=?",(digest(token),))
    response.delete_cookie(SESSION_COOKIE,path="/",secure=COOKIE_SECURE,httponly=True,samesite="strict")
    return {"authenticated":False}
@app.get("/api/auth/me")
def me(user=Depends(session_user)):return {"user":user,"authenticated":True}
@app.post("/api/representatives",status_code=201)
def create_representative(body:RepresentativeIn,user=Depends(session_user)):
    rid=str(uuid4())
    with db() as con:
        con.execute("INSERT INTO representatives(id,owner_id,label,profession,version,state,ai_disclosure,created_at) VALUES(?,?,?,?,?,?,?,?)",(rid,user["id"],body.label,body.profession,1,"DRAFT","This is an AI representative, not the human owner.",iso_now()))
        audit(con,user["id"],"REPRESENTATIVE_CREATED",rid,{"profession":body.profession,"state":"DRAFT"})
    return {"id":rid,"label":body.label,"profession":body.profession,"version":1,"state":"DRAFT","ai_disclosure":"This is an AI representative, not the human owner.","note":"Draft only. No authority, model access or external actions are enabled."}
@app.get("/api/representatives")
def list_representatives(user=Depends(session_user)):
    with db() as con:rows=con.execute("SELECT id,label,profession,version,state,ai_disclosure,created_at FROM representatives WHERE owner_id=? ORDER BY created_at DESC",(user["id"],)).fetchall()
    return [dict(row) for row in rows]
def owned_rep(con,owner_id,rep_id):
    row=con.execute("SELECT * FROM representatives WHERE id=? AND owner_id=?",(rep_id,owner_id)).fetchone()
    if not row:raise HTTPException(status_code=404,detail="Representative not found")
    return row
@app.post("/api/knowledge",status_code=201)
def submit_knowledge(body:KnowledgeIn,user=Depends(session_user)):
    with db() as con:owned_rep(con,user["id"],body.representative_id)
    raise HTTPException(status_code=403,detail="Knowledge ingestion is disabled until approved legal documents and separate persistent-memory consent are live.")
@app.get("/api/knowledge")
def list_knowledge(user=Depends(session_user)):
    with db() as con:rows=con.execute("SELECT id,representative_id,title,source_type,source_origin,content_digest,data_scope,version,state,created_at,reviewed_at FROM knowledge WHERE owner_id=? ORDER BY created_at DESC",(user["id"],)).fetchall()
    return [dict(row) for row in rows]
@app.post("/api/tasks",status_code=201)
def create_task(body:TaskIn,user=Depends(session_user)):
    with db() as con:
        rep=owned_rep(con,user["id"],body.representative_id)
        if rep["state"]!="ACTIVE":raise HTTPException(status_code=409,detail="Representative is not active; task admission is on HOLD.")
    raise HTTPException(status_code=403,detail="Task execution is not enabled in this build. No model or external action will be invoked.")
@app.get("/api/tasks")
def list_tasks(user=Depends(session_user)):
    with db() as con:rows=con.execute("SELECT id,representative_id,task_type,request_text,draft_json,source_ids_json,state,created_at,reviewed_at,review_note FROM tasks WHERE owner_id=? ORDER BY created_at DESC",(user["id"],)).fetchall()
    return [dict(row) for row in rows]
@app.post("/api/tasks/{task_id}/review")
def review_task(task_id:str,body:ReviewIn,user=Depends(session_user)):
    with db() as con:
        row=con.execute("SELECT * FROM tasks WHERE id=? AND owner_id=?",(task_id,user["id"])).fetchone()
        if not row:raise HTTPException(status_code=404,detail="Task not found")
        if row["state"]!="AWAITING_HUMAN_REVIEW":raise HTTPException(status_code=409,detail="Task is not awaiting review")
        state="HUMAN_REVIEWED_DRAFT" if body.decision=="approve_draft" else "REJECTED_BY_HUMAN"
        con.execute("UPDATE tasks SET state=?,reviewed_at=?,review_note=? WHERE id=?",(state,iso_now(),body.note,task_id))
        audit(con,user["id"],"TASK_DRAFT_REVIEWED",task_id,{"decision":body.decision,"state":state})
    return {"id":task_id,"state":state,"external_action_performed":False}
@app.get("/api/evidence")
def evidence(user=Depends(session_user)):
    with db() as con:
        rows=con.execute("SELECT seq,event_type,subject_id,payload_json,occurred_at,previous_digest,record_digest FROM evidence WHERE owner_id=? ORDER BY seq",(user["id"],)).fetchall()
        valid=verify_evidence(con,user["id"])
    return {"integrity_valid":valid,"records":[{**dict(row),"payload":json.loads(row["payload_json"])} for row in rows],"integrity_note":"Hash linkage detects alteration relative to this database chain; it does not prove truth or independent attestation."}
@app.get("/app")
def app_page():return FileResponse(WEB_ROOT/"app.html")
@app.get("/")
def home_page():return FileResponse(WEB_ROOT/"index.html")
if WEB_ROOT.exists():app.mount("/",StaticFiles(directory=WEB_ROOT,html=True),name="web-assets")
