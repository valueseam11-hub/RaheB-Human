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
from raheb_human.authority.persistence import (
    AuthorityHold, AuthorityStoreError, init_authority_schema, issue_warrant,
    revoke_warrant, approve_exact_action, admit_once, verify_authority_events,
)

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
        init_authority_schema(con)

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


class AuthorityWarrantIn(BaseModel):
    representative_id: str
    representative_version: int = Field(ge=1)
    purpose: str = Field(min_length=3, max_length=240)
    actions: list[str] = Field(min_length=1, max_length=20)
    resources: list[str] = Field(min_length=1, max_length=20)
    money_limit: str = Field(pattern=r"^\d+(?:\.\d{1,2})?$")
    token_limit: int = Field(ge=0, le=10000000)
    retry_limit: int = Field(ge=0, le=100)
    agent_limit: int = Field(ge=1, le=100)
    duration_limit_seconds: int = Field(ge=1, le=86400)
    expires_at: datetime

class AuthorityRevokeIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

class ExactApprovalIn(BaseModel):
    warrant_id: str
    action: str
    resource: str
    purpose: str
    output_digest: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    task_id: str | None = Field(default=None, max_length=100)
    expires_at: datetime

class AuthorityAdmissionIn(BaseModel):
    approval_id: str
    idempotency_key: str = Field(min_length=8, max_length=128)
    action: str
    resource: str
    purpose: str
    output_digest: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    estimated_money: str = Field(pattern=r"^\d+(?:\.\d{1,2})?$")
    estimated_tokens: int = Field(ge=0, le=10000000)
    retry_number: int = Field(default=0, ge=0, le=100)
    active_agent_count: int = Field(default=1, ge=1, le=100)
    elapsed_seconds: int = Field(default=0, ge=0, le=86400)

def require_synthetic_authority_demo(user):
    if not user["id"].startswith("demo-"):
        raise HTTPException(status_code=403, detail="Authority issuance and admission are synthetic-demo only until verified identity, durable tenant isolation and production security review are complete.")

@app.post("/api/authority/warrants", status_code=201)
def create_authority_warrant(body: AuthorityWarrantIn, user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    try:
        with db() as con:
            result = issue_warrant(
                con, owner_id=user["id"], representative_id=body.representative_id,
                representative_version=body.representative_version,
                authorizer_id=user["id"], authority_source="INDIVIDUAL_OWNER",
                purpose=body.purpose, actions=body.actions, resources=body.resources,
                limits={"money":body.money_limit,"tokens":body.token_limit,
                        "retries":body.retry_limit,"agent_count":body.agent_limit,
                        "duration_seconds":body.duration_limit_seconds},
                expires_at=body.expires_at,
            )
            audit(con,user["id"],"AUTHORITY_WARRANT_ISSUED",result["warrant_id"],
                  {"warrant_digest":result["warrant_digest"],"representative_id":body.representative_id})
        return {"status":"ISSUED","authority":result,"note":"Synthetic demonstration only; no external action is enabled."}
    except AuthorityHold as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except AuthorityStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/authority/warrants")
def list_authority_warrants(user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    with db() as con:
        rows=con.execute("""SELECT w.warrant_id,w.representative_id,w.representative_version,
          w.purpose,w.actions_json,w.resources_json,w.limits_json,w.issued_at,w.expires_at,
          w.warrant_digest,CASE WHEN r.revocation_id IS NULL THEN 0 ELSE 1 END AS revoked
          FROM authority_warrants w LEFT JOIN authority_revocations r
          ON r.owner_id=w.owner_id AND r.warrant_id=w.warrant_id
          WHERE w.owner_id=? ORDER BY w.issued_at DESC""",(user["id"],)).fetchall()
    return [{"warrant_id":r["warrant_id"],"representative_id":r["representative_id"],
             "representative_version":r["representative_version"],"purpose":r["purpose"],
             "actions":json.loads(r["actions_json"]),"resources":json.loads(r["resources_json"]),
             "limits":json.loads(r["limits_json"]),"issued_at":r["issued_at"],
             "expires_at":r["expires_at"],"warrant_digest":r["warrant_digest"],
             "revoked":bool(r["revoked"])} for r in rows]

@app.post("/api/authority/warrants/{warrant_id}/revoke", status_code=200)
def revoke_authority_warrant(warrant_id: str, body: AuthorityRevokeIn, user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    try:
        with db() as con:
            revoke_warrant(con,owner_id=user["id"],warrant_id=warrant_id,
                           revoked_by=user["id"],reason=body.reason)
            audit(con,user["id"],"AUTHORITY_WARRANT_REVOKED",warrant_id,{"reason":body.reason})
        return {"warrant_id":warrant_id,"status":"REVOKED","descendants":"will HOLD at next admission check"}
    except AuthorityHold as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@app.post("/api/authority/approvals", status_code=201)
def create_exact_approval(body: ExactApprovalIn, user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    try:
        with db() as con:
            result=approve_exact_action(con,owner_id=user["id"],approved_by=user["id"],
                warrant_id=body.warrant_id,action=body.action,resource=body.resource,
                purpose=body.purpose,output_digest=body.output_digest,task_id=body.task_id,
                expires_at=body.expires_at)
            audit(con,user["id"],"EXACT_ACTION_APPROVED",result["approval_id"],
                  {"warrant_id":body.warrant_id,"request_digest":result["request_digest"],
                   "output_digest":body.output_digest})
        return {"status":"APPROVED","approval":result,
                "note":"Approval is bound to this exact output digest and is single-use."}
    except AuthorityHold as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except AuthorityStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.post("/api/authority/admit", status_code=200)
def admit_authorized_action(body: AuthorityAdmissionIn, user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    try:
        with db() as con:
            result=admit_once(con,owner_id=user["id"],approval_id=body.approval_id,
                idempotency_key=body.idempotency_key,action=body.action,
                resource=body.resource,purpose=body.purpose,
                output_digest=body.output_digest,estimated_money=body.estimated_money,
                estimated_tokens=body.estimated_tokens,retry_number=body.retry_number,
                active_agent_count=body.active_agent_count,elapsed_seconds=body.elapsed_seconds)
            audit(con,user["id"],"AUTHORITY_ADMISSION_RESERVED",body.approval_id,
                  {"idempotency_key":body.idempotency_key,"side_effect_permitted":False})
        return result
    except AuthorityHold as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except AuthorityStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/authority/evidence/verify")
def verify_authority_evidence(user=Depends(session_user)):
    require_synthetic_authority_demo(user)
    with db() as con:
        valid=verify_authority_events(con,user["id"])
    return {"valid":valid,"scope":"synthetic-demo-owner","meaning":"Hash-chain integrity only; not proof of truth, identity or lawful authority."}

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
