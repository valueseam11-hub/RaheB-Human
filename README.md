# RaheB Human

**Bring your professional AI to work. You remain the human in control.**

RaheB Human is infrastructure through which people build, own, develop and bring their own professional AI representatives into work, while organisations discover, assess and deploy human professionals together with those representatives under explicit workplace controls.

An individual builds a representative around their profession, approved knowledge, real workflows and tested capabilities. They retain ownership and control, choose what evidence to share, and can bring the representative to a new workplace. An organisation can hire the human professional and authorise a bounded deployment of that representative into its own approved workflows. The employer does not acquire ownership of the person's personal AI.

**The platform serves two sides:**
- **Professional AI Builder:** identity, profession and task profile, representative creation, approved knowledge, capability testing, learning, authority controls and portable evidence.
- **Organisation Workforce Deployment:** role/workflow definition, evidence-based professional discovery, representative assessment, employer-side data/tool permissions, supervised deployment, human approvals and workflow outcome evidence.

**The core distinction:** human capability, AI representative capability and joint human–AI work evidence are separate. A representative's test result does not prove the owner's competence. AI-prepared work is never misrepresented as human-performed work.

**The workplace boundary:** the owner authorises their representative; the organisation authorises its systems, data, tools and workflows. Where employer/client resources are involved, both applicable permissions must be current. Missing, expired, revoked or uncertain authority means HOLD.

**The product is not** a generic chatbot builder, résumé tool, job board, employee surveillance suite, worker ranking or replaceability score, or automated employment-decision system. Career development and talent discovery support the human-owned professional representative; they are not the product's centre.

## Architecture Foundation v1.0

The canonical product architecture is defined in `docs/ARCHITECTURE_FOUNDATION.md`. It sets out the five axioms, individual and organisation journeys, professional task intelligence, separate human/AI capability registries, Human Capability Continuity, two-key workplace authority, evidence and provenance, contribution attribution, portability and explicit exclusions.

## Engineering status

The repository contains testable architecture references and synthetic prototypes, not a production-ready AI workforce platform. Some foundations are in-memory or browser-local and are not integrated with production identity, persistent multi-tenant storage, live model execution, workplace connectors or durable operational controls. Use synthetic data only unless a specific component is explicitly verified for production use.

Every capability must be described honestly as specified, prototyped, tested, integrated or production-verified. Architecture documentation is not proof of implementation.

## Quick start

Requires Python 3.11+; no third-party runtime dependencies.

    python -m unittest discover -s tests -v

