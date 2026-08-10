# BOSAI Studio Control Plane — Phase 9 Cloud Run Runtime Enforcement Readiness

Status: **PASS — REAL CLOUD RUN RUNTIME IAM ENFORCEMENT PROVEN**  
Issue: **#18 — PHASE 9 — Cloud Run Runtime Enforcement Proof**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `804ae52044a263701b998bdad4b17d5705efe10d`  
Working branch: `phase/09-cloud-run-runtime-enforcement`

---

## 1. Phase decision

Phase 9 is **PASS**.

Phase 8 proved readiness only. Phase 9 deployed a minimal synthetic Cloud Run topology and captured real Google Cloud IAM runtime enforcement proof.

Proven runtime path:

```text
studio-control-plane
→ authority-executor
→ media-pipeline-sim
```

Proven denied edge:

```text
studio-control-plane ↛ media-pipeline-sim
```

Observed closure state:

```text
PHASE_9_LOCAL_REGRESSION=48_PASS
PHASE_9_DEPLOYMENT_HUMAN_GO=RECEIVED
PHASE_9_DRY_RUN_PLAN=PASS
PHASE_9_CLOUD_RUN_DEPLOYMENT=PASS
PHASE_9_RUNTIME_IAM_POSITIVE_PROOF=PASS
PHASE_9_RUNTIME_IAM_NEGATIVE_PROOF=PASS
PHASE_9_RUNTIME_IAM_ENFORCEMENT=PASS
PHASE_9_SECRET_VALUES_PRINTED=FALSE
PHASE_9=PASS
```

---

## 2. Operator authorization

The operator gave the explicit deployment authorization phrase:

```text
HUMAN GO PHASE 9 DEPLOYMENT
```

The deployment script required the matching environment variable before cloud mutation:

```text
BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO=HUMAN GO PHASE 9 DEPLOYMENT
```

The real deployment proof observed:

```text
human_go_verified=true
secret_values_printed=false
```

---

## 3. Synthetic runtime resources

Phase 9 deployed only minimal synthetic Cloud Run resources:

```text
studio-control-plane
authority-executor
media-pipeline-sim
```

The runtime proof app was deployed from this repository's Dockerfile. It is not a customer media workload.

---

## 4. Service identities

Distinct service accounts:

```text
sa-studio-control-plane
sa-authority-executor
sa-media-pipeline-sim
```

During the corrected redeploy, all three service accounts already existed:

```text
created=false
```

---

## 5. IAM bindings

Expected allowed invoker bindings were applied:

```text
sa-studio-control-plane → authority-executor
sa-authority-executor → media-pipeline-sim
```

The critical direct binding remained intentionally absent:

```text
sa-studio-control-plane ↛ media-pipeline-sim
```

---

## 6. First probe and correction

The first real probe showed negative edges working, but the positive chain failed with Cloud Run `404` before the app route executed.

Root cause:

```text
authority-executor and media-pipeline-sim used ingress=internal-and-cloud-load-balancing
while the proof chain invokes their run.app URLs using identity-token authentication.
```

Correction:

```text
allow_unauthenticated=false
ingress=all
roles/run.invoker only for the allowed service-account edge
```

This keeps services private by IAM while making the run.app authenticated proof possible.

---

## 7. Runtime IAM proof

The corrected probe returned:

```text
runtime_iam_enforcement_proven=true
secret_values_printed=false
```

Positive proof:

```text
studio-control-plane /health = 200
studio-control-plane → authority-executor = 200
authority-executor → media-pipeline-sim = 200
```

Negative proof:

```text
public internet → authority-executor = 403
public internet → media-pipeline-sim = 403
studio-control-plane → media-pipeline-sim = denied by Cloud Run IAM
```

Interpretation:

- public entrypoint works only on `studio-control-plane`;
- private services reject unauthenticated public access;
- `studio-control-plane` can invoke `authority-executor`;
- `authority-executor` can invoke `media-pipeline-sim`;
- `studio-control-plane` cannot invoke `media-pipeline-sim` directly.

---

## 8. Code shipped

### `src/bosai_studio/cloud_run_phase9.py`

Defines the Phase 9 Cloud Run deployment contract, Human GO guard, service-account mapping, allowed bindings, and intentionally absent bindings.

### `src/bosai_studio/cloud_run_runtime_app.py`

Defines the synthetic runtime proof app:

```text
/health
/execute-pipeline
/call-pipeline-direct
```

### `scripts/cloud_run_phase9_deploy.py`

Deploys only with both:

```text
--apply
BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO=HUMAN GO PHASE 9 DEPLOYMENT
```

### `scripts/cloud_run_phase9_proof.py`

Captures the positive and negative Cloud Run IAM runtime proof.

### `scripts/cloud_run_phase9_rollback.py`

Deletes the synthetic Cloud Run resources only with explicit rollback Human GO.

### `tests/test_cloud_run_phase9_deployment.py`

Covers exact Human GO gating, distinct service accounts, allowed bindings, absent direct binding, and private-by-IAM service behavior.

---

## 9. Regression proof

Complete repository regression returned:

```text
Ran 48 tests
OK
```

Existing Phase 0–8 tests remained part of the suite.

---

## 10. Security / dependency readback

Final Phase 9 readback requirements:

- no OpenAI dependency/reference;
- no Anthropic dependency/reference;
- no Firestore credential value;
- no Grafana/OTLP credential value;
- no identity token printed;
- no secret value printed;
- Gemini/ADK still has no direct pipeline edge;
- Grafana MCP remains observation-only;
- runtime resources are synthetic and isolated.

---

## 11. Explicit non-scope

Phase 9 does not add:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- persistent customer action execution.

---

## 12. Closure state

```text
PHASE_9=PASS
G9_A_REGRESSION=48_PASS
G9_B_HUMAN_GO_DEPLOYMENT=PASS
G9_C_CLOUD_RUN_DEPLOYMENT=PASS
G9_D_POSITIVE_RUNTIME_IAM_PROOF=PASS
G9_E_NEGATIVE_RUNTIME_IAM_PROOF=PASS
G9_F_SECRET_VALUES_PRINTED=FALSE
G9_G_IDENTITY_TOKENS_PRINTED=FALSE
```

Phase 9 is ready for final PR readback, red-team diff, and expected-SHA squash merge into `air`.
