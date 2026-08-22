# BOSAI Studio Control Plane

**Governed autonomous operations for AI-powered media production.**

> **Intelligence is not authority.**

BOSAI Studio Control Plane is a contest-built, clean-room implementation for the Google Cloud **Agentic Cinema: The Blockbuster Hackathon**. It demonstrates a governed media-operations workflow in which Gemini can observe evidence and propose an action, while BOSAI alone evaluates policy, issues a bounded single-use permit, controls execution, verifies postconditions, and records proof.

## Judge links

- **Hosted project / interactive judge surface:** https://arthur9293.github.io/bosai-studio-control-plane/
- **Devpost submission:** https://devpost.com/software/bosai-studio-control-plane
- **Demo video:** https://youtu.be/bNyq_NPUYco
- **Source repository:** https://github.com/Arthur9293/bosai-studio-control-plane
- **Selected partner track:** IBM
- **License:** MIT — see [`LICENSE`](LICENSE)
- **Judge evidence map:** [`docs/devpost/JUDGE-EVIDENCE-MAP.md`](docs/devpost/JUDGE-EVIDENCE-MAP.md)

## Contest provenance and clean-room boundary

The Agentic Cinema contest period began on **July 27, 2026**. This repository was created on **August 9, 2026** and its initial commit contained only the MIT license and a two-line repository description.

This submission is a **new contest implementation**, not a copy or extension of a pre-existing BOSAI codebase:

- no source file from another BOSAI repository was imported here;
- no pre-existing BOSAI deployment or production service is required by this project;
- no customer workload or customer dataset is reused;
- the media workflow, runtime topology, tests, evidence registers, and judge surface were implemented inside this repository during the contest period;
- the broader BOSAI governance thesis predates the contest, but this **Studio Control Plane implementation does not**.

The chronological commit and register trail under `docs/registers/` is retained so judges can verify the build sequence from thesis → architecture → executable vertical slice → real partner/runtime evidence → hosted judge experience.

IBM Bob was used as a **development-process partner** for the IBM track. It is not part of BOSAI runtime authority and cannot issue permits, execute mutations, or bypass the deterministic control path. Evidence is recorded in [`docs/devpost/IBM-BOB-USAGE-EVIDENCE.md`](docs/devpost/IBM-BOB-USAGE-EVIDENCE.md).

## Architecture

```text
Grafana observes
Gemini proposes
BOSAI authorizes
Firestore persists
Cloud Run/IAM enforces
Verifier proves
```

The governed workflow is:

```text
OBSERVE → REASON → PROPOSE → AUTHORIZE → EXECUTE → VERIFY → PROVE
```

| Step | Actor | What happens |
|---|---|---|
| OBSERVE | Grafana + OpenTelemetry | Runtime evidence exposes a final-trailer delivery incident. |
| REASON | Gemini / Google ADK | Gemini reasons over read-only Grafana evidence. |
| PROPOSE | Gemini proposal envelope | One bounded proposal is emitted with `proposal_only=true`. |
| AUTHORIZE | BOSAI deterministic authority | Policy and trajectory invariants are evaluated; authorization is not delegated to the model. |
| EXECUTE | Authority-controlled path | Mutation is allowed only after a valid single-use permit is consumed. |
| VERIFY | BOSAI Verifier + evidence | Postconditions are checked against authoritative state and run-bound telemetry. |
| PROVE | Firestore audit + runtime evidence | Durable authority state and verification evidence provide an auditable proof trail. |

## Hosted judge experience

The public judge surface is deliberately **safe to inspect without credentials**. It provides an interactive replay of three already-proven control outcomes:

1. governed restart → authorized, executed, verified;
2. unsafe QC bypass → denied by invariant;
3. consumed-permit replay → denied.

The browser replay is **not a fake live backend** and it does not call private Google Cloud or Grafana services. It is labeled as a deterministic evidence replay and links the judge to the source files and historical runtime readbacks that prove the real external integrations.

This separation lets judges test the product semantics without exposing secrets or mutation authority while preserving a clear distinction between:

```text
INTERACTIVE JUDGE REPLAY = deterministic, credential-free product surface
REAL RUNTIME PROOF       = contest-period Grafana + Gemini + Firestore + Cloud Run/IAM evidence
```

## Google Cloud / Gemini implementation

The project uses Google Cloud AI and runtime components directly in code:

