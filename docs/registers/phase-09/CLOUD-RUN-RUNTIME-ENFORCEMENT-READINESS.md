# BOSAI Studio Control Plane — Phase 9 Cloud Run Runtime Enforcement Readiness

Status: **PREPARED — DEPLOYMENT HUMAN GO RECEIVED / RUNTIME PROOF PENDING**  
Issue: **#18 — PHASE 9 — Cloud Run Runtime Enforcement Proof**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `804ae52044a263701b998bdad4b17d5705efe10d`  
Working branch: `phase/09-cloud-run-runtime-enforcement`

---

## 1. Phase objective

Phase 9 moves from Phase 8 readiness-only planning to real Google Cloud runtime enforcement proof.

Target path:

```text
studio-control-plane → authority-executor → media-pipeline-sim
```

Critical denied path:

```text
studio-control-plane ↛ media-pipeline-sim
```

The user/operator supplied the required deployment phrase:

```text
HUMAN GO PHASE 9 DEPLOYMENT
```

This authorizes a minimal, synthetic, isolated, reversible Cloud Run/IAM proof. It does not authorize customer workload, broad UI work, new AI authority, or non-Google AI dependencies.

---

## 2. Runtime proof topology

Cloud Run services:

```text
studio-control-plane
authority-executor
media-pipeline-sim
```

Distinct service accounts:

```text
sa-studio-control-plane
sa-authority-executor
sa-media-pipeline-sim
```

Allowed IAM invoker bindings:

```text
sa-studio-control-plane → authority-executor
sa-authority-executor → media-pipeline-sim
```

Intentionally absent binding:

```text
sa-studio-control-plane → media-pipeline-sim
```

---

## 3. Runtime app

`src/bosai_studio/cloud_run_runtime_app.py` provides a synthetic Cloud Run app used only for proof.

It exposes:

```text
/health
/execute-pipeline
/call-pipeline-direct
```

Expected proof behavior:

1. Public browser/operator can hit `studio-control-plane /health`.
2. Public unauthenticated access to `authority-executor /health` is denied.
3. Public unauthenticated access to `media-pipeline-sim /health` is denied.
4. `studio-control-plane /execute-pipeline` calls `authority-executor` with a runtime identity token.
5. `authority-executor` calls `media-pipeline-sim` with its runtime identity token.
6. `studio-control-plane /call-pipeline-direct` attempts the forbidden direct edge and receives denial.

No token value is returned by the app.

---

## 4. Deployment script

`scripts/cloud_run_phase9_deploy.py`

Guards:

```text
BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO="HUMAN GO PHASE 9 DEPLOYMENT"
--apply
```

Default behavior without `--apply` is dry-run plan only.

Mutations when applied:

- create missing service accounts;
- deploy the three synthetic Cloud Run services from the repository Dockerfile;
- set distinct service accounts;
- configure studio as unauthenticated public entrypoint;
- configure authority/pipeline as non-unauthenticated services;
- add only the two required `roles/run.invoker` bindings.

---

## 5. Proof script

`scripts/cloud_run_phase9_proof.py`

Read/probe behavior:

- discovers Cloud Run service URLs;
- probes public studio health;
- probes public unauthenticated denial for authority and pipeline;
- probes studio-to-authority-to-pipeline success;
- probes studio-to-pipeline direct denial;
- emits a JSON proof packet;
- returns nonzero if any required proof fails.

---

## 6. Rollback script

`scripts/cloud_run_phase9_rollback.py`

Guards:

```text
BOSAI_PHASE9_ROLLBACK_HUMAN_GO="HUMAN GO PHASE 9 ROLLBACK"
--apply
```

Rollback deletes the isolated proof services and service accounts.

---

## 7. Current gate state

```text
PHASE_9_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_9_DEPLOYMENT_HUMAN_GO=RECEIVED
PHASE_9_DEPLOYMENT_SCRIPT=PREPARED
PHASE_9_PROOF_SCRIPT=PREPARED
PHASE_9_ROLLBACK_SCRIPT=PREPARED
PHASE_9_LOCAL_REGRESSION=PENDING
PHASE_9_REAL_CLOUD_RUN_DEPLOYMENT=PENDING
PHASE_9_RUNTIME_IAM_POSITIVE_PROOF=PENDING
PHASE_9_RUNTIME_IAM_NEGATIVE_PROOF=PENDING
PHASE_9=PARTIAL
```

No runtime enforcement PASS is claimed until the proof script succeeds against real Cloud Run services.

---

## 8. Explicit non-scope

Phase 9 does not authorize:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- Gemini/ADK direct pipeline credentials;
- Grafana MCP mutation credentials.

---

## 9. Exit criteria

Phase 9 may move to PASS only when:

1. full repository regression is green;
2. deployment script runs under the exact Human GO guard;
3. real Cloud Run services exist with distinct service accounts;
4. allowed IAM invoker bindings exist only for studio→authority and authority→pipeline;
5. studio→authority→pipeline positive proof succeeds;
6. studio→pipeline direct proof is denied;
7. public unauthenticated authority/pipeline access is denied;
8. proof packet prints no secret values;
9. rollback path is available;
10. final diff/readback confirms no OpenAI/Anthropic dependency, no secrets, and no authority bypass.

The branch remains unmerged until all runtime proof gates pass, or until the phase is explicitly downgraded without claiming runtime enforcement.
