# BOSAI Studio Control Plane — Phase 10 Public Judge-Facing Demo Readiness

Status: **PREPARED — LOCAL DEMO SURFACE NOT YET PROVEN**  
Issue: **#20 — PHASE 10 — Public Judge-Facing Control Plane Demo**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `fbfc4a30b29e46325f0176807a95fb4b03bcae4e`  
Working branch: `phase/10-public-judge-control-plane-demo`

---

## Phase objective

Phase 10 translates the proven BOSAI control-plane stack into a judge-facing demo surface.

It does not add new authority. It does not add new AI behavior. It does not claim a customer production workload.

Locked thesis:

```text
Intelligence is not authority.
```

Locked workflow:

```text
OBSERVE → REASON → PROPOSE → AUTHORIZE → EXECUTE → VERIFY → PROVE
```

---

## Proof basis

Phase 10 summarizes proof semantics already established by prior phases:

```text
Phase 3: deterministic authority core and vertical slice
Phase 4: real Grafana telemetry and official Grafana MCP readback
Phase 5: Gemini/Google ADK proposal-only loop through Grafana MCP
Phase 6: governed execution and verification loop
Phase 7: durable Firestore authority state
Phase 8: Cloud Run/IAM boundary readiness
Phase 9: real Cloud Run/IAM runtime enforcement proof
```

---

## Implemented

### `src/bosai_studio/judge_demo_surface.py`

Defines the static judge-facing narrative:

- locked BOSAI thesis;
- proof cards;
- workflow steps;
- no public URL claim;
- no customer workload claim;
- no secret/token expectation.

### `scripts/render_judge_demo.py`

Renders the demo HTML to:

```text
build/judge-demo/index.html
```

The script prints:

```text
PHASE_10_PUBLIC_URL_CLAIMED=false
PHASE_10_SECRET_VALUES_PRINTED=false
```

### `tests/test_judge_demo_surface.py`

Covers:

- thesis visibility;
- workflow visibility;
- authority proof claims;
- Cloud Run/IAM denial claim;
- no public URL claim;
- no customer workload claim;
- no secret/token markers.

---

## Current gate state

```text
PHASE_10_CODE_PREPARATION=PREPARED
PHASE_10_LOCAL_REGRESSION=PENDING
PHASE_10_LOCAL_DEMO_RENDER=PENDING
PHASE_10_PUBLIC_URL_CLAIMED=FALSE
PHASE_10_PUBLIC_DEPLOYMENT=PENDING_HUMAN_GO
PHASE_10=PARTIAL
```

---

## Non-scope

Phase 10 does not authorize:

- new AI provider;
- new model surface;
- new authority path;
- new Cloud Run/IAM topology;
- customer media workload;
- Grafana write tools;
- public URL claim without deployment proof;
- Devpost final submission;
- final video recording.

---

## Exit criteria

Phase 10 can close as **DEMO-SURFACE-READY PASS** when:

1. full local regression is green;
2. `python -m scripts.render_judge_demo` renders local HTML;
3. content includes the locked thesis and workflow;
4. content does not expose secrets or tokens;
5. content does not claim public hosted URL.

Phase 10 can close as **PUBLIC-DEMO PASS** only after explicit Human GO for deployment and public URL readback.
