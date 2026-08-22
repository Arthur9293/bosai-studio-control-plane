# R1-D — Eligibility + Judge Experience Hardening

Status: **IMPLEMENTED — DRAFT PR #28 OPEN — NOT READY / NOT MERGED**
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
.github/workflows/r1-d-regression.yml
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

R1-D may be marked READY only after the **current PR head** satisfies:

```text
EXACT_HEAD_CHECKOUT=PASS
SOURCE_SYNTAX=PASS
JUDGE_SURFACE_TESTS=PASS
FULL_REGRESSION=PASS
GENERATED_SURFACE_CONTRACT=PASS
GENERATED_DOCS_INDEX_BYTE_MATCH=PASS
SECRET_MARKER_PREFLIGHT=PASS
DRAFT_PR_OPEN=true
AIR_UNCHANGED=true
DEVPOST_UNCHANGED=true
```

Implementation GO, CI PASS, and REVIEW do not by themselves authorize READY or MERGE.

## 8. Historical implementation readback — superseded where noted

First R1-D implementation commit:

```text
R1_D_IMPLEMENTATION_COMMIT=6653eebd42eec6511ce07b02fee9f78f3cacbe66
```

Validation performed against the initial R1-D judge-surface source content:

```text
SOURCE_SYNTAX=PASS
JUDGE_SURFACE_TESTS=PASS
JUDGE_SURFACE_TEST_COUNT=5
GENERATED_SURFACE_CONTRACT=PASS
SECRET_MARKER_PREFLIGHT=PASS
LIVE_CLOUD_MUTATION=false
CUSTOMER_WORKLOAD=false
```

At that earlier implementation point, the execution container could not clone GitHub because outbound DNS/network access was unavailable. The following values are therefore preserved strictly as **historical state at that point** and are superseded by Section 9 for regression status:

```text
HISTORICAL_FULL_REGRESSION=NOT_RERUN_ENVIRONMENT_NETWORK_BLOCKED
HISTORICAL_FULL_REGRESSION_STATUS=EXPLAINED_NOT_FABRICATED
HISTORICAL_GENERATED_DOCS_INDEX_BYTE_MATCH=NOT_ASSERTED
```

The pre-existing canonical Phase 12 evidence was 52/52 PASS at that time. R1-D changes remain limited to judge-facing presentation/tests, evidence, CI, and documentation; runtime authority code is untouched.

Historical post-implementation control readback:

```text
DRAFT_PR_OPEN=true
DRAFT_PR_NUMBER=28
PR_BASE=air
PR_BASE_SHA=5978a0b0ade8a73ccf28fbc78ec15a6fe6257167
PR_HEAD_BEFORE_REGISTER_CLOSEOUT=3abbc604784f67da6a3a1b0d80538851822fed4c
AIR_UNCHANGED=true
AIR_HEAD=5978a0b0ade8a73ccf28fbc78ec15a6fe6257167
DEVPOST_UNCHANGED=true
DEVPOST_PROJECT_STATE=published
```

## 9. R1-D R2 — superseding exact-head CI and generated-surface parity gate

Authorized R2 gate:

```text
GO R1-D R2 — EVIDENCE COHERENCE + GENERATED SURFACE PARITY
PR=28
AUTHORIZED_PRE_R2_HEAD=71d30dfecfb3796004ac3bd48c0f1a7772d94d3e
```

Before R2 mutation, GitHub Actions had already replaced the historical container limitation with a real exact-head regression proof:

```text
PRE_R2_CI_RUN=32596370532
PRE_R2_CI_JOB=97087905611
PRE_R2_EXPECTED_SHA=71d30dfecfb3796004ac3bd48c0f1a7772d94d3e
PRE_R2_CHECKED_OUT_SHA=71d30dfecfb3796004ac3bd48c0f1a7772d94d3e
PRE_R2_EXACT_HEAD_MATCH=true
PRE_R2_FULL_REGRESSION=PASS
PRE_R2_TEST_COUNT=53
PRE_R2_FAILURES=0
PRE_R2_ERRORS=0
PRE_R2_RENDER=PASS
PRE_R2_RENDER_CONTRACT=PASS
```

R2 strengthens the CI contract so the generated judge surface must also be byte-for-byte identical to the committed GitHub Pages source:

```text
python -m scripts.render_judge_demo
cmp -s build/judge-demo/index.html docs/index.html
```

The workflow logs both SHA-256 hashes before the comparison. A mismatch fails the job; no approximate or visual-only equivalence is accepted.

Because this register change itself creates a new PR head, the final R2 result must be read from GitHub Actions on the **current post-R2 exact head**. The repository intentionally does not hard-code a future untested head as PASS. The PR body / control-tower readback is the current-head evidence surface.

R2 does not authorize READY or MERGE. Those remain separate Human GO gates.
