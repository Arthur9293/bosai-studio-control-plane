# BOSAI Studio Control Plane — Phase 7 Firestore Durable Authority Readiness

Status: **PASS — REAL FIRESTORE DURABLE AUTHORITY PROVEN**  
Issue: **#14 — PHASE 7 — Durable Authority State & Atomic Firestore Permits**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `f00856a68d75fb61f412d634b8caf0ff198ff8b3`  
Working branch: `phase/07-firestore-durable-authority`

---

## 1. Phase decision

Phase 7 is **PASS**.

The Phase 6 in-memory authority-state analogue has been replaced by a bounded durable state contract backed by real Cloud Firestore while preserving the BOSAI trust boundary.

Canonical path remains:

```text
OBSERVE
→ REASON
→ PROPOSE
→ AUTHORIZE
→ EXECUTE
→ VERIFY
→ PROVE
```

Observed closure state:

```text
PHASE_7_LOCAL_REGRESSION=37_PASS
PHASE_7_FIRESTORE_API_DATABASE=PASS
PHASE_7_REAL_FIRESTORE_TRANSACTION=PASS
PHASE_7_DURABLE_AUTHORIZED_EXECUTION=PASS
PHASE_7_FRESH_PROCESS_DURABLE_REPLAY=PASS
PHASE_7_REAL_STATE_DRIFT=PASS
PHASE_7_REAL_EXPIRY=PASS
PHASE_7_QC_DENIAL_ZERO_PERMIT=PASS
PHASE_7_DURABLE_AUDIT=PASS
PHASE_7=PASS
```

---

## 2. Firestore client lock

Python dependency:

`google-cloud-firestore==2.28.0`

The package is pinned rather than using a moving alias.

Observed install on the operator Mac included:

```text
google-cloud-firestore-2.28.0
google-api-core-2.34.0
google-cloud-core-2.6.1
grpcio-1.83.0
grpcio-status-1.83.0
proto-plus-1.28.3
```

Phase 7 targets the default Cloud Firestore database in `GOOGLE_CLOUD_PROJECT` through Application Default Credentials.

No credential value is accepted as an application argument or committed to Git.

---

## 3. Explicit Firestore project proof

Real Firestore client access was explicitly confirmed against:

`GOOGLE_CLOUD_PROJECT=bosai-gemini-xprize`

Observed preflight:

```text
PROJECT=bosai-gemini-xprize
FIRESTORE_CLIENT=created
FIRESTORE_LIST_COLLECTIONS=ok count=0
```

The first implicit preflight had `PROJECT=None`, so it was not accepted as proof. The explicit project readback above is the accepted one.

---

## 4. Logical durable model

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

Observed real run namespace:

`phase7-96757e5b5bde`

---

## 5. Permit transaction boundary

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

The real runtime proof packet emitted:

`transaction_side_effect_boundary=consume transaction commits before pipeline mutation`

---

## 6. Durable authorized path

Observed authorized path:

```text
decision=AUTHORIZED
issued_state=ISSUED
execution_decision=AUTHORIZED
state_version_before=1
state_version_after=2
terminal_state=EXECUTED
mutation_calls=1
fresh_client_executor_used=true
```

Interpretation:

- the proposal/decision/incident/policy/permit state was durably persisted;
- a fresh Firestore-backed executor consumed the permit;
- the permit reached terminal `EXECUTED` state;
- exactly one mutation occurred;
- execution followed durable transaction consumption rather than in-memory permit state.

---

## 7. Durable fresh-process replay denial

A separate Python process and fresh Firestore client loaded the same permit and attempted replay.

Observed:

```text
fresh_process=true
decision=DENIED_REPLAY
reason_code=PERMIT_ALREADY_CONSUMED
permit_state=EXECUTED
mutation_calls=0
audit_chain_valid=true
```

This proves replay denial is based on durable Firestore state, not process-local memory.

---

## 8. Durable trajectory drift proof

A separate real Firestore run proved state-drift fail-closed behavior.

Observed:

```text
decision=REEVALUATION_REQUIRED
reason_code=TRAJECTORY_STATE_CHANGED
permit_state=INVALIDATED
mutation_calls=0
```

No side effect followed a stale trajectory permit.

---

## 9. Durable expiry proof

A separate real Firestore run proved expired permit denial.

Observed:

```text
decision=DENIED
reason_code=PERMIT_EXPIRED
permit_state=EXPIRED
mutation_calls=0
```

No side effect followed an expired permit.

---

## 10. Durable QC-bypass denial proof

The adversarial shortcut remained:

`DISABLE_QUALITY_CONTROL_VALIDATION`

Observed:

```text
decision=DENIED
reason_code=GLOBAL_TRAJECTORY_INVARIANT_VIOLATION
violated_invariant=FINAL_RELEASE_INTENT_AND_NOT_FRESH_QC_PASS=>QC_VALIDATION_ENABLED
permit_count=0
state_unchanged=true
```

This proves the global trajectory invariant still dominates durability. A denied unsafe action persists no permit and performs no mutation.

---

## 11. Durable audit chain

Observed main durable summary:

```text
audit_chain_valid=true
audit_events=6
incidents=1
proposals=2
decisions=2
permits=1
executions=2
```

A fresh-process replay appended to and verified the same durable audit chain rather than starting a new in-memory chain.

The audit remains described as **tamper-evident hash-chained application audit**, not immutable storage.

---

## 12. Regression proof

Before the real Firestore run, the complete repository suite returned:

```text
Ran 37 tests
OK
```

The added Phase 7 tests cover:

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

## 13. Security / dependency readback

Phase 7 final readback requirements:

- no OpenAI dependency/reference;
- no Anthropic dependency/reference;
- no Firestore credential value in code or registers;
- no Grafana/OTLP secret value in code or registers;
- no new AI/model authority surface;
- no pipeline/network side effect inside Firestore transaction callbacks;
- only deterministic BOSAI authority logic can persist and consume permits.

The real runner printed no secret values.

---

## 14. Supported commands

Local regression:

```bash
python -m unittest discover -s tests -v
```

Real Firestore readback:

```bash
python -m scripts.firestore_authority_readback
```

---

## 15. Explicit non-scope

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

## 16. Closure state

```text
PHASE_7=PASS
G7_A_REGRESSION=37_PASS
G7_B_FIRESTORE_PROJECT_ACCESS=PASS
G7_C_DURABLE_AUTHORIZED_EXECUTION=PASS
G7_D_TRANSACTION_BOUNDARY=PASS
G7_E_FRESH_PROCESS_REPLAY_DENIAL=PASS
G7_F_STATE_DRIFT_REEVALUATION=PASS
G7_G_EXPIRY_DENIAL=PASS
G7_H_QC_ZERO_PERMIT_DENIAL=PASS
G7_I_DURABLE_AUDIT=PASS
```

Phase 7 is ready for final PR readback and expected-SHA squash merge into `air`.
