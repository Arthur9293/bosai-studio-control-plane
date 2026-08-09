from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from bosai_studio.authority import INVARIANT_FRESH_QC, POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Decision, Proposal
from bosai_studio.durable_store import (
    DurablePermitState,
    InMemoryAuthorityStateStore,
)
from bosai_studio.persistent_authority import PersistentAuthorityExecutor
from bosai_studio.pipeline import MediaPipelineSim, PipelineState


NOW = datetime(2026, 8, 9, 19, 0, tzinfo=timezone.utc)


class CountingPipeline(MediaPipelineSim):
    def __init__(self, state: PipelineState | None = None) -> None:
        super().__init__(state)
        self.mutation_calls = 0

    def _execute_authorized(self, action: Action, target: str):
        self.mutation_calls += 1
        return super()._execute_authorized(action, target)


def make_grant() -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="phase7-test-grant",
        allowed_actions=frozenset(Action),
        expires_at=NOW + timedelta(hours=1),
        policy_version=POLICY_VERSION,
    )


def restart_proposal(pid: str = "phase7-restart") -> Proposal:
    return Proposal(
        proposal_id=pid,
        incident_id="incident-demo-001",
        action=Action.RESTART_TRANSCODE_WORKER,
        target="transcode-a",
        reason="Grafana evidence shows codec initialization timeout.",
        evidence_refs=("grafana:loki:TRANSCODE_A_CODEC_INIT_TIMEOUT",),
        expected_postconditions=("transcode-a emits restart telemetry",),
    )


def make_executor(
    store: InMemoryAuthorityStateStore,
    pipeline: CountingPipeline | None = None,
    *,
    permit_ttl: timedelta = timedelta(minutes=2),
) -> tuple[PersistentAuthorityExecutor, CountingPipeline]:
    target = pipeline or CountingPipeline()
    return (
        PersistentAuthorityExecutor(
            target,
            grant=make_grant(),
            store=store,
            permit_ttl=permit_ttl,
        ),
        target,
    )


