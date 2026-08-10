# BOSAI Phase 12 — IBM Bob Authority Guardrails

These project-level IBM Bob rules apply to Phase 12 work for BOSAI Studio Control Plane.

## Contest target

We are preparing BOSAI for the Devpost Agentic Cinema IBM partner track.

BOSAI's product thesis is:

```text
Intelligence is not authority.
```

BOSAI is a governed media/studio operations control plane where:

```text
Grafana observes
Gemini proposes
BOSAI authorizes
Firestore persists
Cloud Run/IAM enforces
Verifier proves
```

## Hard constraints

When assisting on this repository, do not introduce:

- OpenAI runtime dependency;
- Anthropic runtime dependency;
- non-Google AI model in the runtime path;
- new BOSAI authority path;
- bypass of Human GO gates;
- customer/production media workload claims;
- secrets, bearer tokens, API keys, identity tokens, or credential values;
- public hosted URL claim unless a real hosted URL has been deployed and read back.

## IBM Bob role

IBM Bob may assist the development process by improving documentation, packaging, demo narrative, submission readiness, and code quality.

IBM Bob must not be represented as BOSAI runtime authority.

IBM Bob must not be given secrets or cloud credentials.

IBM Bob output must preserve the distinction between:

```text
IBM Bob = development process partner
Gemini = proposal-only runtime intelligence
BOSAI = deterministic authority
Google Cloud IAM = runtime enforcement
```

## Required evidence behavior

If Bob changes files or proposes changes, summarize:

- the prompt used;
- files inspected;
- files changed or suggested;
- what Bob contributed;
- what was human-reviewed;
- what was rejected;
- confirmation that no secrets/tokens were exposed.

Write that evidence into `docs/devpost/IBM-BOB-USAGE-EVIDENCE.md` or a follow-up evidence note.
