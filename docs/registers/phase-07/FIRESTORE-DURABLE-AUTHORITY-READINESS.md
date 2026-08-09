# BOSAI Studio Control Plane — Phase 7 Firestore Durable Authority Readiness

Status: **PREPARED — LOCAL REGRESSION AND REAL FIRESTORE PROOF PENDING**  
Issue: **#14 — PHASE 7 — Durable Authority State & Atomic Firestore Permits**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `f00856a68d75fb61f412d634b8caf0ff198ff8b3`  
Working branch: `phase/07-firestore-durable-authority`

---

## 1. Phase objective

Phase 7 replaces the Phase 6 in-memory authority-state analogue with a bounded durable state contract backed by Cloud Firestore.

The control-plane thesis remains unchanged:

```text
OBSERVE
→ REASON
→ PROPOSE
→ AUTHORIZE
→ EXECUTE
→ VERIFY
→ PROVE
```

Phase 7 changes only the durability and atomicity of the BOSAI authority layer. Gemini still has no permit, execution, policy-write, or pipeline-mutation capability.

---

## 2. Firestore client lock

Python dependency:

`google-cloud-firestore==2.28.0`

The package is pinned rather than using a moving alias.

Phase 7 targets the default Cloud Firestore database in `GOOGLE_CLOUD_PROJECT` through Application Default Credentials.

No credential value is accepted as an application argument or committed to Git.

---

## 3. Logical durable model

Each real validation run is isolated below:

`bosai_authority_runs/{phase7_run_id}`

with logical subcollections:

```text
incidents/{incident_id}
policies/{policy_id}/versions/{version}
proposals/{proposal_id}
decisions/{proposal_id}
permits/{permit_id}
executions/{execution_id}
audit_events/{event_id}
meta/audit
```

The run namespace prevents validation evidence from colliding with earlier runs while preserving the Architecture V1 logical model.

---

## 4. Permit transaction boundary

The critical Phase 7 ordering is:

```text
Firestore transaction:
  read permit
  read durable incident trajectory
  validate status / expiry / proposal binding / state version
  write ISSUED → CONSUMED_PENDING
COMMIT

only after commit:
  execute pipeline side effect
  persist updated incident state
  write permit terminal state
  persist execution receipt
```

There is deliberately no pipeline/network invocation in the transaction callback.

A transaction retry can therefore repeat only Firestore reads/writes, not the external mutation.

---

## 5. Durable permit states

Phase 7 durable permit lifecycle:

```text
ISSUED
→ CONSUMED_PENDING
→ EXECUTED
```

Failure terminals:

```text
CONSUMED_PENDING → EXECUTION_FAILED
ISSUED → EXPIRED
ISSUED → INVALIDATED
```

Replay against any non-`ISSUED` state fails closed as `DENIED_REPLAY`.

A crash after `CONSUMED_PENDING` does not automatically repeat the side effect. A new proposal and authorization are required.

---

## 6. Durable trajectory binding

Each permit contains:

```text
proposal_id
incident_id
action
target
policy_version
bound_state_version
expires_at
status
```

The Firestore consumption transaction reads the current durable incident document and compares its `state_version` with `bound_state_version`.

A mismatch returns:

```text
decision=REEVALUATION_REQUIRED
reason_code=TRAJECTORY_STATE_CHANGED
permit_state=INVALIDATED
```

No side effect follows.

---

## 7. Durable audit chain

Phase 7 introduces a Firestore-backed audit chain that remains tamper-evident by application design.

Audit append is itself transactional:

1. read durable audit sequence/head;
2. compute payload digest and next event hash;
3. write the next `audit_events/{event_id}` document;
4. update `meta/audit` with the new sequence/head.

A fresh executor/client therefore continues the existing chain rather than starting a new in-memory sequence.

The storage is **not** described as immutable.

---

## 8. Local semantic tests prepared

The Phase 7 test suite adds proofs for:

- authorized permit persistence;
- execution through a fresh executor instance;
- durable replay denial;
- simulated transaction retries with exactly one external mutation;
- durable trajectory drift → reevaluation;
- durable permit expiry;
- `CONSUMED_PENDING` crash analogue with no automatic side-effect retry;
- QC bypass denial with zero permit and zero mutation;
- durable audit-chain continuation across executor instances;
- missing permit fail-closed behavior.

Existing Phase 0–6 tests remain part of the mandatory regression.

---

## 9. Real Cloud Firestore runner

`scripts/firestore_authority_readback.py` is the real Phase 7 evidence runner.

It is designed to prove against the configured Google Cloud project:

1. authorization persists proposal, decision, incident, policy, and an `ISSUED` permit;
2. a fresh Firestore client/executor consumes and executes that permit;
3. the permit reaches durable `EXECUTED`;
4. a true fresh Python subprocess reloads Firestore and receives `DENIED_REPLAY` with zero mutation calls;
5. QC bypass persists no permit and performs no mutation;
6. a separate real Firestore run proves trajectory drift returns `REEVALUATION_REQUIRED`;
7. a separate real Firestore run proves expiry returns `PERMIT_EXPIRED` and persists `EXPIRED`;
8. the main durable audit chain still verifies after the fresh subprocess appended its replay-denial event.

The runner prints identifiers and states, not ADC credentials or secret values.

---

## 10. Explicit non-scope

Phase 7 does not yet add:

- Cloud Run deployment;
- service-to-service IAM enforcement;
- IAM negative proof;
- public UI;
- Secret Manager runtime injection;
- Grafana write tools;
- any new AI/model authority.

These remain later gates.

---

## 11. Current gate state

```text
PHASE_7_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_7_FIRESTORE_CLIENT_PIN=2.28.0
PHASE_7_DURABLE_STORE=PREPARED
PHASE_7_PERSISTENT_AUTHORITY_EXECUTOR=PREPARED
PHASE_7_TRANSACTION_RETRY_SAFETY_TEST=PREPARED
PHASE_7_FRESH_PROCESS_REPLAY_PROBE=PREPARED
PHASE_7_REAL_FIRESTORE_RUNNER=PREPARED
PHASE_7_LOCAL_REGRESSION=PENDING
PHASE_7_FIRESTORE_API_DATABASE=PENDING
PHASE_7_REAL_FIRESTORE_TRANSACTION=PENDING
PHASE_7_FRESH_PROCESS_DURABLE_REPLAY=PENDING
PHASE_7_REAL_STATE_DRIFT=PENDING
PHASE_7_REAL_EXPIRY=PENDING
PHASE_7=PARTIAL
```

No Firestore runtime PASS may be claimed from code inspection alone.

---

## 12. Exit criteria

Phase 7 may move to PASS only when:

1. full repository regression is green;
2. Firestore API/database availability is externally read back;
3. real Firestore writes and transactional permit consumption succeed;
4. authorized execution occurs only after `CONSUMED_PENDING` is committed;
5. durable terminal permit state is `EXECUTED`;
6. fresh-process replay is denied from Firestore state with zero mutation;
7. real Firestore state drift requires reevaluation with zero mutation;
8. real Firestore expiry denies execution and persists `EXPIRED`;
9. QC bypass creates zero permit and zero mutation;
10. durable audit chain verifies after cross-process activity;
11. final diff/readback finds no authority bypass, no secret value, and no disallowed AI dependency.

The branch remains unmerged until all gates are proven.
