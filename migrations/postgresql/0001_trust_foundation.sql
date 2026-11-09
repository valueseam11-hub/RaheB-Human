BEGIN;
CREATE TABLE IF NOT EXISTS raheb_owner_accounts (
 owner_id UUID PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','SUSPENDED','CLOSED'))
);
CREATE TABLE IF NOT EXISTS raheb_representatives (
 representative_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 display_name TEXT NOT NULL CHECK(length(trim(display_name)) BETWEEN 2 AND 120),
 professional_role TEXT NOT NULL CHECK(length(trim(professional_role)) BETWEEN 2 AND 160),
 version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),
 state TEXT NOT NULL CHECK(state IN ('DRAFT','CONFIGURED','ACTIVE','PAUSED','REVOKED')),
 ai_disclosure_enabled BOOLEAN NOT NULL DEFAULT TRUE CHECK(ai_disclosure_enabled),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(owner_id,representative_id)
);
CREATE TABLE IF NOT EXISTS raheb_authority_contracts (
 contract_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 representative_id UUID NOT NULL, version INTEGER NOT NULL CHECK(version>0),
 status TEXT NOT NULL CHECK(status IN ('DRAFT','ACTIVE','SUSPENDED','REVOKED','EXPIRED')),
 contract_json JSONB NOT NULL, contract_digest BYTEA NOT NULL CHECK(octet_length(contract_digest)=32),
 issued_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL CHECK(expires_at>issued_at),
 revoked_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(owner_id,representative_id) REFERENCES raheb_representatives(owner_id,representative_id),
 UNIQUE(owner_id,representative_id,version), UNIQUE(owner_id,contract_id)
);
CREATE TABLE IF NOT EXISTS raheb_consent_records (
 consent_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 purpose TEXT NOT NULL CHECK(purpose IN ('REQUIRED_SERVICE','PERSISTENT_MEMORY','ANALYTICS','MODEL_TRAINING','EMPLOYER_SHARING')),
 granted BOOLEAN NOT NULL, affirmative_action BOOLEAN NOT NULL,
 document_version TEXT NOT NULL, document_hash BYTEA NOT NULL CHECK(octet_length(document_hash)=32),
 recorded_at TIMESTAMPTZ NOT NULL, withdrawn_at TIMESTAMPTZ, expires_at TIMESTAMPTZ,
 evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
 CHECK(withdrawn_at IS NULL OR withdrawn_at>=recorded_at),
 CHECK(expires_at IS NULL OR expires_at>recorded_at)
);
CREATE TABLE IF NOT EXISTS raheb_capability_assessments (
 assessment_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 representative_id UUID NOT NULL, capability TEXT NOT NULL, scope TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('NOT_ASSESSED','TESTED','FAILED','EXPIRED')),
 test_suite_version TEXT NOT NULL, evidence_digest BYTEA NOT NULL CHECK(octet_length(evidence_digest)=32),
 assessed_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ,
 FOREIGN KEY(owner_id,representative_id) REFERENCES raheb_representatives(owner_id,representative_id),
 UNIQUE(owner_id,assessment_id)
);
CREATE TABLE IF NOT EXISTS raheb_knowledge_documents (
 document_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 representative_id UUID NOT NULL, source_ref TEXT NOT NULL, source_type TEXT NOT NULL,
 source_title TEXT NOT NULL, source_origin TEXT NOT NULL, source_version INTEGER NOT NULL CHECK(source_version>0),
 object_key TEXT NOT NULL, content_digest BYTEA NOT NULL CHECK(octet_length(content_digest)=32),
 data_scope TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PENDING_REVIEW','APPROVED','WITHDRAWN','QUARANTINED','DELETED')),
 submitted_at TIMESTAMPTZ NOT NULL, approved_at TIMESTAMPTZ, approved_by UUID,
 FOREIGN KEY(owner_id,representative_id) REFERENCES raheb_representatives(owner_id,representative_id),
 UNIQUE(owner_id,source_ref,source_version)
);
CREATE TABLE IF NOT EXISTS raheb_tasks (
 task_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 representative_id UUID NOT NULL, request_digest BYTEA NOT NULL CHECK(octet_length(request_digest)=32),
 task_type TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('RECEIVED','HOLD','ADMITTED','RUNNING','AWAITING_HUMAN_REVIEW','APPROVED','REJECTED','CANCELLED','FAILED')),
 authority_contract_id UUID, authority_contract_version INTEGER, capability_assessment_id UUID,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(owner_id,representative_id) REFERENCES raheb_representatives(owner_id,representative_id),
 UNIQUE(owner_id,task_id),
 FOREIGN KEY(owner_id,authority_contract_id) REFERENCES raheb_authority_contracts(owner_id,contract_id),
 FOREIGN KEY(owner_id,capability_assessment_id) REFERENCES raheb_capability_assessments(owner_id,assessment_id)
);
CREATE TABLE IF NOT EXISTS raheb_human_approvals (
 approval_id UUID PRIMARY KEY, owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id),
 task_id UUID NOT NULL, contract_id UUID NOT NULL,
 contract_version INTEGER NOT NULL, request_digest BYTEA NOT NULL CHECK(octet_length(request_digest)=32),
 decision TEXT NOT NULL CHECK(decision IN ('APPROVED','REJECTED')), approved_by UUID NOT NULL,
 approved_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL CHECK(expires_at>approved_at),
 consumed_at TIMESTAMPTZ, FOREIGN KEY(owner_id,task_id) REFERENCES raheb_tasks(owner_id,task_id),
 FOREIGN KEY(owner_id,contract_id) REFERENCES raheb_authority_contracts(owner_id,contract_id)
);
CREATE TABLE IF NOT EXISTS raheb_evidence_events (
 sequence BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, event_id UUID NOT NULL UNIQUE,
 owner_id UUID NOT NULL REFERENCES raheb_owner_accounts(owner_id), subject_type TEXT NOT NULL,
 subject_id TEXT NOT NULL, event_type TEXT NOT NULL, occurred_at TIMESTAMPTZ NOT NULL,
 payload JSONB NOT NULL, previous_digest BYTEA NOT NULL CHECK(octet_length(previous_digest)=32),
 record_digest BYTEA NOT NULL UNIQUE CHECK(octet_length(record_digest)=32),
 signer_key_id TEXT, signature BYTEA, UNIQUE(owner_id,sequence)
);
CREATE INDEX IF NOT EXISTS raheb_representatives_owner_idx ON raheb_representatives(owner_id,created_at DESC);
CREATE INDEX IF NOT EXISTS raheb_contract_owner_rep_idx ON raheb_authority_contracts(owner_id,representative_id,status);
CREATE INDEX IF NOT EXISTS raheb_consent_owner_purpose_idx ON raheb_consent_records(owner_id,purpose,recorded_at DESC);
CREATE INDEX IF NOT EXISTS raheb_knowledge_owner_scope_idx ON raheb_knowledge_documents(owner_id,representative_id,data_scope,state);
CREATE INDEX IF NOT EXISTS raheb_tasks_owner_state_idx ON raheb_tasks(owner_id,state,created_at DESC);
CREATE INDEX IF NOT EXISTS raheb_evidence_owner_seq_idx ON raheb_evidence_events(owner_id,sequence);
DO $$
DECLARE table_name TEXT;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['raheb_owner_accounts','raheb_representatives','raheb_authority_contracts','raheb_consent_records','raheb_capability_assessments','raheb_knowledge_documents','raheb_tasks','raheb_human_approvals','raheb_evidence_events'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',table_name);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',table_name);
  EXECUTE format('CREATE POLICY tenant_isolation ON %I USING (owner_id=NULLIF(current_setting(''raheb.owner_id'',true),'''')::uuid) WITH CHECK (owner_id=NULLIF(current_setting(''raheb.owner_id'',true),'''')::uuid)',table_name);
 END LOOP;
END $$;
CREATE OR REPLACE FUNCTION raheb_reject_evidence_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'raheb evidence events are append-only'; END;
$$;
DROP TRIGGER IF EXISTS raheb_evidence_no_update_delete ON raheb_evidence_events;
CREATE TRIGGER raheb_evidence_no_update_delete BEFORE UPDATE OR DELETE ON raheb_evidence_events
FOR EACH ROW EXECUTE FUNCTION raheb_reject_evidence_mutation();
COMMIT;
