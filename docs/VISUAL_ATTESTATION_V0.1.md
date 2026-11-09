# Human-in-the-Loop Visual Attestation v0.1

## Product fit
Visual Attestation is a capability inside RaheB Human's existing professional representative, authority, consent and evidence architecture. It is not a second governance platform or a replacement control plane. Initial use is synthetic visual evidence and human review preparation.

## Lifecycle
1. Preserve original media or a governed immutable reference; record digest, capture time, source/device, integrity state and transformation history. Derived crops/enhancements are separate derivatives linked to the original.
2. Record model identity/version, output digest, uncertainty method/value, risk and detected conflicts.
3. Route missing evidence to HOLD; high, critical and unknown risk to mandatory human review regardless of confidence; uncertainty/conflicts to review; unavailable reviewer capacity to HOLD. Thresholds are configurable policy, not universal confidence truths.
4. Where appropriate, show original evidence and context before the model interpretation. Record presentation order. Verdicts: OBSERVED, NOT_OBSERVED, UNCERTAIN, EVIDENCE_UNUSABLE, DISAGREES_WITH_MODEL.
5. An authorised reviewer may request a defined safe state through a separate authorised control path. This module does not operate machinery, vehicles, medical devices or payment systems.
6. Bind the human attestation to evidence and model-output digests. Corrections remain pending validation and are not automatically treated as ground truth or training labels.

## Evidence dossier
Include original media digest/reference, capture timestamp/timezone, source/device identity, source integrity, transformation history, related streams, relevant time window, model output/version/digest, uncertainty method, risk and conflicts. Never silently filter or overwrite raw evidence. Privacy, consent, access control, retention and lawful purpose remain mandatory.

## Human factors
A human observer is an additional evidence source, not an infallible truth oracle. Spoofing, occlusion, fatigue, bias, poor lighting and missing context remain possible. Preserve uncertainty and disagreement. Use risk/anomaly routing, bounded queues, batching, reviewer capacity limits, rotation and escalation. Confidence is meaningful only with a documented validated calibration method and never overrides mandatory risk rules. Independent-first presentation can reduce automation bias but should be policy-controlled and presentation order recorded.

## Authority and safety
This capability grants no task authority. Existing owner/organisation permissions, consent, capability evidence and execution gateway remain authoritative. Missing, expired, conflicting or uncertain authority means HOLD. Human review cannot waive legal, safety or organisational constraints. An operational stop requires authenticated identity, role permission, defined safe state, audit record and separate operational integration.

## Evidence semantics
An attestation proves that a named reviewer recorded a verdict against specific evidence and model-output digests at a recorded time. It does not prove the verdict is correct, media authentic, reviewer qualified or physical action completed. Hashes provide tamper evidence, not truth.

## Implementation boundary
The dependency-free core defines typed evidence, model assessment, routing, attestation, intervention and correction-feedback contracts. It does not implement media storage, reviewer authentication/qualification, durable API endpoints, multi-party adjudication, operational stop integration, calibrated model uncertainty, queue orchestration or training pipelines. Synthetic data only until those controls are implemented and independently tested.


## Browser review workspace (synthetic demo)

The existing `/app` workspace now includes a Visual Attestation panel. It presents a clearly labelled synthetic vector scene, asks for an independent observation before revealing the illustrative model assessment, and then offers five verdicts including UNCERTAIN, EVIDENCE_UNUSABLE and DISAGREES_WITH_MODEL. The verdict summary is held in browser memory only. The reference identifier shown by the UI is not a cryptographic digest or signature.

The panel is a UX demonstration, not an authenticated reviewer workflow. It does not store media or verdicts, call a vision model, establish reviewer competence, create durable evidence, or trigger a stop command. The synthetic scene is not a camera feed. Production implementation must replace the local fixture with governed media custody and authenticated APIs only after consent, privacy, security and retention controls are in place.
