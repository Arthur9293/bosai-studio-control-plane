# R1-D — Eligibility + Judge Experience Hardening

Status: **IMPLEMENTED + LOCAL SURFACE TESTED — DRAFT PR PENDING**
Date: **2026-08-22**
Contest: **Agentic Cinema: The Blockbuster Hackathon**
Selected track: **IBM**

## 1. Human GO

Authorized gate:

```text
GO R1-D — ELIGIBILITY + JUDGE EXPERIENCE HARDENING
EXACT HEAD 5978a0b0ade8a73ccf28fbc78ec15a6fe6257167
```

No authorization was granted to:

- modify Devpost;
- merge to `air`;
- expose secrets;
- change cloud IAM;
- deploy or mutate a customer workload;
- add a new runtime AI provider.

## 2. Fresh-read base lock

Immediately before branch creation:

```text
CANONICAL_BRANCH=air
CANONICAL_HEAD=5978a0b0ade8a73ccf28fbc78ec15a6fe6257167
EXPECTED_HEAD_MATCH=true
```

Working branch:

```text
milestone/agentic-cinema-r1-d-eligibility-judge-experience-hardening
```

## 3. Why R1-D exists

The original Phase 12 package passed the known submission requirements, but the post-submission audit identified three judge-risk surfaces:

1. **New Project Only interpretation risk**
   - the implementation is contest-period and clean-room, but the broader BOSAI governance thesis predates the contest;
   - the distinction must be explicit and evidence-backed rather than implied.

2. **Hosted project experience**
   - the existing page was informative but mostly static;
   - judges benefit from a credential-free product interaction that exposes both an authorized path and fail-closed denials.

3. **IBM track visibility**
   - IBM Bob evidence exists, but the judge should not have to discover the track qualification by searching the repository.

## 4. Hardening implemented

### Eligibility provenance

README now states the exact boundary:

```text
broader BOSAI governance thesis = predates contest
BOSAI Studio Control Plane implementation = contest-built clean-room project
```

The repository creation date and minimal initial-commit provenance are surfaced for judge review.

### Judge evidence map

Added:

```text
docs/devpost/JUDGE-EVIDENCE-MAP.md
```

It maps Stage-One eligibility/runtime questions directly to primary source evidence.

### Interactive judge replay

The judge surface source now exposes three deterministic outcomes:

```text
governed restart → AUTHORIZED
unsafe QC bypass → DENIED
consumed permit replay → DENIED
```

The page explicitly labels these as **recorded evidence replays**.

Critical non-claim:

```text
HOSTED_REPLAY_CALLS_LIVE_CLOUD=false
HOSTED_REPLAY_CONSUMES_REAL_PERMIT=false
HOSTED_REPLAY_MUTATES_PIPELINE=false
```

Real Google Cloud / Grafana runtime evidence remains grounded in the historical contest registers.

### IBM visibility

IBM Bob is surfaced directly as:

```text
IBM Bob — development-process partner
real usage evidenced
```

It is never presented as BOSAI runtime authority.

## 5. Files in R1-D implementation scope

```text
README.md
src/bosai_studio/judge_demo_surface.py
tests/test_judge_demo_surface.py
docs/devpost/JUDGE-EVIDENCE-MAP.md
docs/registers/r1-d/ELIGIBILITY-JUDGE-EXPERIENCE-HARDENING.md
docs/index.html
scripts/render_judge_demo.py
```

## 6. Runtime-authority boundary

R1-D is a judge-experience and eligibility-evidence change.

It does **not** alter:

- proposal contracts;
- deterministic authority evaluation;
- permit creation/consumption;
- Firestore state semantics;
- Cloud Run/IAM topology;
- Grafana credentials or MCP permissions;
- Gemini model/tool authority.

## 7. Required exit readback

R1-D may be marked READY only after:

```text
SOURCE_SYNTAX=PASS
JUDGE_SURFACE_TESTS=PASS
FULL_REGRESSION=PASS_OR_EXPLAINED
GENERATED_SURFACE_CONTRACT=PASS
SECRET_MARKER_PREFLIGHT=PASS
DRAFT_PR_OPEN=true
AIR_UNCHANGED=true
DEVPOST_UNCHANGED=true
```

Implementation GO does not authorize READY or MERGE.

## 8. Implementation readback

First R1-D implementation commit:

```text
R1_D_IMPLEMENTATION_COMMIT=6653eebd42eec6511ce07b02fee9f78f3cacbe66
```

Validation performed against the exact R1-D judge-surface source content:

```text
SOURCE_SYNTAX=PASS
JUDGE_SURFACE_TESTS=PASS
JUDGE_SURFACE_TEST_COUNT=5
GENERATED_SURFACE_CONTRACT=PASS
SECRET_MARKER_PREFLIGHT=PASS
LIVE_CLOUD_MUTATION=false
CUSTOMER_WORKLOAD=false
```

`docs/index.html` is being updated to the same interaction contract and content as the Python renderer. Byte-for-byte generator equivalence is not claimed in this gate because the execution environment cannot clone the remote repository to render and diff the committed branch.

The container could not clone GitHub because outbound DNS/network access is unavailable in the execution environment. Therefore the complete repository regression suite could not be freshly rerun from the remote branch in this gate.

```text
FULL_REGRESSION=NOT_RERUN_ENVIRONMENT_NETWORK_BLOCKED
FULL_REGRESSION_STATUS=EXPLAINED_NOT_FABRICATED
GENERATED_DOCS_INDEX_BYTE_MATCH=NOT_ASSERTED
```

The pre-existing canonical Phase 12 evidence remains 52/52 PASS. R1-D changes are limited to README, judge-surface presentation/tests, render metadata, evidence index and register; runtime authority code is untouched.

Remaining before READY:

```text
DRAFT_PR_OPEN=false
AIR_UNCHANGED=TO_BE_FRESH_READ
DEVPOST_UNCHANGED=TO_BE_FRESH_READ
```
