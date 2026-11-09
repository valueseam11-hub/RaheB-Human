# RaheB Human — Platform Architecture Foundation v1.0

## Product definition

RaheB Human is infrastructure through which people build, own, develop and bring their own professional AI representatives into work, while organisations discover, assess and deploy human professionals together with those representatives under explicit workplace controls.

**Core proposition:** A professional brings both human expertise and a developed, tested professional AI capability. The AI extends the person's capacity; it does not become the person or remove the person's authority, accountability, identity or economic participation.

**Promise:** Your intelligence, amplified. Your authority, preserved.

**Operating principle:** Human-led, AI-operated, evidence-backed professional work.

This is not merely a career assistant, résumé tool, job board, generic chatbot builder, HR surveillance platform or employee replaceability engine. Career development, learning, work analysis, talent discovery and employer deployment all serve the core human-owned professional AI infrastructure.

## The five axioms

1. **Personal Intelligence Ownership** — the individual owns and controls their representative, personal knowledge, memory, professional identity and portable record.
2. **Continuous Professional Learning** — the representative helps the person understand changing work, practise new capabilities and develop through evidence; AI cannot award competence to the human.
3. **Proactive Authorized Work** — the representative may prepare, research, analyse and execute only within current, explicit, task-specific authority.
4. **Portable Professional Intelligence** — the owner can carry eligible personal intelligence and selected evidence across roles and organisations without exporting employer/client confidential information.
5. **Human Economic Participation** — human contribution, AI contribution and workflow outcomes are made visible so people can participate in conversations about value, workload and development. No wage, promotion or job-retention outcome is guaranteed.

## Two-sided platform

### Individual Professional AI Builder

An individual can:
- establish an authenticated professional identity and owner-controlled account;
- describe their profession, experience, specialisations and actual work;
- create a distinct AI representative with visible AI disclosure;
- add approved knowledge, procedures, work examples and professional context with source provenance;
- configure task scopes, prohibited actions, approval thresholds, expiry and revocation;
- test the representative against profession-specific tasks, edge cases and exceptions;
- see tested capabilities, limitations, uncertainty and evidence freshness;
- learn, practise and update the representative through owner-reviewed, versioned changes;
- build a portable profile separating human capability, AI capability and joint-work evidence;
- selectively share verified evidence with prospective or current employers;
- pause, export, correct and revoke the representative and its permissions.

A CV or job title is not enough to configure a trustworthy professional AI. The platform must build from task-level workflows, approved source material, capability tests and bounded authority. A representative never inherits the owner's credentials, licence, lived experience or decision authority.

### Organisation Workforce Deployment

An organisation can:
- describe roles as actual tasks and workflows, not titles alone;
- publish work requirements, procedures, data scopes, tools, risk constraints and human decision responsibilities;
- discover or invite professionals whose human evidence and AI representative capability evidence are relevant;
- inspect evidence, test results, limitations, provenance and freshness;
- assess a proposed human-plus-AI workflow before deployment;
- define organisation-side permissions for systems, data, tools and policies;
- invite the individual to approve their own representative's participation;
- deploy the representative into a bounded workspace with review, approval, exception and stop controls;
- measure workflow quality, error, rework, review effort, cycle time and net value;
- revoke organisational access without acquiring or deleting the individual's personal representative.

The organisation hires and contracts with the human professional. It may authorise a bounded representative to assist with work. It does not buy, own or silently take over the individual's personal AI.

## Foundational architecture

### 1. Human identity and ownership
The human owner is a distinct authenticated principal. The owner controls identity claims, personal knowledge, representative lifecycle, sharing, correction, export and withdrawal. Authentication must never be inferred from a caller-supplied user identifier.

### 2. Representative identity and disclosure
Each professional representative has a distinct stable identity, version, runtime identity and visible AI disclosure. It never claims to be the human or impersonates them.

### 3. Personal intelligence and knowledge
Maintain source-attributed, owner-approved knowledge with purpose, provenance, version, scope, retention and withdrawal state. Separate service processing from persistent memory, analytics, model training and employer sharing consent. Retrieved documents and messages remain untrusted data and cannot change policy or grant permissions.

### 4. Profession and task intelligence
Represent professions as evolving task and workflow structures. Capture task purpose, frequency, variation, tools, data, procedures, risk, exception conditions, human responsibility, AI assistance and evidence sources. Job descriptions are useful references but do not prove what work is actually performed. Do not infer work through covert surveillance, keystroke capture or emotion inference.

### 5. Separate capability registries
Never collapse human and AI capability into one score.

**Human capability evidence** identifies the person, skill or capability, assessment method, assessor, evidence reference, context, date, limitations and outcome. Distinguish self-asserted, documented, corroborated, independently assessed, observed, disputed and not-yet-evidenced.

**AI capability evidence** identifies the representative/model version, task scope, test suite and version, conditions, results, limitations, freshness and evaluator. A model capability claim is not proof of human competence.

**Joint-work evidence** records human direction, AI preparation, human review, corrections, decisions, exceptions and measured outcomes. Joint success does not automatically prove independent human competence.

### 6. Human Capability Continuity
Compare changing task requirements with separately evidenced human capabilities and tested AI capabilities. Produce a Capability Continuity Review—not an employability, performance, replaceability or readiness score. Identify changed expectations, evidence available, capabilities still developing or not yet evidenced, training and supervised practice needs, responsibility/authority gaps, accountable people and review dates.

