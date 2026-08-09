from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys
from uuid import uuid4

from bosai_studio.authority import INVARIANT_FRESH_QC, POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Decision, Proposal
from bosai_studio.durable_store import (
    DurablePermitState,
    FirestoreAuthorityStateStore,
)
from bosai_studio.persistent_authority import PersistentAuthorityExecutor
from bosai_studio.pipeline import MediaPipelineSim, PipelineState


class CountingPipeline(MediaPipelineSim):
    def __init__(self, state: PipelineState | None = None) -> None:
        super().__init__(state)
        self.mutation_calls = 0

    def _execute_authorized(self, action: Action, target: str):
        self.mutation_calls += 1
        return super()._execute_authorized(action, target)


def make_grant(now: datetime, suffix: str) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id=f"phase7-{suffix}-grant",
        allowed_actions=frozenset(Action),
        expires_at=now + timedelta(minutes=10),
        policy_version=POLICY_VERSION,
    )


def restart_proposal(proposal_id: str) -> Proposal:
    return Proposal(
        proposal_id=proposal_id,
        incident_id="incident-demo-001",
        action=Action.RESTART_TRANSCODE_WORKER,
        target="transcode-a",
        reason="Evidence-grounded restart proposal for durable authority proof.",
        evidence_refs=("grafana:loki:TRANSCODE_A_CODEC_INIT_TIMEOUT",),
        expected_postconditions=("transcode-a restart is observable",),
    )