- `google-adk[mcp]` for the Gemini agent;
- Vertex AI mode enforced by `GOOGLE_GENAI_USE_VERTEXAI=true`;
- Gemini `gemini-2.5-flash` as proposal-only intelligence;
- Google Cloud Firestore for durable authority and audit state;
- Cloud Run + IAM for runtime service boundaries;
- Google authentication libraries for service-to-service identity.

The Gemini implementation is in [`src/bosai_studio/gemini_agent.py`](src/bosai_studio/gemini_agent.py) and [`src/bosai_studio/gemini_config.py`](src/bosai_studio/gemini_config.py). The agent is allowlisted to the read-only Grafana MCP tool `query_loki_logs`; no mutation tools are exposed to it.

## IBM partner-track evidence

IBM Bob was used in Plan + Agent modes during Phase 12 for bounded repository inspection, compliance-gap analysis, README refinement, and human-reviewed judge-surface improvements.

```text
IBM Bob          = development-process partner
Gemini           = proposal-only runtime intelligence
BOSAI            = deterministic authority
Google Cloud IAM = runtime enforcement
```

See:

- [`docs/devpost/IBM-BOB-USAGE-EVIDENCE.md`](docs/devpost/IBM-BOB-USAGE-EVIDENCE.md)
- [`docs/devpost/IBM-BOB-RUNBOOK.md`](docs/devpost/IBM-BOB-RUNBOOK.md)
- [`docs/devpost/JUDGE-EVIDENCE-MAP.md`](docs/devpost/JUDGE-EVIDENCE-MAP.md)

## Judge quick start

Requirements: Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
python -m scripts.render_judge_demo
```

The rendered judge surface is written to:

```text
build/judge-demo/index.html
```

The repository includes environment templates only; secret values are not committed:

- `ops/google.env.example`
- `ops/grafana.env.example`

Live Vertex AI / Grafana / Firestore / Cloud Run proof requires the corresponding authorized cloud credentials and resources. The historical registers preserve the exact runtime readbacks used during the contest build.

## Runtime proof highlights

The contest build progressively proved:

- deterministic BOSAI authority and single-use permits;
- replay denial and state-drift re-evaluation;
- real Grafana Cloud telemetry and official read-only Grafana MCP use;
- real Gemini / Google ADK proposal generation grounded in Grafana evidence;
- governed execution with postcondition verification;
- durable Firestore authority state;
- real Cloud Run + IAM positive and negative invocation-edge proof;
- IBM Bob development-process usage;
- public GitHub Pages judge surface;
- public YouTube demo and submitted Devpost project.

The key Cloud Run boundary proven in Phase 9 is:

```text
studio-control-plane → authority-executor → media-pipeline-sim
studio-control-plane ↛ media-pipeline-sim
```

## Security and competition boundary

- synthetic media workflow and synthetic operational state only;
- no customer production workload;
- no model-issued permit or model-controlled execution;
- no OpenAI or Anthropic runtime dependency;
- no committed credential, token, private key, or identity token;
- `.gitignore` excludes `.env`, `.env.*`, `*.pem`, `*.key`, and `*.token`;
- example environment files use placeholders / `REDACTED` values;
- Grafana MCP is read-only for the Gemini observation path;
- IBM Bob is development tooling, not runtime authority;
- hosted interactive replay performs no cloud mutation and requires no secret.

## Evidence trail

The chronological proof records are under `docs/registers/`:

```text
phase-01  Winning thesis lock
phase-02  Architecture V1 lock
phase-03  Minimal governed vertical slice
phase-04  Grafana Cloud + official MCP runtime
phase-05  Gemini / Google ADK reasoning loop
phase-06  Governed execution and verification
phase-07  Firestore durable authority
phase-08  Cloud Run / IAM boundary readiness
phase-09  Cloud Run runtime enforcement proof
phase-10  Judge-facing demo surface
phase-11  Devpost compliance alignment
phase-12  IBM track, public demo, and final Devpost/GitHub compliance closeout
r1-d      Eligibility + judge-experience hardening
```

For the original final submission state, use [`docs/registers/phase-12/FINAL-DEVPOST-GITHUB-JUDGE-COMPLIANCE.md`](docs/registers/phase-12/FINAL-DEVPOST-GITHUB-JUDGE-COMPLIANCE.md). For the post-submission hardening workstream, use [`docs/registers/r1-d/ELIGIBILITY-JUDGE-EXPERIENCE-HARDENING.md`](docs/registers/r1-d/ELIGIBILITY-JUDGE-EXPERIENCE-HARDENING.md).

## License

MIT. See [`LICENSE`](LICENSE).
