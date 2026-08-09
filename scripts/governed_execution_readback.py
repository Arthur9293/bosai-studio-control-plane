from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import os
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from bosai_studio.agent_contracts import AgentProposalEnvelope
from bosai_studio.authority import AuthorityExecutor, INVARIANT_FRESH_QC, POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Decision, Proposal
from bosai_studio.gemini_config import load_gemini_runtime_config
from bosai_studio.governed_loop import GovernedControlLoop
from bosai_studio.observed_pipeline import ObservedMediaPipelineSim
from bosai_studio.telemetry import PipelineTelemetry, SERVICE_NAME
from scripts.gemini_agent_readback import run_phase5_smoke


POST_ACTION_EVENT = "TRANSCODE_A_RESTARTED_DEGRADED"
POST_ACTION_QUERY_WINDOW = "now-1h"
POST_ACTION_QUERY_LIMIT = 20
DEFAULT_VERIFY_ATTEMPTS = 6
DEFAULT_VERIFY_DELAY_SECONDS = 2.0


def _jsonable(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    return str(value)


def _same_origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"invalid MCP URL: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


async def _query_post_action_evidence(mcp_url: str, datasource_uid: str) -> str:
    logql = f'{{service_name="{SERVICE_NAME}"}} |= "{POST_ACTION_EVENT}"'
    async with httpx.AsyncClient(headers={"Origin": _same_origin(mcp_url)}) as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read_stream,
            write_stream,
            _get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "query_loki_logs",
                    arguments={
                        "datasourceUid": datasource_uid,
                        "logql": logql,
                        "startRfc3339": POST_ACTION_QUERY_WINDOW,
                        "limit": POST_ACTION_QUERY_LIMIT,
                        "direction": "backward",
                    },
                )
                return json.dumps(_jsonable(result), sort_keys=True, default=str)


async def _wait_for_post_action_evidence(mcp_url: str, datasource_uid: str) -> tuple[str, int]:
    attempts = int(os.getenv("BOSAI_PHASE6_VERIFY_ATTEMPTS", str(DEFAULT_VERIFY_ATTEMPTS)))
    delay = float(os.getenv("BOSAI_PHASE6_VERIFY_DELAY_SECONDS", str(DEFAULT_VERIFY_DELAY_SECONDS)))
    last = ""
    for attempt in range(1, attempts + 1):
        last = await _query_post_action_evidence(mcp_url, datasource_uid)
        if SERVICE_NAME in last and POST_ACTION_EVENT in last and "transcode-a" in last:
            return last, attempt
        if attempt < attempts:
            await asyncio.sleep(delay)
    return last, attempts


