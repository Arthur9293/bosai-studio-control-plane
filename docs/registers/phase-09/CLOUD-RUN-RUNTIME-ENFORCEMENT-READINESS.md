# BOSAI Studio Control Plane — Phase 9 Cloud Run Runtime Enforcement Readiness

Status: **PASS — REAL CLOUD RUN RUNTIME IAM ENFORCEMENT PROVEN**  
Issue: **#18 — PHASE 9 — Cloud Run Runtime Enforcement Proof**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `804ae52044a263701b998bdad4b17d5705efe10d`  
Working branch: `phase/09-cloud-run-runtime-enforcement`

## Phase decision

Phase 9 is **PASS**.

Phase 8 proved readiness only. Phase 9 deployed a minimal synthetic Cloud Run topology and captured real Google Cloud IAM runtime enforcement proof.

Proven runtime path:

```text
studio-control-plane → authority-executor → media-pipeline-sim
```

Proven denied edge:

```text
studio-control-plane ↛ media-pipeline-sim
```

## Runtime IAM proof

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

## Deployment proof

The operator gave the explicit deployment authorization phrase:

```text
HUMAN GO PHASE 9 DEPLOYMENT
```

The real deployment proof observed:

```text
human_go_verified=true
secret_values_printed=false
```

Expected allowed invoker bindings were applied:

```text
sa-studio-control-plane → authority-executor
sa-authority-executor → media-pipeline-sim
```

The critical direct binding remained intentionally absent:

```text
sa-studio-control-plane ↛ media-pipeline-sim
```

## First probe correction

The first real probe showed negative edges working, but the positive chain failed with Cloud Run `404` before the app route executed.

Correction:

```text
allow_unauthenticated=false
ingress=all
roles/run.invoker only for the allowed service-account edge
```

This keeps services private by IAM while making the run.app authenticated proof possible.

## Code shipped

- `Dockerfile`
- `src/bosai_studio/cloud_run_phase9.py`
- `src/bosai_studio/cloud_run_runtime_app.py`
- `scripts/cloud_run_phase9_deploy.py`
- `scripts/cloud_run_phase9_proof.py`
- `scripts/cloud_run_phase9_rollback.py`
- `tests/test_cloud_run_phase9_deployment.py`

## Regression proof

```text
Ran 48 tests
OK
```

## Security / dependency readback

- no OpenAI dependency/reference;
- no Anthropic dependency/reference;
- no Firestore credential value;
- no Grafana/OTLP credential value;
- no identity token printed;
- no secret value printed;
- Gemini/ADK still has no direct pipeline edge;
- Grafana MCP remains observation-only;
- runtime resources are synthetic and isolated.

## Closure state

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
