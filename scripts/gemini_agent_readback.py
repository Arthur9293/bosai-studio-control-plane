from __future__ import annotations

import asyncio
import json
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bosai_studio.agent_contracts import AgentProposalEnvelope
from bosai_studio.gemini_agent import GRAFANA_TOOL_ALLOWLIST, build_gemini_investigator
from bosai_studio.gemini_config import load_gemini_runtime_config


APP_NAME = "bosai_studio_phase5"
USER_ID = "hackathon_operator"
SESSION_ID = "phase5_real_gemini_smoke"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    return str(value)


async def run_phase5_smoke() -> dict[str, Any]:
    config = load_gemini_runtime_config()
    agent = build_gemini_investigator(config)
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

    prompt = (
        "Investigate incident FINAL_TRAILER_DELIVERY_SLA_AT_RISK for incident-demo-001. "
        "Use Grafana evidence first. Return exactly one structured recovery proposal. "
        "Do not authorize or execute anything."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    tool_calls: list[dict[str, Any]] = []
    tool_responses: list[dict[str, Any]] = []
    final_text: str | None = None

    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        content = getattr(event, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            function_call = getattr(part, "function_call", None)
            if function_call is not None:
                tool_calls.append(
                    {
                        "name": getattr(function_call, "name", None),
                        "args": _jsonable(getattr(function_call, "args", None)),
                    }
                )
            function_response = getattr(part, "function_response", None)
            if function_response is not None:
                tool_responses.append(
                    {
                        "name": getattr(function_response, "name", None),
                        "response_observed": True,
                    }
                )

        is_final = getattr(event, "is_final_response", None)
        if callable(is_final) and is_final():
            texts = [getattr(part, "text", None) for part in parts]
            final_text = "".join(text for text in texts if text).strip()

    advertised_calls = [call["name"] for call in tool_calls]
    if "query_loki_logs" not in advertised_calls:
        raise RuntimeError(f"Gemini did not use required Grafana MCP tool; observed={advertised_calls}")
    if any(name not in GRAFANA_TOOL_ALLOWLIST for name in advertised_calls):
        raise RuntimeError(f"Gemini invoked a tool outside the Phase 5 allowlist: {advertised_calls}")
    if not final_text:
        raise RuntimeError("Gemini produced no final structured proposal")

    envelope = AgentProposalEnvelope.model_validate_json(final_text)
    domain_proposal = envelope.to_domain_proposal()

    return {
        "phase": "PHASE_5_GEMINI_AGENT_LOOP",
        "model": config.model,
        "vertex_ai": True,
        "grafana_mcp_required_tool_observed": True,
        "tool_calls": tool_calls,
        "tool_responses": tool_responses,
        "proposal": envelope.model_dump(mode="json"),
        "domain_proposal": {
            "proposal_id": domain_proposal.proposal_id,
            "incident_id": domain_proposal.incident_id,
            "action": str(domain_proposal.action),
            "target": domain_proposal.target,
            "reason": domain_proposal.reason,
            "evidence_refs": list(domain_proposal.evidence_refs),
            "expected_postconditions": list(domain_proposal.expected_postconditions),
        },
        "authority_engine_invoked": False,
        "permit_issued": False,
        "mutation_attempted": False,
    }


def main() -> None:
    print(json.dumps(asyncio.run(run_phase5_smoke()), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