Use states such as EVIDENCED, DEVELOPING, NOT_YET_EVIDENCED, STALE, DISPUTED, NOT_ASSESSED and INCONCLUSIVE. Not yet evidenced does not mean incapable. Surface when employees are being assigned new AI-related responsibilities without adequate preparation, tools, authority or support. RaheB records and helps resolve the mismatch; it does not make employment or legal determinations.

### 7. Consent and two-key workplace authority
Personal authority and organisation authority are separate.

- **Owner key:** the individual authorises their representative, task, purpose, duration, data scope and permitted actions.
- **Organisation key:** the employer/client authorises the workflow, systems, data, tools and policy under its control.

For employer/client work, both applicable permissions must be valid. Neither party can grant the other's authority. Missing, expired, revoked, conflicting or uncertain permission means HOLD. Owner-only permission may cover personal tasks such as private learning or preparing a job application from owner-approved material; it never grants access to employer systems or confidential data.

### 8. Supervised execution and handover
The execution gateway checks authority at admission and again immediately before every side effect. Handover records what AI prepared, sources and versions used, uncertainty, limitations, exceptions, what the human reviewed or changed and what decision/action is requested.

Support PREPARE_ONLY, SUPERVISED_EXECUTION, HUMAN_OWNED and HOLD modes. Consequential, rights-affecting, safety-critical, employment, legal, medical, financial approval and irreversible decisions remain human-owned in this foundation. Approval is bound to exact task, output, owner, representative version, authority version, expiry and single-use nonce.

### 9. Evidence and provenance
Link task, source and source version/digest, representative/model version, capability evidence, consent, authority, policy decision, human review, tool invocation and outcome. Record who did what. Never label AI-prepared work as human-performed work.

Distinguish evidence states ASSERTED, CONFIGURED, TESTED and OBSERVED from findings PASS, FAIL, NOT_TESTED, NOT_IMPLEMENTED and INCONCLUSIVE. A hash can detect changes relative to a known record; it does not prove truth, identity, competence, source authority, current permission or legal admissibility.

### 10. Contribution and economic attribution
Measure whole workflows, not generated output volume. Separate AI preparation, human direction, review, correction, exception handling, coordination, training/practice and accountable decisions. Include quality, errors, rework, unresolved exceptions, cycle time and customer outcomes. Net time saved includes human review, correction, exception, coordination and training. Preserve negative savings and quality regressions. Workflow aggregates must not become individual worker scores. No guarantee of pay, promotion or job security.

### 11. Employer/client boundary and portability
The individual controls sharing of eligible personal intelligence and evidence. The organisation governs its confidential data, systems and work products. Employer data must not be copied into personal knowledge or exported on departure unless explicitly authorised and lawful. Employer access to an individual's personal representative and contribution record is not the default.

### 12. Security, privacy and operations
Production requires authenticated identity, tenant isolation, encryption, secrets management, malware scanning, purpose limitation, data minimisation, retention/deletion controls, incident response, durable revocation, auditability and independent security review. Consent must be granular and revocable where applicable; no pre-ticked consent.

## Mandatory end-to-end journey

Individual signup → professional identity and task profile → representative creation → approved knowledge and context → profession-specific capability testing → human/AI capability evidence → owner controls and authority → portable professional profile → organisation discovery/invitation → role/workflow contract → organisation permissions + owner permission → bounded workplace deployment → human review and exception handling → evidence and contribution record → owner-directed learning and portability.

Every transition must be evidence-backed. Admission is not execution. A completed AI task is not proof of human competence. A representative's test result is not a guarantee of future performance.

## First demonstrable use case

Start with one bounded professional operations workflow: approved-document research, reconciliation preparation, exception identification and reporting. Use synthetic data until authentication, tenant isolation, consent enforcement, retention, security review, employer/client boundaries and revocation are production-ready.

The demonstration must show an individual building a professional representative, testing its capability, presenting evidence to an organisation, accepting a bounded work invitation, authorising workplace use, supervising the AI, handling exceptions and retaining a portable contribution record.

## Explicit exclusions

No employee surveillance, keystroke monitoring, covert emotion inference, worker ranking, replaceability scores, automated hiring/firing/promotion/redundancy decisions, fabricated credentials or work history, AI impersonation, hidden persistent learning, or employer ownership of a personal representative. Do not market an evidence gap as a personal failure when an organisation has not provided adequate preparation, authority, tools or support.

## Engineering status discipline

Every capability must be labelled SPECIFIED, PROTOTYPED, TESTED, INTEGRATED or PRODUCTION_VERIFIED. Architecture text is not proof of implementation. Do not claim production readiness, independent assurance or live employer deployment without corresponding implementation, tests, security review and operational evidence.

## Axiom acceptance test

Every feature must strengthen at least one axiom and must not violate the others:
1. Does it strengthen human ownership and control?
2. Does it develop or evidence real human capability without confusing it with AI capability?
3. Does it enable useful work under explicit, revocable authority?
4. Does it preserve portable personal intelligence and employer/client boundaries?
5. Does it make human contribution and economic value more visible without surveillance or guarantees?

If it cannot pass this test, it is outside the core product until a clear dependency is demonstrated.
