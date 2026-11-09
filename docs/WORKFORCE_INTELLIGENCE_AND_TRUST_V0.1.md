# RaheB Human — Workforce Intelligence & Trust Foundation v0.1

## Product promise
Own an AI that works with you. Your intelligence, amplified. Your authority, preserved.

RaheB Human is a supervised professional workbench, not an employee replacement score, worker-monitoring product or automated employment decision system. It helps people prepare work, inspect evidence, resolve exceptions, develop skills and make accountable decisions. Employers gain a controlled way to introduce AI while protecting data boundaries, human accountability and service quality.

No product feature guarantees job security or prevents redundancies.

## Why each party should trust and use it
### Employee value
- A representative configured around approved professional context and explicit task scope.
- Visibility into what AI prepared, sources used, what could not be verified and what remains for the human.
- Ability to review, correct, reject, pause and revoke.
- Learning experiences explain methods and provide practice without claiming unproven skills.
- Contribution records distinguish AI preparation from human review, correction, judgment and approval.
- No employer access to personal knowledge or individual contribution records by default.

### Employer value
- Task-by-task delegation assessment before workflow automation.
- Evidence, review and exception handover rather than opaque AI output.
- Separation between employee-owned representative identity and employer-controlled systems/data.
- Workflow measures: quality, errors/rework, cycle time, unresolved exceptions and net time saved after review.
- Knowledge continuity and staff development without making AI the accountable decision-maker.
- No blanket access to a personal AI.

## Six connected engines
1. Personal Work Representative — identity, approved knowledge, AI disclosure and owner controls.
2. Work Intelligence Engine — task inventory, risk, data scope, delegation mode and reasons.
3. Human–AI Handover Engine — completed work, evidence, open questions, exceptions and next authority required.
4. Professional Growth Engine — explanations, guided practice and demonstrated skill evidence.
5. Contribution Evidence Engine — separate AI-prepared, human-reviewed, human-corrected, human-decided and measured outcome records.
6. Workplace Integration Engine — narrow connectors and employer-controlled scopes.

The Workforce Reinvention Engine coordinates workflow redesign. It must not score employee replaceability, infer performance from keystrokes or make employment decisions.

## Work Intelligence contract
Input: task, profession, approved data scopes, known procedure evidence and explicit risk flags.
Output: category, risk, delegation mode, reasons, required controls and accountable human responsibility.
- SUPERVISED_EXECUTION: bounded routine work under a declared procedure; stop on exceptions.
- PREPARE_ONLY: research, analysis or judgment-support drafts; human validates and decides.
- HUMAN_OWNED: consequential decisions and relationship work remain with an accountable human.
- HOLD: unknown, unscoped or insufficiently evidenced work; no delegation.

The v0.1 classifier is deterministic rule scaffolding, not a validated occupational risk model, legal advice or professional advice. Human confirmation is required before deployment.

## Supervised workbench
A draft requires task identity, evidence references, source versions/digests/scopes, representative version, authority version, known limitations and a creation timestamp. No source, no draft. Out-of-scope source, no draft. Unknown task, HOLD. A draft is not an execution request. The reference implementation has no external tools or side effects.

High-impact, irreversible, rights-affecting, safety-critical, financial, legal, medical, employment and public-commitment decisions remain human-owned. Any future action capability requires separate expiring single-use approval bound to exact task, output, owner, representative and authority versions; revocation must be checked at the execution boundary.

## Trust and data boundaries
| Asset | Employee | Employer | RaheB |
|---|---|---|---|
| Personal identity/knowledge | Controls | No default access | Processes for explicit service purpose |
| Employer/client records | Access only as authorized | Governs | Processes through approved scoped connector |
| Representative identity | Owns/controls | Does not acquire ownership | Operates under versioned authority |
| Individual contribution record | Controls sharing | No default individual visibility | Generates only from evidence and consent |
| Aggregate workflow metrics | Permitted aggregate | Governed aggregate | Minimizes and de-identifies where appropriate |

This is a product boundary, not a substitute for jurisdiction-specific employment, privacy, IP or data-processing agreements. Employer/client data must not be copied into a personal knowledge store or exported when employment ends unless explicitly authorized and lawful.

