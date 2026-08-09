from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from bosai_studio.authority import AuthorityExecutor, INVARIANT_FRESH_QC, POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Decision, Proposal
from bosai_studio.pipeline import MediaPipelineSim, PipelineState


NOW = datetime(2026, 8, 9, 13, 30, tzinfo=timezone.utc)


def make_executor(state: PipelineState | None = None) -> AuthorityExecutor:
    grant = AuthorityGrant(
        grant_id="grant-test",
        allowed_actions=frozenset(Action),
        expires_at=NOW + timedelta(hours=1),
        policy_version=POLICY_VERSION,
    )
    return AuthorityExecutor(MediaPipelineSim(state), grant=grant)


def proposal(pid: str, action: Action, target: str) -> Proposal:
    return Proposal(pid, "incident-demo-001", action, target, "test proposal")


class VerticalSliceTests(unittest.TestCase):
    def test_restart_is_authorized_and_executes_once(self) -> None:
        executor = make_executor()
        p = proposal("p-restart", Action.RESTART_TRANSCODE_WORKER, "transcode-a")
        decision = executor.evaluate(p, now=NOW)
        self.assertEqual(decision.decision, Decision.AUTHORIZED)
        receipt = executor.execute(p, decision.permit_id or "", now=NOW)
        self.assertEqual(receipt.decision, Decision.AUTHORIZED)
        self.assertEqual(executor.pipeline.snapshot().transcode_a_health, "DEGRADED")
        self.assertTrue(executor.pipeline.snapshot().sla_at_risk)

    def test_qc_disable_is_locally_valid_but_denied_by_global_trajectory_invariant(self) -> None:
        executor = make_executor()
        p = proposal("p-qc", Action.DISABLE_QUALITY_CONTROL_VALIDATION, "quality-control")
        decision = executor.evaluate(p, now=NOW)
        self.assertEqual(decision.decision, Decision.DENIED)
        self.assertEqual(decision.reason_code, "GLOBAL_TRAJECTORY_INVARIANT_VIOLATION")
        self.assertEqual(decision.violated_invariant, INVARIANT_FRESH_QC)
        self.assertTrue(executor.pipeline.snapshot().qc_validation_enabled)

    def test_same_qc_disable_can_be_authorized_when_no_final_release_intent_exists(self) -> None:
        state = PipelineState(release_intent=False)
        executor = make_executor(state)
        p = proposal("p-qc-maintenance", Action.DISABLE_QUALITY_CONTROL_VALIDATION, "quality-control")
        decision = executor.evaluate(p, now=NOW)
        self.assertEqual(decision.decision, Decision.AUTHORIZED)

    def test_reroute_executes_then_same_permit_is_denied_as_replay(self) -> None:
        executor = make_executor()
        p = proposal("p-reroute", Action.REROUTE_TRANSCODE_WORKLOAD, "transcode-b")
        decision = executor.evaluate(p, now=NOW)
        first = executor.execute(p, decision.permit_id or "", now=NOW)
        second = executor.execute(p, decision.permit_id or "", now=NOW)
        self.assertEqual(first.decision, Decision.AUTHORIZED)
        self.assertEqual(second.decision, Decision.DENIED_REPLAY)
        self.assertEqual(executor.pipeline.snapshot().active_worker, "transcode-b")
        self.assertFalse(executor.pipeline.snapshot().sla_at_risk)
        self.assertFalse(executor.pipeline.snapshot().fresh_qc_pass)

    def test_state_change_after_authorization_requires_reevaluation(self) -> None:
        executor = make_executor()
        reroute = proposal("p-reroute-stale", Action.REROUTE_TRANSCODE_WORKLOAD, "transcode-b")
        decision = executor.evaluate(reroute, now=NOW)

        restart = proposal("p-restart-before-reroute", Action.RESTART_TRANSCODE_WORKER, "transcode-a")
        restart_decision = executor.evaluate(restart, now=NOW)
        executor.execute(restart, restart_decision.permit_id or "", now=NOW)

        stale = executor.execute(reroute, decision.permit_id or "", now=NOW)
        self.assertEqual(stale.decision, Decision.REEVALUATION_REQUIRED)
        self.assertEqual(stale.reason_code, "TRAJECTORY_STATE_CHANGED")

    def test_audit_chain_verifies_after_authorize_deny_execute_and_replay(self) -> None:
        executor = make_executor()
        restart = proposal("p1", Action.RESTART_TRANSCODE_WORKER, "transcode-a")
        d1 = executor.evaluate(restart, now=NOW)
        executor.execute(restart, d1.permit_id or "", now=NOW)
        qc = proposal("p2", Action.DISABLE_QUALITY_CONTROL_VALIDATION, "quality-control")
        executor.evaluate(qc, now=NOW)
        self.assertTrue(executor.audit.verify())
        self.assertGreaterEqual(len(executor.audit.events), 3)

    def test_execution_without_permit_fails_closed(self) -> None:
        executor = make_executor()
        p = proposal("p-no-permit", Action.RESTART_TRANSCODE_WORKER, "transcode-a")
        receipt = executor.execute(p, "missing-permit", now=NOW)
        self.assertEqual(receipt.decision, Decision.DENIED)
        self.assertEqual(receipt.reason_code, "PERMIT_NOT_FOUND")
        self.assertEqual(executor.pipeline.snapshot().state_version, 1)

    def test_audit_chain_detects_payload_tampering(self) -> None:
        executor = make_executor()
        p = proposal("p-audit", Action.RESTART_TRANSCODE_WORKER, "transcode-a")
        executor.evaluate(p, now=NOW)
        self.assertTrue(executor.audit.verify())
        executor.audit.events[0].payload["reason_code"] = "TAMPERED"
        self.assertFalse(executor.audit.verify())


if __name__ == "__main__":
    unittest.main()
