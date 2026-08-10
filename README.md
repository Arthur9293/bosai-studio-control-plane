# BOSAI Studio Control Plane

**Governed autonomous operations for AI-powered media production.**

> *Intelligence is not authority.*

BOSAI is a studio operations control plane that separates AI intelligence from
operational authority. The canonical architecture is:

```
Grafana observes
Gemini proposes
BOSAI authorizes
Firestore persists
Cloud Run/IAM enforces
Verifier proves
```

No AI model can issue a permit, execute a mutation, or bypass a Human GO gate
on its own.

---

## Governed Workflow

```
OBSERVE → REASON → PROPOSE → AUTHORIZE → EXECUTE → VERIFY → PROVE
```

| Step | Actor | What happens |
|---|---|---|
| OBSERVE | Grafana + OpenTelemetry | Telemetry is read from Grafana Cloud Loki. Final trailer delivery SLA at risk is surfaced. |
| REASON | Gemini / Google ADK | Gemini reads the observed evidence and reasons about a recovery action. |
| PROPOSE | Gemini proposal envelope | A proposal is emitted (e.g. `RESTART_TRANSCODE_WORKER`). No permit or mutation exists yet. |
| AUTHORIZE | BOSAI authority executor | BOSAI evaluates policy deterministically and issues a single-use permit — or denies. |
| EXECUTE | Authority-controlled path | Mutation occurs only through the authority executor after permit consumption. |
| VERIFY | Verifier + Grafana evidence | Postconditions are checked from evidence, not Gemini prose. Stale evidence fails closed. |
| PROVE | Verifier | The Verifier returns `POSTCONDITIONS_VERIFIED` only when authoritative state and run-bound telemetry evidence satisfy deterministic checks. Firestore separately persists durable authority and audit state. |

---

## Stack

| Component | Technology | Proved in |
|---|---|---|
| Observability | Grafana Cloud (Loki/telemetry) + official Grafana MCP | Phases 4–6 |
| AI reasoning | Gemini via Google ADK (proposal-only) | Phase 5 |
| Authority executor | BOSAI deterministic policy engine | Phase 3 |
| Durable authority state | Google Cloud Firestore | Phase 7 |
| Runtime boundary enforcement | Cloud Run + Google Cloud IAM | Phases 8–9 |
| Telemetry export | OpenTelemetry SDK + OTLP HTTP exporter | Phase 4 |
| Verification | BOSAI Verifier (postcondition evidence checks) | Phase 6 |

All listed technologies are directly evidenced in the phase registers under
`docs/registers/`.

---

## IBM Partner Track

Phase 12 locks IBM as the selected partner track for BOSAI's Devpost Agentic
Cinema submission.

**IBM Bob** (IBM's AI coding assistant) is used as a **development-process
partner** during Phase 12 of this project. IBM Bob has assisted with:

- repository inspection and gap analysis;
- Phase 12 gap identification against the compliance register;
- README narrative refinement.

**IBM Bob is not BOSAI runtime authority.** IBM Bob has no role in BOSAI's
authority topology, cannot issue permits, cannot execute mutations, and cannot
bypass Human GO gates. The distinction is explicit and intentional:

```
IBM Bob          = development process partner only
Gemini           = proposal-only runtime intelligence
BOSAI            = deterministic authority
Google Cloud IAM = runtime enforcement
```

The IBM Bob usage evidence record is maintained at
[`docs/devpost/IBM-BOB-USAGE-EVIDENCE.md`](docs/devpost/IBM-BOB-USAGE-EVIDENCE.md).

---

## Run the Local Judge Demo

Render the judge-facing demo surface locally:

```bash
python -m scripts.render_judge_demo
```

Output: `build/judge-demo/index.html`

Open the file in a browser to review the governed workflow narrative, proof
cards, and demo steps. The renderer does not contact any external service, does
not claim a public URL, and does not print secrets.

---

## Phase Register Trail

All phase decisions, proof readbacks, and closure states are recorded in:

```
docs/registers/
  phase-01/   Winning thesis lock
  phase-02/   Architecture v1 lock
  phase-03/   Minimal vertical slice readback
  phase-04/   Grafana MCP integration readiness
  phase-05/   Gemini agent loop readiness
  phase-06/   Governed execution and verification
  phase-07/   Firestore durable authority
  phase-08/   Cloud Run / IAM boundary readiness
  phase-09/   Cloud Run runtime enforcement proof
  phase-10/   Public judge-facing demo readiness
  phase-11/   Devpost compliance alignment
  phase-12/   IBM partner track lock and public demo URL
```

---

## License

MIT. See [`LICENSE`](LICENSE).
