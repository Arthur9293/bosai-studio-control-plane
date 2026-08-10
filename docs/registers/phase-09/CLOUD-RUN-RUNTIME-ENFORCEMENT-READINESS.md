# BOSAI Studio Control Plane — Phase 9 Cloud Run Runtime Enforcement Readiness

Status: **PREPARED — DEPLOYMENT AUTHORIZED, RUNTIME PROOF PENDING**  
Issue: **#18 — PHASE 9 — Cloud Run Runtime Enforcement Proof**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `804ae52044a263701b998bdad4b17d5705efe10d`  
Working branch: `phase/09-cloud-run-runtime-enforcement`

---

## 1. Phase objective

Phase 9 moves from Phase 8 readiness-only Cloud Run/IAM boundary planning to real runtime enforcement proof.

The intended runtime path remains:

```text
studio-control-plane
→ authority-executor
→ media-pipeline-sim
```

The critical denied edge remains:

```text
studio-control-plane ↛ media-pipeline-sim
```

---

## 2. Operator authorization

The operator gave the explicit deployment authorization phrase:

```text
HUMAN GO PHASE 9 DEPLOYMENT
```

The deployment script still requires the matching environment variable before any cloud mutation:

```text
BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO=HUMAN GO PHASE 9 DEPLOYMENT
```

This prevents accidental deployment from code checkout or script discovery.

---

## 3. Synthetic runtime resources

Phase 9 prepares only minimal synthetic Cloud Run resources:

```text
studio-control-plane
authority-executor
media-pipeline-sim
```

The runtime proof app is deployed from this repository's Dockerfile.

The app is used only to prove Cloud Run/IAM invocation behavior. It is not a customer media workload.

---

## 4. Service identities

Distinct service accounts:

```text
sa-studio-control-plane
sa-authority-executor
sa-media-pipeline-sim
```

Expected emails are generated as:

```text
<service-account-id>@<project>.iam.gserviceaccount.com
```

---

## 5. Required positive IAM proofs

```text
sa-studio-control-plane → authority-executor
sa-authority-executor → media-pipeline-sim
```

The proof path is:

```text
public caller → studio-control-plane /execute-pipeline
studio-control-plane service identity → authority-executor /execute-pipeline
authority-executor service identity → media-pipeline-sim /health
```

No identity token is printed.

---

## 6. Required negative IAM proofs

```text
sa-studio-control-plane ↛ media-pipeline-sim
public internet ↛ authority-executor
public internet ↛ media-pipeline-sim
```

The probe script must show denial for these paths.

---

## 7. Runtime correction after first probe

First real probe showed the negative edges working but the positive chain failing with Cloud Run 404 responses before the app route executed.

Root cause: `authority-executor` and `media-pipeline-sim` used `ingress=internal-and-cloud-load-balancing`, while the Phase 9 proof chain invokes their `run.app` URLs using identity-token authentication.

Correction: keep the services non-public through Cloud Run IAM, not ingress isolation:

```text
allow_unauthenticated=false
ingress=all
roles/run.invoker only for the allowed service account edge
```

This allows the positive service-to-service `run.app` proof while keeping unauthenticated public access denied and keeping `studio-control-plane ↛ media-pipeline-sim` denied by missing invoker binding.

---

## 8. Code prepared

### `src/bosai_studio/cloud_run_phase9.py`

Defines:

- exact Human GO environment gate;
- synthetic runtime service definitions;
- service-account mapping;
- allowed invoker bindings;
- intentionally absent bindings;
- private-by-IAM service exposure semantics.

### `src/bosai_studio/cloud_run_runtime_app.py`

Defines the synthetic runtime proof app with:

- `/health`;
- `/execute-pipeline`;
- `/call-pipeline-direct`.

### `scripts/cloud_run_phase9_deploy.py`

Deploys only when both conditions hold:

1. `--apply` is passed;
2. `BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO` exactly equals `HUMAN GO PHASE 9 DEPLOYMENT`.

Otherwise it prints a dry-run plan and exits without mutation.

### `scripts/cloud_run_phase9_proof.py`

Performs positive and negative runtime IAM probes after deployment.

### `scripts/cloud_run_phase9_rollback.py`

Deletes the synthetic Cloud Run resources only with explicit rollback Human GO.

### `tests/test_cloud_run_phase9_deployment.py`

Covers:

- exact Human GO requirement;
- distinct service accounts;
- unproven status before runtime probe;
- explicit allowed bindings;
- absent direct studio-to-pipeline binding;
- private services are not unauthenticated public.

---

## 9. Current gate state

```text
PHASE_9_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_9_DEPLOYMENT_HUMAN_GO=RECEIVED
PHASE_9_DRY_RUN_PLAN=PASS
PHASE_9_LOCAL_REGRESSION=48_PASS
PHASE_9_CLOUD_RUN_DEPLOYMENT=DEPLOYED_PENDING_REPROBE
PHASE_9_FIRST_PROBE_NEGATIVE_EDGES=PASS
PHASE_9_FIRST_PROBE_POSITIVE_CHAIN=FAIL_INGRESS_404
PHASE_9_INGRESS_CORRECTION=PREPARED
PHASE_9_POSITIVE_IAM_PROOF=PENDING
PHASE_9_NEGATIVE_IAM_PROOF=PENDING_REPROBE
PHASE_9=PARTIAL
```

No runtime IAM enforcement PASS may be claimed before real Cloud Run probe evidence is captured.

---

## 10. Explicit non-scope

Phase 9 does not add:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- persistent customer action execution.

---

## 11. Exit criteria

Phase 9 may move to PASS only when:

1. full repository regression is green;
2. runtime plan is printed and reviewed;
3. deployment script runs with explicit Human GO env gate;
4. Cloud Run services exist with distinct service accounts;
5. allowed invocation `studio → authority` succeeds;
6. allowed invocation `authority → pipeline` succeeds;
7. direct invocation `studio → pipeline` is denied;
8. unauthenticated public invocation of private services is denied;
9. probe output prints no secret or identity token values;
10. final diff/readback finds no OpenAI/Anthropic dependency and no authority bypass.

The branch remains unmerged until real runtime enforcement evidence exists or the phase is explicitly downgraded.
