# IBM Bob Usage Evidence — Phase 12

Status: **REAL IBM BOB RUN CAPTURED — EVIDENCE COMMITTED / PUSHED / PUBLIC DEMO LIVE**

This file is BOSAI's Phase 12 evidence capture point for documenting real
IBM Bob usage for the Devpost Agentic Cinema IBM partner track.

---

## Current state

```text
IBM_BOB_USED=true
IBM_BOB_USAGE_PROVEN=true
IBM_BOB_EVIDENCE_COMMITTED=true
IBM_BOB_EVIDENCE_COMMIT=4c4075fd0ba744c86cd8e1e649f0a9338351115d
IBM_BOB_EVIDENCE_COMMIT_SCOPE=LOCAL_GIT_COMMIT_PUSHED_TO_REMOTE_BRANCH
GITHUB_PUSHED=true
GITHUB_REMOTE_BRANCH=refs/heads/phase/12-ibm-partner-track-public-demo-url
GITHUB_REMOTE_HEAD=a9a4b3aa72ab92cf0b30047ffeeb89aad4b4cdd3
PUBLIC_URL_CLAIMED=true
PUBLIC_URL=https://arthur9293.github.io/bosai-studio-control-plane/
PUBLIC_URL_READBACK=PASS_HUMAN_BROWSER_DESKTOP_AND_MOBILE
PUBLIC_URL_HTTP_READBACK=PASS
PUBLIC_URL_HTTP_STATUS=200
PUBLIC_DEPLOYMENT=GITHUB_PAGES_STATIC_DOCS_BRANCH
SUBMISSION_READY=false
SECRET_VALUES_EXPOSED=false
IDENTITY_TOKENS_EXPOSED=false
DEPLOYMENT_ATTEMPTED=true
DEPLOYMENT_KIND=GITHUB_PAGES_STATIC_DOCS_BRANCH_PUSH
```

---

## Evidence record

```text
IBM_BOB_USED=true
BOB_IDE_VERSION_OR_CONTEXT=IBM Bob IDE on macOS; exact version not captured
BOB_MODE=Plan+Agent
```

### Prompt summary

IBM Bob was asked to:

- inspect the Phase 12 authority guardrails and submission-readiness context;
- review the repository for IBM partner-track readiness;
- produce a bounded Plan-mode gap analysis (zero file modifications);
- propose development-process improvements that preserve the canonical
  architecture:
    Grafana observes
    Gemini proposes
    BOSAI authorizes
    Firestore persists
    Cloud Run/IAM enforces
    Verifier proves
- avoid runtime-authority changes;
- avoid public deployment;
- avoid OpenAI/Anthropic runtime dependencies;
- make only human-reviewed controlled edits within the authorized write
  allowlist.

### Files inspected

```text
BOB_FILES_INSPECTED=
  .bob/rules/bosai_phase12_authority_guardrails.md
  docs/devpost/IBM-BOB-RUNBOOK.md
  docs/devpost/IBM-BOB-USAGE-EVIDENCE.md
  docs/registers/phase-12/IBM-PARTNER-TRACK-PUBLIC-DEMO-URL.md
  docs/registers/phase-11/DEVPOST-COMPLIANCE-ALIGNMENT.md
  docs/registers/phase-10/PUBLIC-JUDGE-DEMO-READINESS.md
  src/bosai_studio/judge_demo_surface.py
  tests/test_judge_demo_surface.py
  scripts/render_judge_demo.py
  pyproject.toml
  README.md
```

### Implementation files changed

```text
IMPLEMENTATION_FILES_CHANGED=
  README.md
  src/bosai_studio/judge_demo_surface.py
  tests/test_judge_demo_surface.py

EVIDENCE_FILE_CHANGE=WRITTEN_BY_AUTHORIZED_EDIT_D_PENDING_FINAL_HUMAN_REVIEW

BOB_FILES_CHANGED=
  README.md
  src/bosai_studio/judge_demo_surface.py
  tests/test_judge_demo_surface.py
  docs/devpost/IBM-BOB-USAGE-EVIDENCE.md
```