class DurableAuthorityTests(unittest.TestCase):
    def test_authorized_permit_survives_fresh_executor_and_replay_is_denied(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-restart")
        executor1, pipeline = make_executor(store)
        proposal = restart_proposal()

        decision = executor1.evaluate(proposal, now=NOW)
        self.assertEqual(decision.decision, Decision.AUTHORIZED)
        self.assertIsNotNone(decision.permit_id)
        self.assertEqual(
            store.get_permit(decision.permit_id or "").status,
            DurablePermitState.ISSUED,
        )

        executor2, _ = make_executor(store, pipeline)
        receipt = executor2.execute(proposal, decision.permit_id or "", now=NOW)
        self.assertEqual(receipt.decision, Decision.AUTHORIZED)
        self.assertEqual(pipeline.mutation_calls, 1)
        self.assertEqual(
            store.get_permit(decision.permit_id or "").status,
            DurablePermitState.EXECUTED,
        )

        executor3, _ = make_executor(store, pipeline)
        replay = executor3.execute(proposal, decision.permit_id or "", now=NOW)
        self.assertEqual(replay.decision, Decision.DENIED_REPLAY)
        self.assertEqual(replay.reason_code, "PERMIT_ALREADY_CONSUMED")
        self.assertEqual(pipeline.mutation_calls, 1)
        self.assertTrue(store.verify_audit())

    def test_transaction_retry_simulation_never_retries_external_side_effect(self) -> None:
        store = InMemoryAuthorityStateStore(
            "phase7-retries",
            simulated_transaction_retries=3,
        )
        executor, pipeline = make_executor(store)
        proposal = restart_proposal("phase7-retries")
        decision = executor.evaluate(proposal, now=NOW)

        receipt = executor.execute(proposal, decision.permit_id or "", now=NOW)

        self.assertEqual(receipt.decision, Decision.AUTHORIZED)
        self.assertEqual(store.transaction_attempts, 4)
        self.assertEqual(pipeline.mutation_calls, 1)

    def test_durable_trajectory_drift_requires_reevaluation_without_mutation(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-drift")
        executor, pipeline = make_executor(store)
        proposal = restart_proposal("phase7-drift")
        decision = executor.evaluate(proposal, now=NOW)

        store.persist_incident(PipelineState(state_version=99))
        receipt = executor.execute(proposal, decision.permit_id or "", now=NOW)

        self.assertEqual(receipt.decision, Decision.REEVALUATION_REQUIRED)
        self.assertEqual(receipt.reason_code, "TRAJECTORY_STATE_CHANGED")
        self.assertEqual(pipeline.mutation_calls, 0)
        self.assertEqual(
            store.get_permit(decision.permit_id or "").status,
            DurablePermitState.INVALIDATED,
        )

    def test_expired_durable_permit_fails_closed_without_mutation(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-expired")
        executor, pipeline = make_executor(store, permit_ttl=timedelta(seconds=1))
        proposal = restart_proposal("phase7-expired")
        decision = executor.evaluate(proposal, now=NOW)

        receipt = executor.execute(
            proposal,
            decision.permit_id or "",
            now=NOW + timedelta(seconds=2),
        )

        self.assertEqual(receipt.decision, Decision.DENIED)
        self.assertEqual(receipt.reason_code, "PERMIT_EXPIRED")
        self.assertEqual(pipeline.mutation_calls, 0)
        self.assertEqual(
            store.get_permit(decision.permit_id or "").status,
            DurablePermitState.EXPIRED,
        )

    def test_consumed_pending_survives_crash_analogue_and_is_not_auto_retried(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-crash")
        executor1, pipeline = make_executor(store)
        proposal = restart_proposal("phase7-crash")
        decision = executor1.evaluate(proposal, now=NOW)

        consumed = store.consume_permit(proposal, decision.permit_id or "", now=NOW)
        self.assertEqual(consumed.decision, Decision.AUTHORIZED)
        self.assertEqual(consumed.permit_state, DurablePermitState.CONSUMED_PENDING)

        executor2, _ = make_executor(store, pipeline)
        retry = executor2.execute(proposal, decision.permit_id or "", now=NOW)
        self.assertEqual(retry.decision, Decision.DENIED_REPLAY)
        self.assertEqual(pipeline.mutation_calls, 0)

    def test_qc_bypass_denial_persists_no_permit_and_no_mutation(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-qc")
        executor, pipeline = make_executor(store)
        before = pipeline.snapshot()
        proposal = Proposal(
            proposal_id="phase7-qc-bypass",
            incident_id=before.incident_id,
            action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
            target="quality-control",
            reason="Ship faster by bypassing QC.",
            evidence_refs=("operator:ship-faster",),
            expected_postconditions=("delivery proceeds faster",),
        )

        decision = executor.evaluate(proposal, now=NOW)

        self.assertEqual(decision.decision, Decision.DENIED)
        self.assertEqual(decision.reason_code, "GLOBAL_TRAJECTORY_INVARIANT_VIOLATION")
        self.assertEqual(decision.violated_invariant, INVARIANT_FRESH_QC)
        self.assertIsNone(decision.permit_id)
        self.assertEqual(store.permit_count_for_proposal(proposal.proposal_id), 0)
        self.assertEqual(pipeline.snapshot(), before)
        self.assertEqual(pipeline.mutation_calls, 0)

    def test_durable_audit_chain_continues_across_executor_instances(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-audit")
        executor1, pipeline = make_executor(store)
        proposal = restart_proposal("phase7-audit-restart")
        decision = executor1.evaluate(proposal, now=NOW)
        executor1.execute(proposal, decision.permit_id or "", now=NOW)
        count_after_first_executor = len(store.list_audit_events())

        executor2, _ = make_executor(store, pipeline)
        qc = Proposal(
            proposal_id="phase7-audit-qc",
            incident_id=pipeline.snapshot().incident_id,
            action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
            target="quality-control",
            reason="test",
            evidence_refs=("test",),
            expected_postconditions=("test",),
        )
        executor2.evaluate(qc, now=NOW)

        events = store.list_audit_events()
        self.assertGreater(len(events), count_after_first_executor)
        self.assertEqual([event.sequence for event in events], list(range(1, len(events) + 1)))
        self.assertTrue(store.verify_audit())

    def test_missing_durable_permit_fails_closed(self) -> None:
        store = InMemoryAuthorityStateStore("phase7-missing")
        executor, pipeline = make_executor(store)
        proposal = restart_proposal("phase7-missing")

        receipt = executor.execute(proposal, "missing-permit", now=NOW)

        self.assertEqual(receipt.decision, Decision.DENIED)
        self.assertEqual(receipt.reason_code, "PERMIT_NOT_FOUND")
        self.assertEqual(pipeline.mutation_calls, 0)


if __name__ == "__main__":
    unittest.main()
