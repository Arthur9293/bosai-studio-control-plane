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

Runtime image:

```text
us-docker.pkg.dev/cloudrun/container/hello
```

The image is used only to prove Cloud Run/IAM invocation behavior. It is not a customer media workload.

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

The probe script proves these by minting identity tokens for the service accounts and invoking the target Cloud Run services.

No identity token is printed.

---

## 6. Required negative IAM proofs

```text
sa-studio-control-plane ↛ media-pipeline-sim
public internet ↛ authority-executor
public internet ↛ media-pipeline-sim
```

The probe script must show non-2xx denial statuses for these paths.

---

## 7. Code prepared

### `src/bosai_studio/cloud_run_runtime_enforcement.py`

Defines:

- exact Human GO environment gate;
- synthetic runtime service definitions;
- service-account mapping;
- deployment command plan;
- allowed runtime proof edges;
- denied runtime proof edges;
- initial status `PREPARED_ONLY` until runtime proof passes.

### `scripts/cloud_run_runtime_plan.py`

Prints the Phase 9 runtime enforcement plan without mutation.

### `scripts/cloud_run_runtime_deploy.py`

Deploys only when both conditions hold:

1. `--execute` is passed;
2. `BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO` exactly equals `HUMAN GO PHASE 9 DEPLOYMENT`.

Otherwise it prints a plan and exits without mutation.

### `scripts/cloud_run_runtime_probe.py`

Performs positive and negative runtime IAM probes after deployment.

### `tests/test_cloud_run_runtime_enforcement.py`

Covers:

- exact Human GO requirement;
- distinct service accounts;
- unproven status before runtime probe;
- explicit mutating deployment commands;
- no direct `studio-control-plane → media-pipeline-sim` allow edge;
- required allowed and denied runtime proof edges.

---

## 8. Current gate state

```text
PHASE_9_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_9_DEPLOYMENT_HUMAN_GO=RECEIVED
PHASE_9_RUNTIME_PLAN=PREPARED
PHASE_9_DEPLOY_SCRIPT=PREPARED_GATED
PHASE_9_RUNTIME_PROBE=PREPARED
PHASE_9_LOCAL_REGRESSION=PENDING
PHASE_9_CLOUD_RUN_DEPLOYMENT=PENDING
PHASE_9_POSITIVE_IAM_PROOF=PENDING
PHASE_9_NEGATIVE_IAM_PROOF=PENDING
PHASE_9=PARTIAL
```

No runtime IAM enforcement PASS may be claimed before real Cloud Run probe evidence is captured.

---

## 9. Explicit non-scope

Phase 9 does not add:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- persistent customer action execution.

---

## 10. Exit criteria

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
