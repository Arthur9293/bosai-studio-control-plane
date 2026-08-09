from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from bosai_studio.agent_contracts import AgentProposalEnvelope
from bosai_studio.authority import AuthorityExecutor, INVARIANT_FRESH_QC, POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Decision, PermitState, Proposal
from bosai_studio.governed_loop import GovernedControlLoop
from bosai_studio.pipeline import MediaPipelineSim


NOW = datetime(2026, 8, 9, 18, 0, tzinfo=timezone.utc)
RESTART_EVIDENCE = (
    'service_name="bosai-studio-media-pipeline" '
    'TRANSCODE_A_RESTARTED_DEGRADED worker="transcode-a"'
)


def make_loop() -> GovernedControlLoop:
    grant = AuthorityGrant(
        grant_id="phase6-test-grant",
        allowed_actions=frozenset(Action),
        expires_at=NOW + timedelta(hours=1),
        policy_version=POLICY_VERSION,
    )
    return GovernedControlLoop(AuthorityExecutor(MediaPipelineSim(), grant=grant))


def restart_proposal(pid: str = "phase6-restart") -> Proposal:
    return Proposal(
        proposal_id=pid,
        incident_id="incident-demo-001",
        action=Action.RESTART_TRANSCODE_WORKER,
        target="transcode-a",
        reason="Grafana shows a codec initialization timeout.",
        evidence_refs=("grafana:loki:TRANSCODE_A_CODEC_INIT_TIMEOUT",),
        expected_postconditions=(
            "transcode-a restarts",
            "subsequent telemetry shows restart progress",
        ),
    )


class GovernedExecutionLoopTests(unittest.TestCase):
    def test_phase5_envelope_enters_authority_without_schema_relaxation(self) -> None:
        envelope = AgentProposalEnvelope.model_validate(
            {
                "proposal_id": "phase5-compatible",
                "incident_id": "incident-demo-001",
                "action": "RESTART_TRANSCODE_WORKER",
                "target": "transcode-a",
                "reason": "Real Grafana evidence shows the transcode timeout.",
                "evidence_refs": ["grafana:loki:TRANSCODE_A_CODEC_INIT_TIMEOUT"],
                "expected_postconditions": ["transcode-a restarts and emits recovery telemetry"],
                "authority_decision": "NOT_EVALUATED",
                "proposal_only": True,
            }
        )
        proposal = envelope.to_domain_proposal()
        loop = make_loop()

        decision = loop.submit(proposal, now=NOW)

        self.assertEqual(decision.decision, Decision.AUTHORIZED)
        self.assertIsNotNone(decision.permit_id)

    def test_authorized_restart_executes_once_and_verifies_from_state_and_evidence(self) -> None:
        loop = make_loop()
        proposal = restart_proposal()
        before = loop.authority.pipeline.snapshot()

        decision = loop.submit(proposal, now=NOW)
        receipt = loop.execute_authorized(proposal, decision, now=NOW)
        after = loop.authority.pipeline.snapshot()
        verification = loop.verify(proposal, receipt, before, after, RESTART_EVIDENCE)
        replay = loop.authority.execute(proposal, decision.permit_id or "", now=NOW)

        self.assertEqual(decision.decision, Decision.AUTHORIZED)
        self.assertEqual(receipt.decision, Decision.AUTHORIZED)
        self.assertTrue(verification.verified)
        self.assertEqual(verification.missing_evidence_tokens, ())
        self.assertEqual(replay.decision, Decision.DENIED_REPLAY)
        self.assertEqual(loop.authority.permit_state(decision.permit_id or ""), PermitState.EXECUTED)
        self.assertTrue(loop.authority.audit.verify())

        event_types = [event.event_type for event in loop.authority.audit.events]
        for required in (
            "OBSERVATION_CAPTURED",
            "PROPOSAL_CREATED",
            "AUTHORITY_GRANTED",
            "PERMIT_CONSUMED",
            "EXECUTION_STARTED",
            "EXECUTION_SUCCEEDED",
            "POSTCONDITION_VERIFIED",
            "EXECUTION_DENIED",
        ):
            self.assertIn(required, event_types)

    def test_verification_fails_closed_when_grafana_evidence_is_missing(self) -> None:
        loop = make_loop()
        proposal = restart_proposal("phase6-missing-evidence")
        before = loop.authority.pipeline.snapshot()
        decision = loop.submit(proposal, now=NOW)
        receipt = loop.execute_authorized(proposal, decision, now=NOW)
        after = loop.authority.pipeline.snapshot()

        verification = loop.verify(proposal, receipt, before, after, "")

        self.assertFalse(verification.verified)
        self.assertIn("TRANSCODE_A_RESTARTED_DEGRADED", verification.missing_evidence_tokens)
        self.assertIn("POSTCONDITION_FAILED", [event.event_type for event in loop.authority.audit.events])
        self.assertTrue(loop.authority.audit.verify())

    def test_qc_bypass_is_denied_by_trajectory_invariant_without_mutation_or_permit(self) -> None:
        loop = make_loop()
        before = loop.authority.pipeline.snapshot()
        proposal = Proposal(
            proposal_id="phase6-qc-bypass",
            incident_id=before.incident_id,
            action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
            target="quality-control",
            reason="Adversarial request to ship faster by disabling QC.",
            evidence_refs=("operator:ship-faster",),
            expected_postconditions=("delivery is faster",),
        )

        decision = loop.submit(proposal, now=NOW)
        after = loop.authority.pipeline.snapshot()

        self.assertEqual(decision.decision, Decision.DENIED)
        self.assertEqual(decision.reason_code, "GLOBAL_TRAJECTORY_INVARIANT_VIOLATION")
        self.assertEqual(decision.violated_invariant, INVARIANT_FRESH_QC)
        self.assertIsNone(decision.permit_id)
        self.assertEqual(after.state_version, before.state_version)
        self.assertTrue(after.qc_validation_enabled)
        self.assertTrue(loop.authority.audit.verify())

    def test_execute_authorized_fails_closed_when_decision_is_denied(self) -> None:
        loop = make_loop()
        before = loop.authority.pipeline.snapshot()
        proposal = Proposal(
            proposal_id="phase6-denied-execution",
            incident_id=before.incident_id,
            action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
            target="quality-control",
            reason="test",
            evidence_refs=("test",),
            expected_postconditions=("test",),
        )
        decision = loop.submit(proposal, now=NOW)

        receipt = loop.execute_authorized(proposal, decision, now=NOW)

        self.assertEqual(receipt.decision, Decision.DENIED)
        self.assertEqual(receipt.reason_code, "EXECUTION_BLOCKED_WITHOUT_AUTHORIZED_DECISION")
        self.assertEqual(loop.authority.pipeline.snapshot().state_version, before.state_version)


if __name__ == "__main__":
    unittest.main()
