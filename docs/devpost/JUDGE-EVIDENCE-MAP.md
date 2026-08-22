# Agentic Cinema — Judge Evidence Map

Status: **R1-D HARDENING**
Project: **BOSAI Studio Control Plane**
Track: **IBM**
Canonical source branch before R1-D: `air`
R1-D base SHA: `5978a0b0ade8a73ccf28fbc78ec15a6fe6257167`

This file is a judge-facing index. It does not replace the underlying evidence.

## Fast screening map

| Screening question | Direct answer | Primary evidence |
|---|---|---|
| Was this project created during the contest period? | **Yes.** Repository created 2026-08-09; initial commit contains only MIT license + two-line description. | Git history + `docs/registers/r1-d/ELIGIBILITY-JUDGE-EXPERIENCE-HARDENING.md` |
| Is it a new implementation rather than imported BOSAI code? | **Yes, clean-room implementation.** Broader BOSAI governance ideas predate the contest; this media implementation, code, tests, runtime topology and evidence trail were created here during the contest. | README contest-provenance section + chronological registers |
| Does it use permitted Google AI tooling? | **Yes.** Google ADK + Gemini in Vertex AI mode. | `pyproject.toml`, `src/bosai_studio/gemini_agent.py`, `src/bosai_studio/gemini_config.py` |
| Does the model have mutation authority? | **No.** Gemini is proposal-only and sees only read-only Grafana MCP tools. | `src/bosai_studio/gemini_agent.py` |
| Is the IBM track requirement demonstrated? | **Yes.** IBM Bob was used in Plan + Agent modes with human-reviewed edits and committed evidence. | `docs/devpost/IBM-BOB-USAGE-EVIDENCE.md` |
| Is partner/runtime use more than README decoration? | **Yes.** Real Grafana Cloud ingestion and official `mcp-grafana` query readback were proven; Google Cloud Firestore and Cloud Run/IAM proof are recorded. | Phase 4, 7 and 9 registers |
| Is there a hosted project? | **Yes.** Public GitHub Pages judge surface. | `docs/index.html` |
| Can a judge interact without credentials? | **Yes.** Credential-free deterministic replay exposes positive and denied paths. | `docs/index.html`, `src/bosai_studio/judge_demo_surface.py` |
| Does the hosted replay pretend to be live cloud execution? | **No.** It explicitly states that it performs no live cloud call, permit consumption or mutation. | `docs/index.html` |
| Is the repository public and OSI licensed? | **Yes.** Public GitHub repository + MIT license. | repository metadata + `LICENSE` |
| Is there a public demo video? | **Yes.** | https://youtu.be/bNyq_NPUYco |

## Runtime evidence chain

### Google / Gemini

- `src/bosai_studio/gemini_agent.py`
  - imports `google.adk.agents.LlmAgent`;
  - uses `McpToolset`;
  - tool allowlist contains `query_loki_logs`;
  - mutation tool set is empty.
- `src/bosai_studio/gemini_config.py`
  - fails closed unless `GOOGLE_GENAI_USE_VERTEXAI=true`;
  - requires Google Cloud project + location.
- `pyproject.toml`
  - Google ADK, Google auth and Firestore runtime dependencies;
  - no OpenAI or Anthropic runtime dependency.

### IBM

- `docs/devpost/IBM-BOB-USAGE-EVIDENCE.md`
  - `IBM_BOB_USED=true`;
  - Plan + Agent modes;
  - human-reviewed implementation contributions;
  - regression evidence.

### Grafana

- `docs/registers/phase-04/GRAFANA-MCP-RUNTIME-READBACK.md`
  - real Grafana Cloud telemetry;
  - official `grafana/mcp-grafana:1.0.0`;
  - `--disable-write`;
  - real `query_loki_logs` returning BOSAI telemetry;
  - Viewer least-privilege service account.

### Durable authority + cloud enforcement

- `docs/registers/phase-07/FIRESTORE-DURABLE-AUTHORITY-READINESS.md`
- `docs/registers/phase-09/CLOUD-RUN-RUNTIME-ENFORCEMENT-READINESS.md`

Proven execution boundary:

```text
studio-control-plane → authority-executor → media-pipeline-sim
studio-control-plane ↛ media-pipeline-sim
```

## Judge-safe interactive surface

The hosted browser experience offers three deterministic evidence replays:

```text
1. RESTART_TRANSCODE_WORKER → AUTHORIZED → execute → verify
2. DISABLE_QC_VALIDATION    → DENIED     → no permit / no mutation
3. REUSE_CONSUMED_PERMIT    → DENIED     → replay blocked
```

The replay exists to make the product's authority semantics directly testable without exposing cloud credentials or a live mutation endpoint.

It must never be described as a fresh live Google Cloud execution. The real external runtime claims are grounded separately in the evidence registers above.

## Stage-Two judging alignment

| Criterion | BOSAI evidence |
|---|---|
| Technological Implementation | Real Gemini/ADK, Grafana MCP, Firestore, Cloud Run/IAM plus deterministic authority controls. |
| Design | Hosted interactive control-room replay with positive and denied paths, evidence links and clear trust-boundary labeling. |
| Potential Impact | Prevents intelligent agents from silently turning recommendations into unauthorized production actions. |
| Quality of the Idea | Separates intelligence from authority and verifies postconditions instead of trusting model prose. |

## Non-claims

- no customer production workload;
- no live public mutation endpoint;
- no public secret or identity token;
- no claim that IBM Bob is runtime authority;
- no claim that the hosted replay itself is fresh external runtime proof.
