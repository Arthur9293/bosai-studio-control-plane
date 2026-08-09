from __future__ import annotations

import asyncio
import json
import sys
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
TARGET_EVENT = "TRANSCODE_A_CODEC_INIT_TIMEOUT"
TARGET_SERVICE = "bosai-studio-media-pipeline"


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


def _extract_json_payload(text: str) -> tuple[str, bool]:
    """Accept raw JSON or one markdown JSON fence; reject surrounding commentary."""
    stripped = text.strip()
    fenced = False
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise RuntimeError("Gemini returned an incomplete markdown code fence")
        opener = lines[0].strip().lower()
        if opener not in {"```", "```json"}:
            raise RuntimeError(f"Gemini returned unsupported code fence: {lines[0].strip()}")
        stripped = "\n".join(lines[1:-1]).strip()
        fenced = True

    if not (stripped.startswith("{") and stripped.endswith("}")):
        raise RuntimeError("Gemini final response is not a standalone JSON object")
    return stripped, fenced


def _tool_trajectory_diagnostic(
    tool_calls: list[dict[str, Any]], tool_responses: list[dict[str, Any]]
) -> dict[str, Any]:
    """Return a bounded, secret-free readback of the MCP trajectory for debugging."""
    summaries: list[dict[str, Any]] = []
    for item in tool_responses:
        response_text = json.dumps(item.get("response"), sort_keys=True, default=str)
        summaries.append(
            {
                "name": item.get("name"),
                "contains_target_event": TARGET_EVENT in response_text,
                "contains_target_service": TARGET_SERVICE in response_text,
                "response_chars": len(response_text),
                "response_preview": response_text[:1600],
            }
        )
    return {
        "tool_calls": tool_calls,
        "tool_response_summaries": summaries,
    }


def _assert_real_grafana_evidence(tool_responses: list[dict[str, Any]]) -> None:
    required = [item for item in tool_responses if item.get("name") == "query_loki_logs"]
    if not required:
        raise RuntimeError("No query_loki_logs tool response was observed")

    evidence_text = json.dumps(required, sort_keys=True, default=str)
    missing = [value for value in (TARGET_EVENT, TARGET_SERVICE) if value not in evidence_text]
    if missing:
        raise RuntimeError(
            "Grafana MCP response did not contain required BOSAI evidence: " + ", ".join(missing)
        )


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
                        "response": _jsonable(getattr(function_response, "response", None)),
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

    print(
        "PHASE5_TOOL_DIAGNOSTIC="
        + json.dumps(_tool_trajectory_diagnostic(tool_calls, tool_responses), sort_keys=True, default=str),
        file=sys.stderr,
    )

    _assert_real_grafana_evidence(tool_responses)

    if not final_text:
        raise RuntimeError("Gemini produced no final structured proposal")

    json_payload, markdown_fence_stripped = _extract_json_payload(final_text)
    envelope = AgentProposalEnvelope.model_validate_json(json_payload)
    domain_proposal = envelope.to_domain_proposal()

    return {
        "phase": "PHASE_5_GEMINI_AGENT_LOOP",
        "model": config.model,
        "vertex_ai": True,
        "grafana_mcp_required_tool_observed": True,
        "grafana_mcp_evidence_verified": True,
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
        "final_response_markdown_fence_stripped": markdown_fence_stripped,
        "authority_engine_invoked": False,
        "permit_issued": False,
        "mutation_attempted": False,
    }


def main() -> None:
    print(json.dumps(asyncio.run(run_phase5_smoke()), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
