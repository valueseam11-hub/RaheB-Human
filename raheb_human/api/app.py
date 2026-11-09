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

@app.middleware("http")
async def security_headers_and_origin_guard(request:Request,call_next):
    if request.method in {"POST","PUT","PATCH","DELETE"}:
        origin=request.headers.get("origin")
        fetch_site=request.headers.get("sec-fetch-site")
        if fetch_site=="cross-site":
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail":"Cross-site state-changing requests are not accepted."},status_code=403)
        if origin:
            from urllib.parse import urlsplit
            parsed=urlsplit(origin);target=urlsplit(str(request.base_url))
            if (parsed.scheme,parsed.netloc)!=(target.scheme,target.netloc):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail":"Cross-origin state-changing requests are not accepted."},status_code=403)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    return response

@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB_PATH,timeout=10,isolation_level="DEFERRED");con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON");con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
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
    return "pbkdf2_sha256$310000$" + salt.hex() + "$" + derived.hex()

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
    fixture_id:str=Field(pattern="^(month_end|reporting|controls)$")
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

@app.post("/api/demo/session")
def create_demo_session(response:Response):
    """Create an isolated short-lived workspace populated only with server fixtures."""
    uid="demo-"+str(uuid4())
    email=uid+"@demo.rahebhuman.invalid"
    token=secrets.token_urlsafe(48)
    expires=utcnow()+timedelta(hours=2)
    with db() as con:
        con.execute("INSERT INTO users(id,email,password_hash,created_at) VALUES(?,?,?,?)",
                    (uid,email,password_hash(secrets.token_urlsafe(32)),iso_now()))
        con.execute("INSERT INTO sessions(token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?)",
                    (digest(token),uid,expires.isoformat(),iso_now()))
    response.set_cookie(SESSION_COOKIE,token,httponly=True,secure=COOKIE_SECURE,samesite="strict",
                        max_age=7200,path="/")
    return {"authenticated":True,"mode":"synthetic_demo","expires_at":expires.isoformat(),
            "notice":"Temporary synthetic-only workspace. Do not enter personal, employer or client information."}

@app.delete("/api/demo/session")
def end_demo_session(request:Request,response:Response):
    token=request.cookies.get(SESSION_COOKIE)
    if token:
        with db() as con:
            row=con.execute("SELECT user_id FROM sessions WHERE token_hash=?",(digest(token),)).fetchone()
            if row and row["user_id"].startswith("demo-"):
                con.execute("DELETE FROM users WHERE id=?",(row["user_id"],))
            else:
                con.execute("DELETE FROM sessions WHERE token_hash=?",(digest(token),))
    response.delete_cookie(SESSION_COOKIE,path="/",secure=COOKIE_SECURE,httponly=True,samesite="strict")
    return {"ended":True}

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
DEMO_FIXTURES={
 "month_end":("Month-end reconciliation procedure","Match synthetic ledger entries to synthetic approved invoices. Flag unmatched items. Record exceptions for owner review."),
 "reporting":("Management reporting checklist","State reporting period, reconcile synthetic source totals, explain material variances and identify missing evidence."),
 "controls":("Two-person review control","A second authorized human reviews sensitive changes. Record reviewer, decision, timestamp and evidence.")
}

