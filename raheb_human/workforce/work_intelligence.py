"""Fail-closed workforce task assessment and human-supervised workbench.

Deterministic policy scaffolding, not an AI model or execution agent.
Unknown tasks remain on HOLD until a qualified human defines their scope.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib, hmac, json
from typing import Iterable

class TaskCategory(str, Enum):
    ROUTINE="ROUTINE_RULE_BASED"; RESEARCH="RESEARCH_PREPARATION"
    JUDGMENT="PROFESSIONAL_JUDGMENT"; HIGH_IMPACT="HIGH_IMPACT_DECISION"
    HUMAN_INTERACTION="HUMAN_INTERACTION"; UNKNOWN="UNKNOWN"
class RiskLevel(str, Enum):
    LOW="LOW"; MODERATE="MODERATE"; HIGH="HIGH"; CRITICAL="CRITICAL"; UNKNOWN="UNKNOWN"
class DelegationMode(str, Enum):
    PREPARE_ONLY="PREPARE_ONLY"; SUPERVISED_EXECUTION="SUPERVISED_EXECUTION"
    HUMAN_OWNED="HUMAN_OWNED"; HOLD="HOLD"

@dataclass(frozen=True)
class TaskInput:
    task_id: str; title: str; description: str; profession: str
    data_scopes: frozenset[str]=frozenset()
    involves_external_commitment: bool=False; irreversible: bool=False
    affects_rights_or_eligibility: bool=False; safety_critical: bool=False
    requires_empathy_or_negotiation: bool=False; known_procedure: bool=False
    human_owner_id: str=""; employer_id: str|None=None
    def __post_init__(self):
        for n in ("task_id","title","description","profession","human_owner_id"):
            if not getattr(self,n).strip(): raise ValueError(f"{n} is required")
        if len(self.description)>8000: raise ValueError("description exceeds 8000 characters")

@dataclass(frozen=True)
class TaskAssessment:
    task_id: str; category: TaskCategory; risk: RiskLevel; delegation: DelegationMode
    reasons: tuple[str,...]; human_responsibility: str; required_controls: tuple[str,...]
    policy_version: str="work-intelligence-v0.1"
    @property
    def can_run_without_human_review(self)->bool: return False

_HIGH= ("hire","fire","terminate employment","dismiss employee","promote","credit decision","loan approval","deny benefit","medical diagnosis","treatment decision","legal filing","sign contract","transfer funds","payment release","disciplinary action","eligibility decision")
_JUDGMENT=("approve","recommend","investigate","reconcile","variance","exception","forecast","risk assessment","materiality","interpret","audit finding")
_RESEARCH=("research","summarise","summarize","prepare report","draft report","meeting brief","compare documents","extract information","prepare presentation")
_ROUTINE=("format","sort","categorise","categorize","schedule","transcribe","check completeness","data entry","classify records","compile list")

def assess_task(task: TaskInput)->TaskAssessment:
    text=f"{task.title} {task.description}".casefold()
    controls=["Use only approved data scopes","Show sources and limitations","Keep an auditable human/AI contribution record","No external side effects in this reference implementation"]
    if task.safety_critical or task.irreversible or task.affects_rights_or_eligibility or task.involves_external_commitment or any(t in text for t in _HIGH):
        category,risk,mode=TaskCategory.HIGH_IMPACT,RiskLevel.CRITICAL,DelegationMode.HUMAN_OWNED
        reasons=["Consequential, externally committing, irreversible, rights-affecting or high-impact task pattern."]
        controls += ["Human decision-maker retains the decision","Require explicit task-bound human approval before any future permitted side effect","Escalate to qualified accountable personnel"]
        responsibility="The accountable human retains the decision and professional responsibility."
    elif task.requires_empathy_or_negotiation:
        category,risk,mode=TaskCategory.HUMAN_INTERACTION,RiskLevel.HIGH,DelegationMode.HUMAN_OWNED
        reasons=["Requires human relationship, empathy, negotiation or context-sensitive interaction."]
        controls += ["AI may prepare context only; human conducts and owns the interaction"]
        responsibility="The human owns the relationship, communication and outcome."
    elif any(t in text for t in _JUDGMENT):
        category,risk,mode=TaskCategory.JUDGMENT,RiskLevel.HIGH,DelegationMode.PREPARE_ONLY
        reasons=["Contains interpretation, investigation, exception handling or professional judgment."]
        controls += ["AI may organise evidence and propose options, not decide the exception","Human verifies source material and reasoning"]
        responsibility="The professional evaluates evidence, resolves exceptions and makes the judgment."
    elif any(t in text for t in _RESEARCH):
        category,risk,mode=TaskCategory.RESEARCH,RiskLevel.MODERATE,DelegationMode.PREPARE_ONLY
        reasons=["Research or preparation output requires source review and professional validation."]
        controls += ["Cite source references and label unsupported or missing information"]
        responsibility="The professional validates accuracy, relevance and final recommendations."
    elif task.known_procedure and any(t in text for t in _ROUTINE):
        category,risk,mode=TaskCategory.ROUTINE,RiskLevel.LOW,DelegationMode.SUPERVISED_EXECUTION
        reasons=["Matches a declared known procedure and bounded routine task pattern."]
        controls += ["Run only within declared procedure and approved data scope","Stop on exception, missing source or scope mismatch"]
        responsibility="Human owner remains accountable for supervision and exceptions."
    else:
        category,risk,mode=TaskCategory.UNKNOWN,RiskLevel.UNKNOWN,DelegationMode.HOLD
        reasons=["Cannot safely classify from supplied description and procedure evidence."]
        controls += ["Do not delegate or execute","Human must define scope, risk and acceptance criteria"]
        responsibility="No delegation until an accountable human resolves uncertainty."
    if not task.data_scopes:
        mode,risk=DelegationMode.HOLD,RiskLevel.UNKNOWN
        reasons.append("No approved data scope was supplied; fail closed.")
        controls.append("Obtain purpose-specific data permission before retrieval")
    return TaskAssessment(task.task_id,category,risk,mode,tuple(reasons),responsibility,tuple(dict.fromkeys(controls)))

@dataclass(frozen=True)
class EvidenceReference:
    source_id:str; source_digest:str; source_version:str; scope:str
    def __post_init__(self):
        if not all((self.source_id,self.source_digest,self.source_version,self.scope)): raise ValueError("Evidence reference fields must be non-empty")

@dataclass(frozen=True)
class ApprovalBinding:
    task_id:str; task_digest:str; draft_digest:str; owner_id:str; reviewer_id:str
    representative_version:str; authority_version:str; expires_at:datetime; nonce:str

def _digest(payload:dict)->str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def create_approval_binding(*,task_id:str,task_digest:str,draft_digest:str,owner_id:str,reviewer_id:str,representative_version:str,authority_version:str,expires_at:datetime,nonce:str)->ApprovalBinding:
    if expires_at.tzinfo is None: raise ValueError("expires_at must be timezone-aware")
    if not all((task_id,task_digest,draft_digest,owner_id,reviewer_id,representative_version,authority_version,nonce)): raise ValueError("Approval binding fields must be non-empty")
    return ApprovalBinding(task_id,task_digest,draft_digest,owner_id,reviewer_id,representative_version,authority_version,expires_at,nonce)

def verify_approval_binding(binding:ApprovalBinding,*,task_id:str,task_digest:str,draft_digest:str,owner_id:str,reviewer_id:str,representative_version:str,authority_version:str,now:datetime,consumed_nonces:Iterable[str]=())->bool:
    """Caller must atomically consume nonce in durable storage."""
    if now.tzinfo is None or binding.expires_at<=now or binding.nonce in set(consumed_nonces): return False
    expected=(binding.task_id,binding.task_digest,binding.draft_digest,binding.owner_id,binding.reviewer_id,binding.representative_version,binding.authority_version)
    supplied=(task_id,task_digest,draft_digest,owner_id,reviewer_id,representative_version,authority_version)
    return hmac.compare_digest(_digest({"v":expected}),_digest({"v":supplied}))

@dataclass(frozen=True)
class WorkDraft:
    task_id:str; title:str; content:str; evidence:tuple[EvidenceReference,...]
    limitations:tuple[str,...]; created_at:datetime; draft_digest:str

class HumanAIWorkbench:
    """Evidence-first draft preparation. It never executes or sends work."""
    def prepare(self,task:TaskInput,assessment:TaskAssessment,*,title:str,content:str,evidence:tuple[EvidenceReference,...],now:datetime|None=None)->WorkDraft:
        if assessment.task_id!=task.task_id: raise ValueError("Assessment does not belong to task")
        if assessment.delegation in {DelegationMode.HOLD,DelegationMode.HUMAN_OWNED}: raise PermissionError("Task is not eligible for AI draft preparation")
        if not evidence: raise PermissionError("A work draft requires at least one evidence reference")
        if any(ref.scope not in task.data_scopes for ref in evidence): raise PermissionError("Evidence scope is outside approved task scopes")
        if not title.strip() or not content.strip(): raise ValueError("Draft title and content are required")
        created=now or datetime.now(timezone.utc)
        if created.tzinfo is None: raise ValueError("now must be timezone-aware")
        payload={"task_id":task.task_id,"title":title,"content":content,"evidence":[ref.__dict__ for ref in evidence],"created_at":created.isoformat()}
        return WorkDraft(task.task_id,title,content,evidence,("Draft only; not independently verified.","No model was invoked by this reference workbench.","No external action or communication was performed."),created,_digest(payload))

@dataclass(frozen=True)
class ContributionRecord:
    owner_id:str; task_id:str
    ai_prepared:tuple[str,...]=(); human_reviewed:tuple[str,...]=(); human_corrected:tuple[str,...]=()
    human_decisions:tuple[str,...]=(); skills_practised:tuple[str,...]=()
    measured_baseline_minutes:int|None=None; ai_assisted_minutes:int|None=None
    human_review_minutes:int|None=None; rework_minutes:int|None=None
    def __post_init__(self):
        if not self.owner_id or not self.task_id: raise ValueError("owner_id and task_id required")
        for value in (self.measured_baseline_minutes,self.ai_assisted_minutes,self.human_review_minutes,self.rework_minutes):
            if value is not None and value<0: raise ValueError("time measurements cannot be negative")

def calculate_net_time_saved(*,baseline_minutes:int,ai_assisted_minutes:int,human_review_minutes:int,rework_minutes:int)->int:
    values=(baseline_minutes,ai_assisted_minutes,human_review_minutes,rework_minutes)
    if any(v<0 for v in values): raise ValueError("time measurements cannot be negative")
    return baseline_minutes-ai_assisted_minutes-human_review_minutes-rework_minutes

@dataclass(frozen=True)
class WorkforceBoundary:
    employee_owner_id:str; employer_id:str; employee_representative_id:str
    employer_system_scopes:frozenset[str]; employee_personal_scopes:frozenset[str]=field(default_factory=frozenset)
    employer_may_view_personal_knowledge:bool=False
    employer_may_view_individual_contribution:bool=False
    employee_may_export_employer_data:bool=False
    def allows_employer_access(self,scope:str)->bool: return scope in self.employer_system_scopes
    def allows_personal_knowledge_export(self)->bool: return False
    def allows_employer_view_of_personal_data(self)->bool: return False