## Proof and measurement
Contribution records distinguish AI-prepared, human-reviewed, human-corrected, human-decided/approved and outcome-observed work.

Net time saved = baseline time − AI-assisted preparation time − human review time − rework time. Negative results remain visible. Generated volume is not productivity. Quality, error rate, rework, cycle time, unresolved exceptions and customer outcomes accompany time measures.

Hash linkage can detect some alteration relative to a stored chain; it does not prove source truth, human identity, independent attestation or legal admissibility. Production evidence needs authenticated actors, durable storage, access control, retention policy, tamper-resistant external anchoring and independent review.

## Threats addressed
- Employer surveillance: no keystroke capture, covert monitoring, employee ranking or default individual contribution access.
- Employee data exfiltration: employer/client data scopes are separate; no personal export by default.
- AI impersonation: clear AI disclosure; representative never claims to be employee.
- Credential confusion: human credentials do not imply AI capability.
- Automation bias: source references, limitations, uncertainty and human review.
- Approval replay/substitution: binding covers exact task/output/owner/representative/authority versions, expiry and nonce. Atomic durable nonce consumption remains a production requirement.
- Scope escalation: unknown or missing scopes force HOLD.
- Metrics gaming: include human review and rework; retain negative savings.
- Job-loss overclaim: no guarantee of continued employment or immunity from automation.

## v0.1 implementation status
Implemented: transparent task classification; fail-closed delegation; evidence-scoped draft workbench; exact approval-binding validation helper; contribution record and net-time calculation; employee/employer boundary primitive.

Not yet implemented: persistent workflow/task store or API integration; production identity, consent, employer tenancy or connector authorization; model runtime, file ingestion, skills assessment or learning analytics; durable atomic nonce consumption, signed evidence, independent audit anchoring; validated industry-specific risk taxonomy or legal review.

The existing synthetic demo remains the only supported end-user demonstration. Do not process real employee, employer, client or personal data with these primitives. Do not describe this as production-ready or independently certified.

## Work redistribution and capability development
AI productivity must be evaluated as a change to the whole workflow, not merely as automated task count. Human effort can move into review, correction, exception handling, coordination, prompting, training and professional judgment. These are real work and must be measured.

The `WorkloadShift` record captures baseline human time and AI-assisted preparation, review, correction, exception and coordination time. It retains negative net savings, unresolved exceptions and quality changes. A workflow is flagged for review when net savings are zero or negative, unresolved exceptions remain, or measured quality declines. It does not infer employee performance or replaceability.

### Learning while work is automated
The learning primitives support explanation, guided practice, shadow review and human performance checks. AI may explain and coach, but it cannot attest to a learner's competence. Skill evidence must identify the learner, assessor, assessment method, evidence reference, outcome and time. Outcomes are limited to DEMONSTRATED, DEVELOPING, NOT_DEMONSTRATED and INCONCLUSIVE.

This addresses a key risk: if AI takes over routine preparation, junior staff may lose the repetitions and feedback through which professional judgment develops. Workflow design should preserve safe practice, supervised responsibility and progression toward more complex work.

### Compensation and labor-market realism
RaheB can make human contributions and workflow outcomes more visible, but it cannot guarantee wage increases, bargaining power, job retention or equitable distribution of productivity gains. AI may expand competition and change the price of professional services even when occupations remain. These economic outcomes depend on employer decisions, labor markets, institutions and policy beyond the product's control.

RaheB must not claim that a personal AI protects a user's job or salary. It should provide evidence that can support transparent conversations about workload, quality, responsibility, skill development and value creation, subject to lawful access and the user's control over disclosure.

### Workforce-level reporting guardrails
- Measure the whole workflow, including hidden review and correction work.
- Separate workflow-level aggregates from individual employee records.
- Do not score replaceability, rank employees or infer layoffs from AI usage.
- Do not use AI-generated output volume as a proxy for productivity.
- Preserve negative savings, quality regressions and unresolved exceptions.
- Do not present AI-completed tasks as proof of human skill.
