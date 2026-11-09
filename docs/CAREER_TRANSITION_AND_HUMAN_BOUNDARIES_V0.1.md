# Career Transition & Human Interaction Boundaries v0.1

## Purpose
Help a person plan for changing work by mapping an owner-defined career goal to dated skill requirements, attributable evidence and practical development actions. Preserve the person's right to decide which professional interactions remain human-owned.

This is a planning and evidence organisation layer. It is not a labour-market forecast, employability score, job-loss predictor, hiring system or automated career adviser.

## Career transition records
- **SkillRequirement:** a skill or capability linked to an owner-defined goal and a dated source reference.
- **SkillEvidenceRecord:** demonstrated/developing/not-yet-evidenced/disputed state, attributable person, context, timestamp and evidence reference.
- **DevelopmentAction:** learn, practise, shadow, seek mentorship, build portfolio evidence or explore a role.
- **CareerTransitionPlan:** current role, owner-defined goal, requirements, evidence and actions.

A missing evidence record is labelled NOT_YET_EVIDENCED, not "unskilled". Disputed evidence is preserved. The system does not infer employability, job availability, salary, promotion or job-loss probability. Skill-demand signals must retain their source and publication date; stale or unverified market claims must not be presented as current facts.

## Human interaction boundaries
The owner can mark communication and relationship work as:
- **HUMAN_OWNED:** the human conducts and owns the interaction.
- **AI_PREPARE_ONLY:** AI may prepare background or draft material but does not communicate.
- **AI_ASSISTED_WITH_APPROVAL:** a specific purpose-bound approval and expiry are required.

The owner's preference is a boundary, not a frictionless default that can be overridden by a model or employer. Existing task risk assessment and authority controls remain in force.

## Product safeguards
- No employee replaceability scores, layoff predictions, worker ranking or automated hiring/employment decisions.
- No assumption that an occupation is "dead" or a role is safe based on anecdotes.
- No treating AI literacy alone as proof of professional competence.
- No AI-generated résumé or interview claim without attributable supporting evidence and owner review.
- No assumption that AI must handle communication; preserve human-owned relationships where selected.
- Keep market claims linked to dated sources and distinguish reported claims from verified evidence.
- Preserve learning and practice opportunities when automating junior or preparatory work.

## Relationship to RaheB Human
Connects Work Identity & Recognition, Professional Identity & Expertise, Work Intelligence, WorkloadShift and the Personal Work Representative. WorkloadShift continues to measure review, correction, exceptions, coordination and training. Work identity evidence can inform a transition plan only with owner consent; it is not silently repurposed.

## v0.1 implementation boundary
Deterministic in-memory Python contracts and summary helpers only. No labour-market data ingestion, role matching, persistent storage, API, résumé generation, employer integration or AI model calls. Synthetic fixtures only; not production-ready.
