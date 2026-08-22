from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
import json

PHASE_10_TITLE = "BOSAI Studio Control Plane"
LOCKED_THESIS = "Intelligence is not authority."
WORKFLOW = "OBSERVE → REASON → PROPOSE → AUTHORIZE → EXECUTE → VERIFY → PROVE"
HOSTED_SURFACE_URL = "https://arthur9293.github.io/bosai-studio-control-plane/"
CONTEST_REPOSITORY_CREATED_AT = "2026-08-09T12:35:38Z"


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


@dataclass(frozen=True)
class ReplayScenario:
    scenario_id: str
    label: str
    request: str
    decision: str
    result: str
    proof: str


PROOF_CARDS: tuple[ProofCard, ...] = (
    ProofCard("Contest provenance", "Contest-built clean-room implementation", "repository created Aug 9, 2026"),
    ProofCard("AI role", "Gemini proposes only", "proposal_only=true"),
    ProofCard("Authority", "BOSAI deterministic executor", "single-use permit required"),
    ProofCard("Durability", "Firestore authority state", "real runtime proof"),
    ProofCard("Runtime boundary", "Cloud Run / IAM enforced", "positive + negative edges proven"),
    ProofCard("Operational evidence", "Grafana Cloud + official MCP", "read-only observation path"),
    ProofCard("Safety invariant", "Final release requires fresh QC", "QC bypass denied"),
    ProofCard("IBM partner track", "IBM Bob — development-process partner", "real usage evidenced"),
)


