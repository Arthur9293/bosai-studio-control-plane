# BOSAI Studio Control Plane — Phase 8 Cloud Run IAM Boundary Readiness

Status: **PASS — READINESS-ONLY CLOUD RUN/IAM BOUNDARY PROVEN**  
Issue: **#16 — PHASE 8 — Cloud Run IAM Runtime Boundary**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `d894a0493e27f404dbdcf98e8f2059f18ad176e1`  
Working branch: `phase/08-cloud-run-iam-boundary`

---

## 1. Phase decision

Phase 8 is **READINESS-ONLY PASS**.

Phase 7 proved durable Firestore authority. Phase 8 prepares the Google Cloud runtime boundary required by Architecture V1 without deploying new Cloud Run services and without claiming runtime IAM enforcement.

Canonical intended control path remains:

```text
studio-control-plane
→ authority-executor
→ media-pipeline-sim
```

Critical denied edge:

```text
studio-control-plane ↛ media-pipeline-sim
```

Observed closure state:

```text
PHASE_8_LOCAL_REGRESSION=42_PASS
PHASE_8_LOCAL_BOUNDARY_CONTRACT=PASS
PHASE_8_GCP_READ_ONLY_PREFLIGHT=PASS
PHASE_8_BOUNDARY_PLAN=PASS
PHASE_8_CLOUD_MUTATION=FALSE
PHASE_8_DEPLOYMENT_AUTHORIZED=FALSE
PHASE_8_RUNTIME_IAM_ENFORCEMENT_PROVEN=FALSE
PHASE_8=READINESS_ONLY_PASS
```

---

## 2. Canonical service identities

```text
sa-studio-control-plane
sa-authority-executor
sa-media-pipeline-sim
```

Each maps to the active project as:

```text
<service-account-id>@<project>.iam.gserviceaccount.com
```

The identities are distinct. No general project Owner/Editor role is authorized by this contract.

---

## 3. Canonical service exposure intent

```text
studio-control-plane: public entrypoint for judges / operator browser
```

```text
authority-executor: private Cloud Run service
```

```text
media-pipeline-sim: private Cloud Run service
```

The private services must not be unauthenticated public endpoints.

---

## 4. Allowed invocation edges

```text
sa-studio-control-plane → authority-executor
sa-authority-executor → media-pipeline-sim
```

These are the only service-to-service invocation edges permitted by Phase 8's local contract.

Observed boundary-plan output included the same allowed edges:

```text
studio-control-plane -> authority-executor
authority-executor -> media-pipeline-sim
```

---

## 5. Denied invocation edges

```text
sa-studio-control-plane → media-pipeline-sim
Gemini / ADK → media-pipeline-sim
Grafana MCP → media-pipeline-sim
public internet → authority-executor
public internet → media-pipeline-sim
```

Undeclared edges fail closed.

Observed boundary-plan output confirmed denied edges for:

```text
studio-control-plane -> media-pipeline-sim
gemini-adk -> media-pipeline-sim
mcp-grafana -> media-pipeline-sim
public-internet -> authority-executor
public-internet -> media-pipeline-sim
```

---

## 6. Regression proof

Complete repository regression returned:

```text
Ran 42 tests
OK
```

The added Phase 8 tests cover:

- distinct service accounts;
- only expected allowed edges;
- denied direct studio-to-pipeline edge;
- denied Gemini/ADK and Grafana MCP pipeline edges;
- denied public access to private services;
- undeclared edges fail closed;
- plan remains readiness-only until real IAM proof exists.

Existing Phase 0–7 tests remain part of the mandatory regression.

---

## 7. Real GCP read-only preflight

`python -m scripts.cloud_run_gcp_preflight` was executed against:

```text
GOOGLE_CLOUD_PROJECT=bosai-gemini-xprize
GOOGLE_CLOUD_LOCATION=global
```

Read-only command families returned `returncode=0`:

```text
gcloud run services list
gcloud iam service-accounts list
```

This proves the operator environment can inspect Cloud Run and IAM state for the target project.

The command output was intentionally not copied into this register because it included existing Cloud Run metadata and logical Secret Manager references. No secret values were captured or committed.

---

## 8. Non-mutating boundary plan

`python -m scripts.cloud_run_boundary_plan` emitted a static readiness plan with:

```text
deployment_authorized=false
runtime_iam_enforcement_proven=false
```

Interpretation:

- Cloud Run deployment is not authorized by Phase 8 readiness-only closure;
- no cloud resource was created, updated, deleted, or rebound;
- runtime IAM enforcement is not claimed;
- this phase proves design, tests, and operator/project preflight only.

---

## 9. Code prepared

### `src/bosai_studio/cloud_run_boundary.py`

Defines:

- canonical service names;
- canonical service identities;
- service exposure intent;
- allowed invocation edges;
- denied invocation edges;
- fail-closed edge decision logic;
- a read-only deployment/readiness plan.

### `scripts/cloud_run_boundary_plan.py`

Prints the current non-mutating Cloud Run/IAM boundary plan from environment variables.

### `scripts/cloud_run_gcp_preflight.py`

Runs read-only `gcloud` preflight commands:

- active account readback;
- Cloud Run service listing;
- service account listing.

It must not create, deploy, bind, delete, or mutate cloud resources.

### `tests/test_cloud_run_boundary.py`

Covers the local service identity and invocation-edge contract.

---

## 10. Security / dependency readback

Phase 8 final readback requirements:

- no OpenAI dependency/reference;
- no Anthropic dependency/reference;
- no Firestore credential value;
- no Grafana/OTLP credential value;
- no new AI/model authority surface;
- no Cloud Run deployment command executed;
- no IAM binding mutation executed;
- no public exposure of private services.

---

## 11. Explicit non-scope

Phase 8 does not yet authorize:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- any Cloud Run deployment without explicit Human GO.

---

## 12. Closure state

```text
PHASE_8=READINESS_ONLY_PASS
G8_A_REGRESSION=42_PASS
G8_B_LOCAL_BOUNDARY_CONTRACT=PASS
G8_C_GCP_READ_ONLY_PREFLIGHT=PASS
G8_D_BOUNDARY_PLAN=PASS
G8_E_CLOUD_MUTATION=FALSE
G8_F_DEPLOYMENT_AUTHORIZED=FALSE
G8_G_RUNTIME_IAM_ENFORCEMENT_PROVEN=FALSE
```

Phase 8 is ready for final PR readback and expected-SHA squash merge into `air` as a readiness-only milestone.
