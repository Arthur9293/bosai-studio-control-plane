from __future__ import annotations

from dataclasses import dataclass
from html import escape

PHASE_10_TITLE = "BOSAI Studio Control Plane"
LOCKED_THESIS = "Intelligence is not authority."
WORKFLOW = "OBSERVE → REASON → PROPOSE → AUTHORIZE → EXECUTE → VERIFY → PROVE"


@dataclass(frozen=True)
class ProofCard:
    label: str
    value: str
    status: str


@dataclass(frozen=True)
class DemoStep:
    name: str
    actor: str
    claim: str
    proof: str


PROOF_CARDS: tuple[ProofCard, ...] = (
    ProofCard("AI role", "Gemini proposes only", "proposal_only=true"),
    ProofCard("Authority", "BOSAI deterministic executor", "permit required"),
    ProofCard("Durability", "Firestore authority state", "Phase 7 PASS"),
    ProofCard("Runtime boundary", "Cloud Run / IAM enforced", "Phase 9 PASS"),
    ProofCard("Observability", "Grafana is operational truth", "MCP read-only"),
    ProofCard("Safety invariant", "Final release requires fresh QC", "QC bypass denied"),
    ProofCard(
        "IBM partner track",
        "IBM Bob — development process partner",
        "not runtime authority",
    ),
)


DEMO_STEPS: tuple[DemoStep, ...] = (
    DemoStep(
        "OBSERVE",
        "Grafana + telemetry",
        "Final trailer delivery SLA is at risk.",
        "Real Grafana Cloud Loki/telemetry path was proven in Phases 4–6.",
    ),
    DemoStep(
        "REASON",
        "Gemini / Google ADK",
        "Gemini reads evidence and proposes a restart.",
        "Proposal remains NOT_EVALUATED until BOSAI authority runs.",
    ),
    DemoStep(
        "PROPOSE",
        "Gemini proposal envelope",
        "Action proposed: RESTART_TRANSCODE_WORKER on transcode-a.",
        "No permit, mutation, or authority claim exists at proposal time.",
    ),
    DemoStep(
        "AUTHORIZE",
        "BOSAI authority executor",
        "BOSAI evaluates policy and issues a single-use permit for the safe path.",
        "QC bypass is denied by invariant: FINAL_RELEASE_INTENT_AND_NOT_FRESH_QC_PASS=>QC_VALIDATION_ENABLED.",
    ),
    DemoStep(
        "EXECUTE",
        "Authority-controlled execution path",
        "Mutation occurs only through the authority executor after permit consumption.",
        "Replay is denied and direct pipeline mutation is not a valid edge.",
    ),
    DemoStep(
        "VERIFY",
        "Verifier + Grafana evidence",
        "Postconditions are verified from evidence, not Gemini prose.",
        "Stale or missing evidence fails closed.",
    ),
    DemoStep(
        "PROVE",
        "Firestore audit + Cloud Run IAM",
        "Authority state is durable and runtime edges are enforced by Google Cloud IAM.",
        "studio-control-plane → authority-executor → media-pipeline-sim is allowed; studio-control-plane ↛ media-pipeline-sim is denied.",
    ),
)


def proof_summary() -> dict[str, object]:
    return {
        "title": PHASE_10_TITLE,
        "thesis": LOCKED_THESIS,
        "workflow": WORKFLOW,
        "cards": [card.__dict__ for card in PROOF_CARDS],
        "steps": [step.__dict__ for step in DEMO_STEPS],
        "unsupported_claims_absent": True,
        "secret_values_expected": False,
        "identity_tokens_expected": False,
        "customer_workload_claimed": False,
        "public_url_claimed": False,
    }


def render_demo_html() -> str:
    cards = "\n".join(
        f"""
        <article class=\"card\">
          <p class=\"eyebrow\">{escape(card.label)}</p>
          <h3>{escape(card.value)}</h3>
          <p class=\"status\">{escape(card.status)}</p>
        </article>
        """.strip()
        for card in PROOF_CARDS
    )
    steps = "\n".join(
        f"""
        <section class=\"step\">
          <div class=\"step-index\">{escape(step.name)}</div>
          <div>
            <p class=\"actor\">{escape(step.actor)}</p>
            <h3>{escape(step.claim)}</h3>
            <p>{escape(step.proof)}</p>
          </div>
        </section>
        """.strip()
        for step in DEMO_STEPS
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(PHASE_10_TITLE)} — Judge Demo</title>
  <style>
    :root {{ color-scheme: dark; --bg:#071018; --panel:#0d1b2a; --line:#24445f; --text:#eef6ff; --muted:#9eb4c7; --ok:#67e8a5; --warn:#facc15; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; background: radial-gradient(circle at top left, #16324a, var(--bg) 44%); color:var(--text); }}
    main {{ max-width:1120px; margin:0 auto; padding:56px 24px 80px; }}
    .hero {{ border:1px solid var(--line); background:rgba(13,27,42,.86); border-radius:28px; padding:40px; box-shadow:0 24px 80px rgba(0,0,0,.35); }}
    .kicker, .eyebrow, .actor {{ color:var(--muted); text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; font-weight:700; }}
    h1 {{ font-size: clamp(2.3rem, 6vw, 5.4rem); line-height:.95; margin:12px 0 18px; }}
    .thesis {{ font-size: clamp(1.25rem, 3vw, 2rem); color:var(--ok); margin:0 0 22px; }}
    .workflow {{ display:inline-flex; flex-wrap:wrap; gap:.6rem; border:1px solid var(--line); border-radius:999px; padding:12px 18px; color:#dbeafe; background:#081522; font-weight:800; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin:28px 0; }}
    .card {{ background:rgba(8,21,34,.92); border:1px solid var(--line); border-radius:18px; padding:18px; min-height:150px; }}
    .card h3 {{ margin:8px 0 18px; font-size:1.15rem; }}
    .status {{ color:var(--ok); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .steps {{ display:grid; gap:14px; margin-top:28px; }}
    .step {{ display:grid; grid-template-columns:160px 1fr; gap:20px; border:1px solid var(--line); border-radius:20px; padding:20px; background:rgba(13,27,42,.74); }}
    .step-index {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color:var(--warn); font-weight:900; }}
    .step h3 {{ margin:4px 0 8px; }}
    .step p {{ color:#cfe1f1; }}
    .footer {{ margin-top:28px; color:var(--muted); font-size:.94rem; }}
    @media (max-width:720px) {{ .hero {{ padding:26px; }} .step {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header class=\"hero\">
      <p class=\"kicker\">Agentic Cinema · BOSAI Studio Control Plane</p>
      <h1>Governed autonomous operations for final trailer delivery.</h1>
      <p class=\"thesis\">{escape(LOCKED_THESIS)}</p>
      <div class=\"workflow\">{escape(WORKFLOW)}</div>
    </header>

    <section class=\"grid\" aria-label=\"Proof summary\">
      {cards}
    </section>

    <section class=\"steps\" aria-label=\"BOSAI governed workflow\">
      {steps}
    </section>

    <p class=\"footer\">This demo surface summarizes locked proof semantics from Phases 3–9. It does not claim customer production workload, secret exposure, identity-token output, or public hosted URL until explicitly proven.</p>
  </main>
</body>
</html>
"""