DEMO_STEPS: tuple[DemoStep, ...] = (
    DemoStep(
        "OBSERVE",
        "Grafana + telemetry",
        "Final trailer delivery SLA is at risk.",
        "Real Grafana Cloud Loki/telemetry path was proven during the contest build.",
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


REPLAY_SCENARIOS: tuple[ReplayScenario, ...] = (
    ReplayScenario(
        "governed-restart",
        "Run governed restart",
        "RESTART_TRANSCODE_WORKER(transcode-a)",
        "AUTHORIZED",
        "permit consumed → worker restarted → postcondition verified",
        "Contest runtime evidence proved the governed positive path.",
    ),
    ReplayScenario(
        "qc-bypass",
        "Try unsafe QC bypass",
        "DISABLE_QC_VALIDATION(final-release)",
        "DENIED",
        "no permit → no mutation",
        "Global trajectory invariant requires fresh QC before final release.",
    ),
    ReplayScenario(
        "permit-replay",
        "Try permit replay",
        "REUSE_CONSUMED_PERMIT",
        "DENIED",
        "single-use permit already consumed",
        "Replay denial is a deterministic BOSAI authority property.",
    ),
)


def proof_summary() -> dict[str, object]:
    return {
        "title": PHASE_10_TITLE,
        "thesis": LOCKED_THESIS,
        "workflow": WORKFLOW,
        "cards": [asdict(card) for card in PROOF_CARDS],
        "steps": [asdict(step) for step in DEMO_STEPS],
        "replay_scenarios": [asdict(scenario) for scenario in REPLAY_SCENARIOS],
        "interactive_replay": True,
        "live_cloud_mutation": False,
        "unsupported_claims_absent": True,
        "secret_values_expected": False,
        "identity_tokens_expected": False,
        "customer_workload_claimed": False,
        "public_url_claimed": True,
        "hosted_surface_url": HOSTED_SURFACE_URL,
        "contest_repository_created_at": CONTEST_REPOSITORY_CREATED_AT,
        "contest_clean_room_claimed": True,
    }


def render_demo_html() -> str:
    cards = "\n".join(
        f"""
        <article class="card">
          <p class="eyebrow">{escape(card.label)}</p>
          <h3>{escape(card.value)}</h3>
          <p class="status">{escape(card.status)}</p>
        </article>
        """.strip()
        for card in PROOF_CARDS
    )
    steps = "\n".join(
        f"""
        <section class="step">
          <div class="step-index">{escape(step.name)}</div>
          <div>
            <p class="actor">{escape(step.actor)}</p>
            <h3>{escape(step.claim)}</h3>
            <p>{escape(step.proof)}</p>
          </div>
        </section>
        """.strip()
        for step in DEMO_STEPS
    )
    scenario_buttons = "\n".join(
        f'<button type="button" class="scenario-button" data-scenario="{escape(s.scenario_id)}">{escape(s.label)}</button>'
        for s in REPLAY_SCENARIOS
    )
    replay_json = json.dumps([asdict(scenario) for scenario in REPLAY_SCENARIOS], separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="BOSAI Studio Control Plane — governed autonomous operations for AI-powered media production.">
  <title>{escape(PHASE_10_TITLE)} — Interactive Judge Demo</title>
  <style>
    :root {{ color-scheme: dark; --bg:#071018; --panel:#0d1b2a; --line:#24445f; --text:#eef6ff; --muted:#9eb4c7; --ok:#67e8a5; --warn:#facc15; --bad:#fda4af; --link:#93c5fd; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:radial-gradient(circle at top left,#16324a,var(--bg) 44%); color:var(--text); }}
    main {{ max-width:1120px; margin:0 auto; padding:56px 24px 80px; }}
    .hero,.replay {{ border:1px solid var(--line); background:rgba(13,27,42,.86); border-radius:28px; padding:40px; box-shadow:0 24px 80px rgba(0,0,0,.35); }}
    .kicker,.eyebrow,.actor {{ color:var(--muted); text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; font-weight:700; }}
    h1 {{ font-size:clamp(2.3rem,6vw,5.4rem); line-height:.95; margin:12px 0 18px; }}
    h2 {{ font-size:clamp(1.6rem,4vw,2.5rem); margin:0 0 12px; }}
    .thesis {{ font-size:clamp(1.25rem,3vw,2rem); color:var(--ok); margin:0 0 22px; }}
    .workflow {{ display:inline-flex; flex-wrap:wrap; gap:.6rem; border:1px solid var(--line); border-radius:999px; padding:12px 18px; color:#dbeafe; background:#081522; font-weight:800; }}
    .notice {{ margin:22px 0 0; color:#cfe1f1; line-height:1.6; }}
    .links {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }}
    .links a,.scenario-button {{ color:var(--text); text-decoration:none; border:1px solid var(--line); background:#0a1a29; border-radius:999px; padding:10px 14px; font-weight:700; }}
    .links a:hover,.scenario-button:hover,.scenario-button:focus {{ border-color:var(--link); outline:none; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin:28px 0; }}
    .card {{ background:rgba(8,21,34,.92); border:1px solid var(--line); border-radius:18px; padding:18px; min-height:150px; }}
    .card h3 {{ margin:8px 0 18px; font-size:1.15rem; }}
    .status {{ color:var(--ok); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
    .replay {{ margin:28px 0; }}
    .replay-actions {{ display:flex; flex-wrap:wrap; gap:10px; margin:20px 0; }}
    .scenario-button {{ cursor:pointer; font:inherit; }}
    .result {{ border:1px solid var(--line); border-radius:18px; padding:18px; min-height:170px; background:#081522; }}
    .result-grid {{ display:grid; grid-template-columns:160px 1fr; gap:10px 18px; }}
    .result-key {{ color:var(--muted); }}
    .decision-authorized {{ color:var(--ok); font-weight:900; }}
    .decision-denied {{ color:var(--bad); font-weight:900; }}
    .steps {{ display:grid; gap:14px; margin-top:28px; }}
    .step {{ display:grid; grid-template-columns:160px 1fr; gap:20px; border:1px solid var(--line); border-radius:20px; padding:20px; background:rgba(13,27,42,.74); }}
    .step-index {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--warn); font-weight:900; }}
    .step h3 {{ margin:4px 0 8px; }}
    .step p {{ color:#cfe1f1; }}
    .footer {{ margin-top:28px; color:var(--muted); font-size:.94rem; line-height:1.6; }}
    @media (max-width:720px) {{ .hero,.replay {{ padding:26px; }} .step,.result-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <p class="kicker">Agentic Cinema · IBM Partner Track · BOSAI Studio Control Plane</p>
      <h1>Governed autonomous operations for final trailer delivery.</h1>
      <p class="thesis">{escape(LOCKED_THESIS)}</p>
      <div class="workflow">{escape(WORKFLOW)}</div>
      <p class="notice"><strong>Contest-built clean-room implementation.</strong> Repository created August 9, 2026 during the contest period. IBM Bob was used in the development process; Gemini is proposal-only runtime intelligence.</p>
      <div class="links" aria-label="Judge links">
        <a href="https://devpost.com/software/bosai-studio-control-plane">Devpost submission</a>
        <a href="https://youtu.be/bNyq_NPUYco">3-minute demo</a>
        <a href="https://github.com/Arthur9293/bosai-studio-control-plane">Source + evidence</a>
        <a href="https://github.com/Arthur9293/bosai-studio-control-plane/blob/air/docs/devpost/JUDGE-EVIDENCE-MAP.md">Evidence map</a>
      </div>
    </header>

    <section class="grid" aria-label="Proof summary">
      {cards}
    </section>

    <section class="replay" aria-labelledby="replay-title">
      <p class="kicker">Judge-safe product interaction</p>
      <h2 id="replay-title">Recorded evidence replay</h2>
      <p class="notice">Choose an action to inspect the deterministic outcome already proven by the contest implementation. <strong>This surface does not call live cloud services, consume a real permit, or mutate a pipeline.</strong> Real Grafana, Gemini, Firestore and Cloud Run/IAM evidence is preserved in the repository.</p>
      <div class="replay-actions">
        {scenario_buttons}
      </div>
      <div class="result" id="scenario-result" aria-live="polite">
        <p class="status">Select a scenario to inspect its governed outcome.</p>
      </div>
    </section>

    <section class="steps" aria-label="BOSAI governed workflow">
      {steps}
    </section>

    <p class="footer">Competition boundary: synthetic media workflow only; no customer production workload; no secret or identity-token values are published. Hosted interaction is a deterministic evidence replay, not a simulated claim of live cloud execution.</p>
  </main>

  <script>
    const scenarios = {replay_json};
    const result = document.getElementById("scenario-result");
    function showScenario(id) {{
      const scenario = scenarios.find((item) => item.scenario_id === id);
      if (!scenario) return;
      const decisionClass = scenario.decision === "AUTHORIZED" ? "decision-authorized" : "decision-denied";
      result.innerHTML = `
        <div class="result-grid">
          <div class="result-key">Request</div><div><code>${{scenario.request}}</code></div>
          <div class="result-key">Decision</div><div class="${{decisionClass}}">${{scenario.decision}}</div>
          <div class="result-key">Outcome</div><div>${{scenario.result}}</div>
          <div class="result-key">Evidence meaning</div><div>${{scenario.proof}}</div>
        </div>`;
    }}
    document.querySelectorAll("[data-scenario]").forEach((button) => {{
      button.addEventListener("click", () => showScenario(button.dataset.scenario));
    }});
  </script>
</body>
</html>
"""
