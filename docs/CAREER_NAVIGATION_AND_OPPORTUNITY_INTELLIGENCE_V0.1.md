# Career Navigation & Opportunity Intelligence v0.1

## Purpose
Help an individual navigate a labour market in which job titles, tasks, skill requirements, hiring workflows and AI adoption can change at different speeds. The module makes sourced requirements and the person's own evidence easier to compare without manufacturing a candidate score.

## Components
- `LabourMarketSignal`: dated, geographically scoped signal with source, confidence and explicit OBSERVED / PROJECTED / SCENARIO label.
- `OpportunityAssessment`: employer and role source, retrieval date, task/skill/experience/credential/work-condition requirements, and owner-supplied evidence.
- `build_opportunity_summary`: identifies requirements with evidence and those not yet evidenced. It does not treat missing evidence as lack of skill.
- `HiringProcessQuestions`: captures questions about permitted AI use, assessment method, human review, data use and accommodations.
- `ApplicationRecord`: tracks progress; submission must be performed by the owner.

## Product behaviour
1. Read the work and requirements, not just the title.
2. Preserve source wording, retrieval date and provenance.
3. Map each claim to real, attributable experience or label it as not yet evidenced.
4. Use AI to research, structure and prepare; the person owns their professional story and live relationships.
5. Ask employers about AI rules in applications, assessments and interviews rather than assuming them.
6. Track outcomes to learn from the process, not to produce an opaque employability score.

## Boundaries
No ATS bypass, keyword stuffing, fabricated experience, synthetic credentials, automatic mass applications, interview impersonation, hiring prediction, employability ranking or job-loss prediction. Do not infer labour-market trends from a single anecdote. Keep observed evidence separate from projections and scenarios. The person reviews all application content and submits applications.

## Limitations
Deterministic in-memory scaffolding. No live job-board ingestion, ATS integration, résumé parser, model calls, application submission, employer data exchange or persistent storage. Market data must be supplied with reliable source metadata. Not production-ready.