@app.post("/api/knowledge",status_code=201)
def submit_knowledge(body:KnowledgeIn,user=Depends(session_user)):
    if not user["id"].startswith("demo-"):
        raise HTTPException(status_code=403,detail="Personal knowledge ingestion remains disabled until approved legal documents and persistent-memory consent controls are published.")
    with db() as con:
        owned_rep(con,user["id"],body.representative_id)
        title,content=DEMO_FIXTURES[body.fixture_id]
        kid=str(uuid4());content_digest=digest(content)
        row=con.execute("SELECT COALESCE(MAX(version),0)+1 AS next FROM knowledge WHERE owner_id=? AND title=?",(user["id"],title)).fetchone()
        version=row["next"]
        con.execute("""INSERT INTO knowledge(id,owner_id,representative_id,title,source_type,source_origin,content,content_digest,data_scope,version,state,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (kid,user["id"],body.representative_id,title,"synthetic_demo","RaheB built-in fixture",content,content_digest,"demo:synthetic",version,"PENDING_OWNER_REVIEW",iso_now()))
        audit(con,user["id"],"DEMO_KNOWLEDGE_SUBMITTED",kid,{"title":title,"digest":content_digest,"state":"PENDING_OWNER_REVIEW"})
    return {"id":kid,"title":title,"content":content,"content_digest":content_digest,"data_scope":"demo:synthetic","version":version,"state":"PENDING_OWNER_REVIEW"}

@app.post("/api/knowledge/{knowledge_id}/approve")
def approve_knowledge(knowledge_id:str,user=Depends(session_user)):
    if not user["id"].startswith("demo-"):
        raise HTTPException(status_code=403,detail="Persistent personal knowledge approval is not enabled.")
    with db() as con:
        row=con.execute("SELECT * FROM knowledge WHERE id=? AND owner_id=?",(knowledge_id,user["id"])).fetchone()
        if not row:raise HTTPException(status_code=404,detail="Knowledge record not found")
        if row["state"]!="PENDING_OWNER_REVIEW":raise HTTPException(status_code=409,detail="Knowledge record is not pending review")
        if digest(row["content"])!=row["content_digest"]:raise HTTPException(status_code=409,detail="Knowledge content integrity check failed")
        con.execute("UPDATE knowledge SET state='APPROVED',reviewed_at=? WHERE id=?",(iso_now(),knowledge_id))
        audit(con,user["id"],"DEMO_KNOWLEDGE_APPROVED",knowledge_id,{"digest":row["content_digest"]})
    return {"id":knowledge_id,"state":"APPROVED"}
@app.get("/api/knowledge")
def list_knowledge(user=Depends(session_user)):
    with db() as con:rows=con.execute("SELECT id,representative_id,title,source_type,source_origin,content_digest,data_scope,version,state,created_at,reviewed_at FROM knowledge WHERE owner_id=? ORDER BY created_at DESC",(user["id"],)).fetchall()
    return [dict(row) for row in rows]
@app.post("/api/tasks",status_code=201)
def create_task(body:TaskIn,user=Depends(session_user)):
    if not user["id"].startswith("demo-"):
        raise HTTPException(status_code=403,detail="Real task processing is not enabled. No model or external action will be invoked.")
    with db() as con:
        owned_rep(con,user["id"],body.representative_id)
        sources=con.execute("SELECT * FROM knowledge WHERE owner_id=? AND representative_id=? AND state='APPROVED' AND data_scope='demo:synthetic' ORDER BY created_at",(user["id"],body.representative_id)).fetchall()
        if not sources:raise HTTPException(status_code=409,detail="No owner-approved synthetic knowledge is available.")
        labels={"reconciliation_checklist":"Reconciliation checklist draft","management_report_outline":"Management report outline","control_summary":"Control considerations summary"}
        bullets={
          "reconciliation_checklist":["Confirm reporting period and ledger extract.","Match each ledger entry to an approved invoice.","List unmatched items and supporting evidence.","Prepare exceptions for owner review."],
          "management_report_outline":["State reporting period and source scope.","Summarise reconciled totals.","Describe material variances and unresolved items.","Identify evidence gaps and decisions required."],
          "control_summary":["Identify sensitive or irreversible steps.","Require a second authorized human for sensitive changes.","Record reviewer, decision, timestamp and evidence."]
        }
        tid=str(uuid4());draft={"title":labels[body.task_type],"bullets":bullets[body.task_type],"generated_by":"deterministic_synthetic_demo","ai_model_invoked":False,"external_action_performed":False}
        source_ids=[row["id"] for row in sources]
        con.execute("""INSERT INTO tasks(id,owner_id,representative_id,task_type,request_text,draft_json,source_ids_json,state,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (tid,user["id"],body.representative_id,body.task_type,body.request_text,json.dumps(draft),json.dumps(source_ids),"AWAITING_HUMAN_REVIEW",iso_now()))
        audit(con,user["id"],"DEMO_TASK_DRAFT_CREATED",tid,{"task_type":body.task_type,"source_ids":source_ids,"state":"AWAITING_HUMAN_REVIEW"})
    return {"id":tid,**draft,"source_ids":source_ids,"state":"AWAITING_HUMAN_REVIEW"}
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
