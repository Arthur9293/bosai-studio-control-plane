# BOSAI Studio Control Plane — Phase 12 IBM Partner Track & Hosted Public Demo URL

Status: **PREPARED — IBM TRACK LOCK / PUBLIC URL NOT YET CLAIMED**  
Issue: **#25 — PHASE 12 — IBM Partner Track Lock & Hosted Public Demo URL**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `e228dfad7ca50e0c7df28ec48a1a3d9c8f849fb5`  
Working branch: `phase/12-ibm-partner-track-public-demo-url`

---

## Phase decision

Phase 12 corrects the submission strategy after live Devpost rules readback.

Current Partner Entity / track lock:

```text
SELECTED_PARTNER_TRACK=IBM
GRAFANA_ROLE=TECHNICAL_PROOF_SUPPORTING_OBSERVABILITY_NOT_SELECTED_PARTNER_TRACK
IBM_BOB_REQUIRED=true
PUBLIC_URL_CLAIMED=false
SUBMISSION_READY=false
```

BOSAI’s Grafana Cloud + official Grafana MCP proof remains valuable evidence for operational truth, but the current rules surface IBM as the selected partner track and require IBM Bob as part of the development process.

---

## Current contest interpretation

The project direction must now be packaged as:

```text
Google Cloud + Gemini + BOSAI governed studio control plane + IBM partner track
```

The existing proof base remains intact:

```text
Grafana observes
Gemini proposes
BOSAI authorizes
Firestore persists
Cloud Run/IAM enforces
Verifier proves
```

But final Devpost packaging must not claim Grafana as the selected partner track unless the live submission form explicitly allows that track.

---

## Phase 12 goals

1. Lock IBM as the selected partner track.
2. Define how IBM Bob is used in the build/development process.
3. Decide whether IBM usage needs source-level evidence, README evidence, or Devpost-copy evidence.
4. Prepare hosted public demo URL path.
5. Preserve no-secret/no-token/no-new-authority constraints.
6. Avoid final Devpost submission claims.

---

## Hosted URL options

Phase 12 can use one of these approaches:

### Option A — GitHub Pages / static hosting

Pros:
- fits the Phase 10 static HTML artifact;
- minimal runtime risk;
- no new authority surface;
- clean public URL proof.

Cons:
- less representative of Cloud Run runtime.

### Option B — Cloud Run public demo surface

Pros:
- aligns with Phase 9 Cloud Run runtime proof;
- Google Cloud-native hosted URL.

Cons:
- requires explicit Human GO because it mutates public hosting configuration;
- must avoid exposing secrets/tokens.

Recommended initial path:

```text
OPTION_A_STATIC_PUBLIC_URL_FIRST
```

Cloud Run runtime proof already exists from Phase 9; the judge-facing demo URL can be static without weakening the governance claim.

---

## Mutation gate

No public hosting mutation is authorized by this register.

Required exact phrase before any public deployment mutation:

```text
HUMAN GO PHASE 12 PUBLIC DEMO DEPLOYMENT
```

Until that phrase is received and applied through a gated script/action:

```text
PHASE_12_PUBLIC_DEPLOYMENT=NOT_AUTHORIZED
PHASE_12_PUBLIC_URL_CLAIMED=FALSE
```

---

## Non-scope

```text
new_ai_provider=false
openai_runtime_dependency=false
anthropic_runtime_dependency=false
new_authority_path=false
customer_media_workload=false
devpost_submission=false
video_recording=false
cloud_run_mutation=false_without_human_go
```

---

## Current blockers

```text
IBM_BOB_USAGE_EVIDENCE=MISSING
PUBLIC_HOSTED_URL=MISSING
FINAL_README_PACKAGING=MISSING
THREE_MINUTE_VIDEO=MISSING
DEVPOST_COPY=MISSING
FINAL_SUBMISSION_READBACK=MISSING
```

---

## Closure states

### Partner-track-lock PASS

Allowed when:

```text
SELECTED_PARTNER_TRACK=IBM
IBM_BOB_USAGE_PLAN=DOCUMENTED
PUBLIC_URL_CLAIMED=FALSE
SUBMISSION_READY=FALSE
```

### Hosted-public-demo PASS

Allowed only when:

```text
PUBLIC_DEPLOYMENT_HUMAN_GO=RECEIVED
PUBLIC_URL_DEPLOYED=TRUE
PUBLIC_URL_READBACK=PASS
SECRET_VALUES_PRINTED=FALSE
IDENTITY_TOKENS_PRINTED=FALSE
SUBMISSION_READY=FALSE
```

Final Devpost submission remains a later phase.
