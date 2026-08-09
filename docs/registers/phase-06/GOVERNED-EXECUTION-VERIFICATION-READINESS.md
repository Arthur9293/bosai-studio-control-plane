# BOSAI Studio Control Plane — Phase 6 Governed Execution & Verification Readiness

Status: **PREPARED — LOCAL REGRESSION AND REAL RUNTIME PROOF PENDING**  
Issue: **#12 — PHASE 6 — Governed Execution & Verification Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `ed6737ed7520337dad88503255344a1da7f32b68`  
Working branch: `phase/06-governed-execution-verification`

---

## 1. Phase objective

Phase 6 closes the first complete local governed-control loop:

```text
OBSERVE
→ REASON
→ PROPOSE
→ AUTHORIZE
→ EXECUTE
→ VERIFY
→ PROVE
```

Phase 5 already proved the first four upstream runtime facts required here:

- real Vertex AI / Gemini invocation;
- Google ADK;
- official read-only Grafana MCP;
- real Grafana Cloud Loki evidence;
- schema-valid BOSAI proposal with `authority_decision=NOT_EVALUATED`.

Phase 6 does not expand Gemini authority. It connects the resulting `Proposal` to the existing deterministic BOSAI authority boundary and proves side effects only through a single-use permit.

---

## 2. New deterministic components

### `verification.py`

Adds an action-specific deterministic verifier.

A model-written expected postcondition is treated as an expectation, not proof. The verifier requires:

- an authorized execution receipt;
- a permit id;
- authoritative pipeline state progression;
- action-specific state checks;
- required read-only Grafana evidence tokens.

Verification fails closed when required telemetry evidence is missing.

### `governed_loop.py`

Adds a coordinator around `AuthorityExecutor`.

It:

- records observation and proposal digests in the audit trail;
- submits proposals to deterministic authority;
- blocks execution unless an `AUTHORIZED` decision contains a permit;
- delegates the side effect only to `AuthorityExecutor.execute`;
- records deterministic postcondition verification results;
- exposes a compact tamper-evident audit proof summary.

It does **not** call the pipeline mutation primitive directly.

---

## 3. Strengthened authority audit

Phase 6 aligns the local audit vocabulary more closely with Architecture V1.

Expected events now include:

```text
OBSERVATION_CAPTURED
PROPOSAL_CREATED
AUTHORITY_GRANTED | AUTHORITY_DENIED
PERMIT_CONSUMED
EXECUTION_STARTED
EXECUTION_SUCCEEDED | EXECUTION_FAILED | EXECUTION_DENIED
POSTCONDITION_VERIFIED | POSTCONDITION_FAILED
```

The existing SHA-256 hash chain remains the tamper-evident mechanism.

The permit lifecycle remains single-use and replay-safe.

---

## 4. Authorized path

The real Phase 5 proposal remains the competition-critical first action:

```text
action=RESTART_TRANSCODE_WORKER
target=transcode-a
```

Required Phase 6 path:

```text
real Gemini proposal
→ BOSAI evaluate
→ AUTHORIZED
→ one-time permit
→ AuthorityExecutor.execute
→ ObservedMediaPipelineSim mutation
→ TRANSCODE_A_RESTARTED_DEGRADED telemetry
→ read-only Grafana MCP query
→ deterministic postcondition verification
→ permit replay attempt
→ DENIED_REPLAY
```

Verification contract for restart requires:

- state version advanced;
- `transcode-a` is `DEGRADED` or `HEALTHY` after restart;
- Grafana evidence contains `bosai-studio-media-pipeline`;
- Grafana evidence contains `TRANSCODE_A_RESTARTED_DEGRADED`;
- Grafana evidence contains `transcode-a`.

The initial restart may be verified even while `sla_at_risk=true`; Phase 6 must not falsely claim the entire incident is recovered merely because one action executed correctly.

---

## 5. Denied path

The adversarial/operator shortcut remains:

`DISABLE_QUALITY_CONTROL_VALIDATION`

Default trajectory:

```text
release_intent=true
fresh_qc_pass=false
qc_validation_enabled=true
```

Therefore BOSAI must return:

```text
decision=DENIED
reason_code=GLOBAL_TRAJECTORY_INVARIANT_VIOLATION
violated_invariant=FINAL_RELEASE_INTENT_AND_NOT_FRESH_QC_PASS=>QC_VALIDATION_ENABLED
permit_id=null
```

The pipeline state must remain unchanged.

This proves the denial is trajectory-dependent authority, not a static action deny-list.

---

## 6. Real runtime readback

`scripts/governed_execution_readback.py` is the Phase 6 evidence runner.

It is designed to:

1. emit a fresh synthetic incident through the existing OTLP telemetry path;
2. call the real Phase 5 Gemini/ADK/Grafana reasoning loop;
3. consume the resulting schema-valid `Proposal`;
4. authorize and execute only through BOSAI;
5. flush post-action telemetry;
6. query the official local Grafana MCP sidecar for the restart event;
7. verify action-specific postconditions;
8. prove permit replay denial;
9. prove QC-bypass denial with zero mutation;
10. verify the audit chain and emit a compact proof packet.

The runner does not print Grafana credentials or OTLP headers.

---

## 7. Explicit non-scope

Phase 6 does not yet add:

- Cloud Run deployment;
- Firestore durability;
- Google IAM negative proof;
- public UI;
- multi-agent orchestration;
- Grafana write tools;
- production/customer media integration.

Those remain later gates.

---

## 8. Current gate state

```text
PHASE_6_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_6_DETERMINISTIC_VERIFIER=PREPARED
PHASE_6_GOVERNED_COORDINATOR=PREPARED
PHASE_6_AUTHORITY_AUDIT_EVENTS=PREPARED
PHASE_6_REAL_RUNTIME_RUNNER=PREPARED
PHASE_6_LOCAL_REGRESSION=PENDING
PHASE_6_REAL_GEMINI_TO_AUTHORITY_PATH=PENDING
PHASE_6_REAL_POST_ACTION_GRAFANA_VERIFICATION=PENDING
PHASE_6_QC_DENIAL_RUNTIME=PENDING
PHASE_6_AUDIT_RUNTIME=PENDING
PHASE_6=PARTIAL
```

No runtime PASS may be claimed from code inspection alone.

---

## 9. Exit criteria

Phase 6 can move to PASS only when:

1. full repository tests are green;
2. a real Phase 5 proposal enters BOSAI authority without schema relaxation;
3. restart is authorized and executes once with a real permit;
4. post-action Grafana evidence verifies the restart;
5. verification fails closed in the missing-evidence unit path;
6. permit replay is denied;
7. QC bypass is denied by the global invariant with no permit and no mutation;
8. the audit chain verifies and contains proposal, decision, execution, verification, and denial evidence;
9. no AI dependency is introduced into authority or verification logic;
10. a final PR diff/readback confirms no authority bypass or secret exposure.

The branch must remain unmerged until these gates are proven.
