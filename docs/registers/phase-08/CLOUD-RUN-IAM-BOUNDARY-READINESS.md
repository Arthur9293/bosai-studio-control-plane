# BOSAI Studio Control Plane — Phase 8 Cloud Run IAM Boundary Readiness

Status: **PREPARED — LOCAL REGRESSION AND REAL GCP PREFLIGHT PENDING**  
Issue: **#16 — PHASE 8 — Cloud Run IAM Runtime Boundary**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `d894a0493e27f404dbdcf98e8f2059f18ad176e1`  
Working branch: `phase/08-cloud-run-iam-boundary`

---

## 1. Phase objective

Phase 8 begins the Google Cloud runtime boundary work.

Phase 7 proved durable Firestore authority. Phase 8 does not add more AI. It defines and prepares the Cloud Run/IAM service identity boundary required by Architecture V1:

```text
studio-control-plane
→ authority-executor
→ media-pipeline-sim
```

and the critical denied edge:

```text
studio-control-plane ↛ media-pipeline-sim
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

---

## 6. Code prepared

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

Covers:

- distinct service accounts;
- only expected allowed edges;
- denied direct studio-to-pipeline edge;
- denied Gemini/ADK and Grafana MCP pipeline edges;
- denied public access to private services;
- undeclared edges fail closed;
- plan remains readiness-only until real IAM proof exists.

---

## 7. Current gate state

```text
PHASE_8_CODE_PREPARATION=PASS_PENDING_TEST_READBACK
PHASE_8_LOCAL_BOUNDARY_CONTRACT=PREPARED
PHASE_8_GCP_PREFLIGHT_SCRIPT=PREPARED
PHASE_8_REAL_GCP_PREFLIGHT=PENDING
PHASE_8_REAL_CLOUD_RUN_DEPLOYMENT=PENDING
PHASE_8_RUNTIME_IAM_POSITIVE_PROOF=PENDING
PHASE_8_RUNTIME_IAM_NEGATIVE_PROOF=PENDING
PHASE_8=PARTIAL
```

No runtime IAM enforcement PASS may be claimed from local contract alone.

---

## 8. Explicit non-scope

Phase 8 does not yet authorize:

- customer/production media workload;
- broad public UI polish;
- generic RBAC system;
- multi-agent orchestration;
- Grafana write tools;
- non-Google AI dependency;
- any Cloud Run deployment without explicit Human GO.

---

## 9. Exit criteria

Phase 8 can move to PASS only if one of these clearly labeled outcomes is reached:

### Readiness-only PASS

- full repository regression is green;
- local boundary contract is tested;
- real GCP read-only preflight succeeds;
- no cloud mutation occurs;
- register explicitly says runtime IAM enforcement is not yet proven.

### Runtime-enforcement PASS

- full repository regression is green;
- minimal synthetic Cloud Run services are deployed with distinct service identities;
- allowed service-to-service invocations succeed;
- direct studio-to-pipeline invocation is denied;
- public unauthenticated invocation of private services is denied;
- no secret values are exposed;
- deployment is reversible and isolated.

The current branch starts as readiness-only until the user explicitly authorizes deployment work.