### Bob contributions

**Plan mode:**

- Read 11 repository files and established current state.
- Identified bounded Phase 12 development-process gaps and improvements,
  including README packaging, IBM Bob usage evidence, Phase 12 register
  closeout requirements, and a high-value judge-facing IBM partner-track
  visibility improvement.
- Produced a structured nine-section Phase 12 gap analysis and edit plan
  in chat (zero file modifications, as required by the Plan-only
  authorization).
- Preserved runtime-authority boundaries throughout.

**Agent mode:**

1. `README.md` — expanded from 2 lines to a judge-readable project README
   including the canonical architecture statement, governed workflow table,
   stack table, IBM partner-track section, local demo run instructions, and
   phase register trail reference. Final content is Revision 2.1 after three
   human review cycles.
2. `src/bosai_studio/judge_demo_surface.py` — appended one IBM
   development-process `ProofCard` to `PROOF_CARDS` (append-only; all six
   existing cards preserved; no authority logic changed):
   label: "IBM partner track"
   value: "IBM Bob — development process partner"
   status: "not runtime authority"
3. `tests/test_judge_demo_surface.py` — appended two IBM rendering assertions
   to the existing `required` list in
   `test_demo_contains_required_authority_claims` (all prior assertions
   preserved):
   "IBM Bob — development process partner"
   "not runtime authority"
4. Local regression verified (see test evidence below).

### Human review — accepted

```text
IMPLEMENTATION_EDITS_HUMAN_REVIEWED=true
EVIDENCE_FILE_FINAL_HUMAN_REVIEW=PASS
```

The following were accepted by human review before write authorization:

- README Revision 2.1 (three review cycles; see rejected/corrected below).
- Append-only IBM ProofCard:
    label: "IBM partner track"
    value: "IBM Bob — development process partner"
    status: "not runtime authority"
- Two IBM test assertion strings in
  `test_demo_contains_required_authority_claims`.
- 52-test regression result (PASS).

### Human review — rejected / corrected

The following Bob proposals were rejected or required correction during this
session:

- **Plan-mode file write rejected:** A Plan-mode attempt to write a plan file
  to the repository was rejected because the Plan-only authorization required
  FILES_MODIFIED=0. The plan was returned in chat only.

- **README "Gemini observes and proposes" rejected:** README Revision 1
  contained the phrase "Gemini observes and proposes." This misattributed
  the observation layer to Gemini rather than Grafana. The sentence was
  corrected to the canonical six-line architecture statement.

- **"BOSAI is submitted under the IBM partner track" rejected:** This wording
  implied that the Devpost final submission had already occurred.
  SUBMISSION_READY remains false. Replaced with:
  "Phase 12 locks IBM as the selected partner track."

- **Incorrect PROVE semantics corrected:** The PROVE row in the workflow
  table incorrectly described the Verifier as checking postconditions against
  the Firestore audit record. The correct semantics are that the Verifier
  checks authoritative state and run-bound telemetry evidence
  deterministically; Firestore separately persists durable authority and
  audit state.

- **Future Bob work not claimed before completion:** An early README draft
  listed IBM ProofCard addition and evidence-file update as already-completed
  Bob contributions at a point when neither had yet been written. This was
  rejected; the IBM Bob contributions list was scoped to only work actually
  completed at each point in the controlled execution.

- **IBM ProofCard formal requirement not claimed:** The IBM judge-facing
  ProofCard was accepted as a high-value judge-facing improvement, not as a
  proven formal Devpost requirement. No claim was made that Devpost formally
  required this card.

- **Evidence file scope corrected:** The evidence file description was
  corrected to state that this is BOSAI's own control artifact for
  documenting IBM Bob usage. No claim was made that Devpost requires this
  exact repository file.

