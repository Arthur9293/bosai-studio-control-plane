# IBM Bob Phase 12 Runbook — BOSAI Devpost Evidence

Status: **READY FOR REAL IBM BOB EXECUTION / NOT YET PROVEN**

This runbook defines how to use IBM Bob as a real development-process partner for BOSAI without changing BOSAI runtime authority.

## Why this exists

The Devpost Agentic Cinema IBM track requires demonstrable IBM Bob usage. BOSAI must therefore produce real evidence that IBM Bob was used during development, not merely mention IBM in documentation.

## Required setup

1. Open the BOSAI repository in IBM Bob IDE.
2. Ensure the branch is:

```text
phase/12-ibm-partner-track-public-demo-url
```

3. Ensure Bob can read project rules from:

```text
.bob/rules/bosai_phase12_authority_guardrails.md
```

4. Do not provide secrets, cloud credentials, service account keys, bearer tokens, identity tokens, Grafana tokens, Google credentials, or Devpost credentials to Bob.

## Recommended Bob task

Use Bob for development-process work only:

```text
Review BOSAI Studio Control Plane for Devpost Agentic Cinema IBM track submission readiness. Focus on README/submission packaging, judge-facing demo clarity, and IBM Bob development-process evidence. Preserve BOSAI's authority model: Gemini proposes, BOSAI authorizes, Firestore persists, Cloud Run/IAM enforces. Do not add runtime authority, do not introduce non-Google AI runtime dependencies, and do not claim a public hosted URL unless one is actually deployed and read back. Produce a concise set of changes or recommendations and update docs/devpost/IBM-BOB-USAGE-EVIDENCE.md with what you did.
```

## Acceptable Bob outputs

Bob may:

- improve README or Devpost packaging language;
- produce a submission-readiness checklist;
- propose edits to the judge-facing narrative;
- generate a security/readback checklist;
- update `docs/devpost/IBM-BOB-USAGE-EVIDENCE.md`;
- create an internal monologue/evidence note if configured.

Bob must not:

- add OpenAI or Anthropic runtime dependencies;
- add a new runtime model provider;
- bypass Human GO gates;
- alter Cloud Run/IAM authority topology;
- claim a public URL before deployment proof;
- claim final Devpost submission readiness;
- expose secrets or tokens.

## Evidence required after Bob run

Capture:

```text
IBM_BOB_USED=true
BOB_MODE=<Plan|Code|Agent|other>
BOB_PROMPT=<exact prompt or redacted-safe prompt>
BOB_FILES_INSPECTED=<list>
BOB_FILES_CHANGED=<list>
BOB_CONTRIBUTION=<summary>
HUMAN_REVIEW=<what was accepted/rejected>
SECRET_VALUES_EXPOSED=false
PUBLIC_URL_CLAIMED=false unless actually deployed
SUBMISSION_READY=false until final submit gate
```

## Completion gate

Phase 12A can pass only after IBM Bob has actually been run and the evidence is committed.

Until then:

```text
IBM_BOB_USAGE_PROVEN=false
```