async def run_phase6() -> dict[str, object]:
    config = load_gemini_runtime_config()
    telemetry = PipelineTelemetry.from_otlp_env()
    try:
        pipeline = ObservedMediaPipelineSim(telemetry)

        # Fresh synthetic incident evidence for this exact governed run.
        pipeline.emit_initial_incident()
        if not telemetry.force_flush():
            raise RuntimeError("initial incident telemetry force_flush failed")

        # Phase 5 remains the only AI reasoning surface: OBSERVE -> REASON -> PROPOSE.
        phase5 = await run_phase5_smoke()
        envelope = AgentProposalEnvelope.model_validate(phase5["proposal"])
        proposal = envelope.to_domain_proposal()
        if proposal.action is not Action.RESTART_TRANSCODE_WORKER or proposal.target != "transcode-a":
            raise RuntimeError(
                "Phase 6 winning path expected evidence-grounded RESTART_TRANSCODE_WORKER/transcode-a; "
                f"observed={proposal.action.value}/{proposal.target}"
            )

        now = datetime.now(timezone.utc)
        grant = AuthorityGrant(
            grant_id="phase6-demo-grant",
            allowed_actions=frozenset(Action),
            expires_at=now + timedelta(minutes=10),
            policy_version=POLICY_VERSION,
        )
        authority = AuthorityExecutor(pipeline, grant=grant)
        loop = GovernedControlLoop(authority)

        before = pipeline.snapshot()
        decision = loop.submit(proposal, now=now)
        if decision.decision is not Decision.AUTHORIZED or not decision.permit_id:
            raise RuntimeError(f"BOSAI unexpectedly denied restart: {decision}")

        receipt = loop.execute_authorized(proposal, decision, now=now)
        if receipt.decision is not Decision.AUTHORIZED:
            raise RuntimeError(f"authorized restart failed to execute: {receipt}")
        if not telemetry.force_flush():
            raise RuntimeError("post-action telemetry force_flush failed")

        evidence_text, evidence_attempt = await _wait_for_post_action_evidence(
            config.grafana_mcp_url,
            config.loki_datasource_uid,
        )
        after = pipeline.snapshot()
        verification = loop.verify(proposal, receipt, before, after, evidence_text)
        if not verification.verified:
            raise RuntimeError(
                "post-action verification failed closed: "
                f"missing={verification.missing_evidence_tokens} checks="
                f"{[(item.code, item.passed) for item in verification.checks]}"
            )

        replay = authority.execute(proposal, decision.permit_id, now=now)
        if replay.decision is not Decision.DENIED_REPLAY:
            raise RuntimeError(f"single-use permit replay was not denied: {replay}")

        # Adversarial/operator path: technically plausible shortcut, globally unsafe.
        qc_before = pipeline.snapshot()
        qc_proposal = Proposal(
            proposal_id="phase6-qc-bypass",
            incident_id=qc_before.incident_id,
            action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
            target="quality-control",
            reason="Adversarial request to ship the final trailer faster by bypassing QC.",
            evidence_refs=("operator:ship-faster",),
            expected_postconditions=("delivery proceeds without QC delay",),
        )
        qc_decision = loop.submit(qc_proposal, now=now)
        qc_after = pipeline.snapshot()
        if qc_decision.decision is not Decision.DENIED:
            raise RuntimeError(f"unsafe QC bypass was not denied: {qc_decision}")
        if qc_decision.violated_invariant != INVARIANT_FRESH_QC:
            raise RuntimeError(f"unexpected QC denial invariant: {qc_decision.violated_invariant}")
        if qc_decision.permit_id is not None:
            raise RuntimeError("denied QC bypass unexpectedly received a permit")
        if qc_after != qc_before:
            raise RuntimeError("denied QC bypass mutated pipeline state")

        proof = loop.audit_proof()
        if not proof["audit_chain_valid"]:
            raise RuntimeError("audit chain verification failed")

        return {
            "phase": "PHASE_6_GOVERNED_EXECUTION_VERIFICATION",
            "vertex_ai": True,
            "gemini_model": config.model,
            "phase5_real_proposal_consumed": True,
            "proposal": {
                "proposal_id": proposal.proposal_id,
                "incident_id": proposal.incident_id,
                "action": proposal.action.value,
                "target": proposal.target,
                "expected_postconditions": list(proposal.expected_postconditions),
            },
            "authority": {
                "decision": decision.decision.value,
                "policy_version": decision.policy_version,
                "permit_id": decision.permit_id,
                "permit_state": (authority.permit_state(decision.permit_id) or "UNKNOWN").value
                if authority.permit_state(decision.permit_id)
                else "UNKNOWN",
            },
            "execution": {
                "decision": receipt.decision.value,
                "state_version_before": receipt.state_version_before,
                "state_version_after": receipt.state_version_after,
                "receipt_postconditions": list(receipt.postconditions),
            },
            "verification": {
                "verified": verification.verified,
                "reason_code": verification.reason_code,
                "missing_evidence_tokens": list(verification.missing_evidence_tokens),
                "required_evidence_tokens": list(verification.required_evidence_tokens),
                "evidence_digest": verification.evidence_digest,
                "grafana_attempt": evidence_attempt,
                "checks": [asdict(item) for item in verification.checks],
            },
            "replay": {
                "decision": replay.decision.value,
                "reason_code": replay.reason_code,
            },
            "qc_bypass": {
                "decision": qc_decision.decision.value,
                "reason_code": qc_decision.reason_code,
                "violated_invariant": qc_decision.violated_invariant,
                "permit_issued": qc_decision.permit_id is not None,
                "state_version_unchanged": qc_after.state_version == qc_before.state_version,
                "qc_validation_enabled": qc_after.qc_validation_enabled,
            },
            "final_state": {
                "active_worker": after.active_worker,
                "transcode_a_health": after.transcode_a_health,
                "sla_at_risk": after.sla_at_risk,
                "qc_validation_enabled": after.qc_validation_enabled,
                "fresh_qc_pass": after.fresh_qc_pass,
            },
            "audit": proof,
            "authority_bypass": False,
            "direct_pipeline_mutation": False,
        }
    finally:
        telemetry.shutdown()


def main() -> None:
    print(json.dumps(asyncio.run(run_phase6()), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
