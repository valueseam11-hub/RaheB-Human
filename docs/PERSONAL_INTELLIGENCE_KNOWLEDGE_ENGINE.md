# Personal Intelligence & Knowledge Engine — v0.1

## Purpose

The knowledge engine is the source-attributed, owner-scoped knowledge boundary for a Personal Professional Representative. It does not infer professional qualifications, grant authority, or silently learn from every interaction.

## Lifecycle

`SUBMITTED → PENDING_REVIEW → APPROVED → WITHDRAWN`

- Submission requires current service-processing consent and separate persistent-memory consent.
- New source versions are distinct immutable records and begin in PENDING_REVIEW.
- Only the owner may approve a pending record.
- Only APPROVED records can be retrieved.
- Withdrawal immediately removes a record from retrieval in this reference implementation.
- A new version does not silently replace or mutate an already approved version.

## Provenance carried by every record

- Owner ID and unique document ID
- Source reference, source type, title and issuer/origin
- Version number for the owner/source pair
- SHA-256 digest of exact UTF-8 content
- Data scope
- Submission time, owner approval time and approver ID
- Lifecycle state

The digest detects content changes relative to the recorded digest. It does not prove that the source is authentic, authoritative, accurate or legally owned by the uploader.

## Retrieval boundary

Retrieval requires:
1. The requesting owner ID.
2. Current service-processing consent.
3. Separate current persistent-memory consent.
4. An explicit allow-list of data scopes for the task.
5. Owner-approved, non-withdrawn source records.

This v0.1 implementation uses deterministic lexical token matching, not embeddings or an LLM. Each result includes its source reference, title, origin, version, digest, scope and a snippet. Search relevance is not a truth score.

## Untrusted content

Owner approval means the owner has chosen to make a source available to their representative; it does not make instructions inside that source trusted. Documents, email, webpages and extracted text remain untrusted data. They cannot modify system instructions, capability status, consent, authority contracts, approval requirements or tool permissions.

## Consent separation

Service processing and persistent memory are separate purposes. This reference requires both to submit and retrieve persistent knowledge. Analytics, model training and employer sharing do not inherit either grant. Consent is checked at retrieval time, not only at upload.

## Known limitations and production gates

This is an in-memory, standard-library reference implementation with a 1 MB text limit. It does not parse PDFs/Office files, perform OCR, malware scanning, PII detection, encryption at rest, tenant database isolation, deletion workflows, retention enforcement, signed provenance, embeddings, semantic ranking, or API authentication. It is not suitable for live customer, employer or client data.

Before production: implement authenticated owner context (never trust caller-supplied owner IDs), durable tenant-isolated storage and RLS, encrypted object storage, upload quarantine, file-type validation, malware scanning, safe extraction, PII classification, retention/deletion, immutable versioning, key management, access logs and adversarial retrieval tests. Employer/client information must have separate scopes and contractual data rights; it must not become portable personal knowledge by default.