---

## Test evidence

```text
UNITTEST_COMMAND_OBSERVED=.venv/bin/python -m unittest discover -s tests
UNITTEST_CANONICAL_COMMAND=python -m unittest discover -s tests -v
UNITTEST_COMMAND_VARIANCE=missing_-v_on_observed_execution
UNITTEST_SCOPE_EQUIVALENT=true
UNITTEST_RESULT=PASS
UNITTEST_TEST_COUNT=52
UNITTEST_FAILURE_COUNT=0
UNITTEST_ERROR_COUNT=0
UNITTEST_RERUN_PERFORMED=false
HEAD_UNCHANGED=true
HEAD=6b5c8be3ee8b28056c26fe7ec5a4636081a0d79a
```

Note: the `-v` flag controls verbosity only. The observed execution
`.venv/bin/python -m unittest discover -s tests` and the canonical command
`python -m unittest discover -s tests -v` cover the same test scope. No
duplicate rerun was performed to reconcile the variance.

---

## Hard constraints confirmed

```text
SECRET_VALUES_EXPOSED=false
IDENTITY_TOKENS_EXPOSED=false
PUBLIC_URL_CLAIMED=true
PUBLIC_URL=https://arthur9293.github.io/bosai-studio-control-plane/
PUBLIC_URL_READBACK=PASS_HUMAN_BROWSER_DESKTOP_AND_MOBILE
PUBLIC_URL_HTTP_READBACK=PASS
PUBLIC_URL_HTTP_STATUS=200
SUBMISSION_READY=false
IBM_BOB_USAGE_PROVEN=true
IBM_BOB_EVIDENCE_COMMITTED=true
IBM_BOB_EVIDENCE_COMMIT=4c4075fd0ba744c86cd8e1e649f0a9338351115d
IBM_BOB_EVIDENCE_COMMIT_SCOPE=LOCAL_GIT_COMMIT_PUSHED_TO_REMOTE_BRANCH
GITHUB_PUSHED=true
GITHUB_REMOTE_BRANCH=refs/heads/phase/12-ibm-partner-track-public-demo-url
GITHUB_REMOTE_HEAD=a9a4b3aa72ab92cf0b30047ffeeb89aad4b4cdd3
DEPLOYMENT_ATTEMPTED=true
DEPLOYMENT_KIND=GITHUB_PAGES_STATIC_DOCS_BRANCH_PUSH
NEW_AI_PROVIDER_ADDED=false
OPENAI_RUNTIME_DEPENDENCY=false
ANTHROPIC_RUNTIME_DEPENDENCY=false
NEW_AUTHORITY_PATH_ADDED=false
HUMAN_GO_GATE_BYPASSED=false
```

IBM Bob is a development-process partner only.
IBM Bob is NOT BOSAI runtime authority.

---

## Evidence commit state and remaining non-claims

- `IBM_BOB_USAGE_PROVEN=true` — evidence package exists as git commit
  `4c4075fd0ba744c86cd8e1e649f0a9338351115d`, pushed to remote branch.
- `IBM_BOB_EVIDENCE_COMMITTED=true` scoped to:
  `LOCAL_GIT_COMMIT_PUSHED_TO_REMOTE_BRANCH`
- `GITHUB_PUSHED=true` — branch pushed; remote HEAD:
  `a9a4b3aa72ab92cf0b30047ffeeb89aad4b4cdd3`
- Public demo URL is live and read back:
  `https://arthur9293.github.io/bosai-studio-control-plane/`
  `PUBLIC_URL_HTTP_READBACK=PASS` / `HTTP_STATUS=200`
- No final Devpost submission readiness has been claimed.
- `SUBMISSION_READY=false` — remaining blockers:
  `THREE_MINUTE_VIDEO=MISSING`
  `DEVPOST_COPY=MISSING`
  `FINAL_SUBMISSION_READBACK=MISSING`