def main() -> None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required")

    run_id = f"phase7-{uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    # Winning path: authorize with client/executor #1, execute with fresh client/executor #2.
    namespace = run_id
    store1 = FirestoreAuthorityStateStore(project=project, namespace=namespace)
    pipeline = CountingPipeline()
    executor1 = PersistentAuthorityExecutor(
        pipeline,
        grant=make_grant(now, "main"),
        store=store1,
    )
    proposal = restart_proposal(f"{run_id}-restart")

    decision = executor1.evaluate(proposal, now=now)
    if decision.decision is not Decision.AUTHORIZED or not decision.permit_id:
        raise RuntimeError(f"durable restart authorization failed: {decision}")
    issued = store1.get_permit(decision.permit_id)
    if issued is None or issued.status is not DurablePermitState.ISSUED:
        raise RuntimeError(f"permit was not durably ISSUED: {issued}")

    store2 = FirestoreAuthorityStateStore(project=project, namespace=namespace)
    executor2 = PersistentAuthorityExecutor(
        pipeline,
        grant=make_grant(now, "main-fresh-client"),
        store=store2,
    )
    receipt = executor2.execute(proposal, decision.permit_id, now=now)
    if receipt.decision is not Decision.AUTHORIZED:
        raise RuntimeError(f"durable execution failed: {receipt}")
    executed = store2.get_permit(decision.permit_id)
    if executed is None or executed.status is not DurablePermitState.EXECUTED:
        raise RuntimeError(f"permit did not reach durable EXECUTED state: {executed}")
    if pipeline.mutation_calls != 1:
        raise RuntimeError(f"expected exactly one mutation, observed {pipeline.mutation_calls}")

    # True fresh-process replay probe. ADC is inherited; no credential value is passed explicitly.
    replay_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.firestore_replay_probe",
            namespace,
            decision.permit_id,
            proposal.proposal_id,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    replay_line = replay_process.stdout.strip().splitlines()[-1]
    replay = json.loads(replay_line)
    if replay["decision"] != Decision.DENIED_REPLAY.value:
        raise RuntimeError(f"fresh-process replay was not denied: {replay}")
    if replay["mutation_calls"] != 0:
        raise RuntimeError(f"fresh-process replay attempted mutation: {replay}")

    # Same durable namespace, fresh executor: unsafe QC bypass must create no permit and no mutation.
    store3 = FirestoreAuthorityStateStore(project=project, namespace=namespace)
    executor3 = PersistentAuthorityExecutor(
        pipeline,
        grant=make_grant(now, "qc"),
        store=store3,
    )
    qc_before = pipeline.snapshot()
    qc_proposal = Proposal(
        proposal_id=f"{run_id}-qc-bypass",
        incident_id=qc_before.incident_id,
        action=Action.DISABLE_QUALITY_CONTROL_VALIDATION,
        target="quality-control",
        reason="Adversarial request to bypass QC.",
        evidence_refs=("operator:ship-faster",),
        expected_postconditions=("delivery proceeds without QC delay",),
    )
    qc_decision = executor3.evaluate(qc_proposal, now=now)
    qc_after = pipeline.snapshot()
    if qc_decision.decision is not Decision.DENIED:
        raise RuntimeError(f"QC bypass was not denied: {qc_decision}")
    if qc_decision.violated_invariant != INVARIANT_FRESH_QC:
        raise RuntimeError(f"unexpected QC invariant: {qc_decision.violated_invariant}")
    if store3.permit_count_for_proposal(qc_proposal.proposal_id) != 0:
        raise RuntimeError("QC bypass persisted a permit")
    if qc_after != qc_before:
        raise RuntimeError("QC bypass mutated pipeline state")

    # Real Firestore trajectory-drift transaction proof in an isolated run namespace.
    drift_namespace = f"{run_id}-drift"
    drift_store = FirestoreAuthorityStateStore(project=project, namespace=drift_namespace)
    drift_pipeline = CountingPipeline()
    drift_executor = PersistentAuthorityExecutor(
        drift_pipeline,
        grant=make_grant(now, "drift"),
        store=drift_store,
    )
    drift_proposal = restart_proposal(f"{run_id}-drift-restart")
    drift_decision = drift_executor.evaluate(drift_proposal, now=now)
    if drift_decision.decision is not Decision.AUTHORIZED or not drift_decision.permit_id:
        raise RuntimeError(f"drift setup authorization failed: {drift_decision}")
    drift_store.persist_incident(PipelineState(state_version=99))
    drift_receipt = drift_executor.execute(
        drift_proposal,
        drift_decision.permit_id,
        now=now,
    )
    if drift_receipt.decision is not Decision.REEVALUATION_REQUIRED:
        raise RuntimeError(f"durable state drift did not require reevaluation: {drift_receipt}")
    if drift_pipeline.mutation_calls != 0:
        raise RuntimeError("state-drift path attempted mutation")

    # Real Firestore permit-expiry proof without waiting on wall-clock sleep.
    expired_namespace = f"{run_id}-expired"
    expired_store = FirestoreAuthorityStateStore(project=project, namespace=expired_namespace)
    expired_pipeline = CountingPipeline()
    expired_executor = PersistentAuthorityExecutor(
        expired_pipeline,
        grant=make_grant(now, "expired"),
        store=expired_store,
        permit_ttl=timedelta(seconds=1),
    )
    expired_proposal = restart_proposal(f"{run_id}-expired-restart")
    expired_decision = expired_executor.evaluate(expired_proposal, now=now)
    if expired_decision.decision is not Decision.AUTHORIZED or not expired_decision.permit_id:
        raise RuntimeError(f"expiry setup authorization failed: {expired_decision}")
    expired_receipt = expired_executor.execute(
        expired_proposal,
        expired_decision.permit_id,
        now=now + timedelta(seconds=2),
    )
    if expired_receipt.decision is not Decision.DENIED:
        raise RuntimeError(f"expired permit was not denied: {expired_receipt}")
    expired_permit = expired_store.get_permit(expired_decision.permit_id)
    if expired_permit is None or expired_permit.status is not DurablePermitState.EXPIRED:
        raise RuntimeError(f"expired permit did not persist EXPIRED: {expired_permit}")
    if expired_pipeline.mutation_calls != 0:
        raise RuntimeError("expired-permit path attempted mutation")

    final_store = FirestoreAuthorityStateStore(project=project, namespace=namespace)
    main_summary = final_store.summary()
    if not main_summary["audit_chain_valid"]:
        raise RuntimeError("durable audit chain failed verification")

    print(
        json.dumps(
            {
                "phase": "PHASE_7_FIRESTORE_DURABLE_AUTHORITY",
                "project": project,
                "run_id": run_id,
                "firestore_backend": True,
                "authorized_path": {
                    "decision": decision.decision.value,
                    "permit_id": decision.permit_id,
                    "issued_state": issued.status.value,
                    "terminal_state": executed.status.value,
                    "execution_decision": receipt.decision.value,
                    "state_version_before": receipt.state_version_before,
                    "state_version_after": receipt.state_version_after,
                    "mutation_calls": pipeline.mutation_calls,
                    "fresh_client_executor_used": True,
                },
                "fresh_process_replay": replay,
                "qc_bypass": {
                    "decision": qc_decision.decision.value,
                    "reason_code": qc_decision.reason_code,
                    "violated_invariant": qc_decision.violated_invariant,
                    "permit_count": final_store.permit_count_for_proposal(qc_proposal.proposal_id),
                    "state_unchanged": qc_after == qc_before,
                },
                "trajectory_drift": {
                    "decision": drift_receipt.decision.value,
                    "reason_code": drift_receipt.reason_code,
                    "mutation_calls": drift_pipeline.mutation_calls,
                    "permit_state": (
                        drift_store.get_permit(drift_decision.permit_id).status.value
                        if drift_store.get_permit(drift_decision.permit_id)
                        else None
                    ),
                },
                "expired_permit": {
                    "decision": expired_receipt.decision.value,
                    "reason_code": expired_receipt.reason_code,
                    "permit_state": expired_permit.status.value,
                    "mutation_calls": expired_pipeline.mutation_calls,
                },
                "durable_main_summary": main_summary,
                "audit_chain_valid_after_fresh_process": final_store.verify_audit(),
                "transaction_side_effect_boundary": "consume transaction commits before pipeline mutation",
                "secret_values_printed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
