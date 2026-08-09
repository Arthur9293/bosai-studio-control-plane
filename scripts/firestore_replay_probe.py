from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import sys

from bosai_studio.authority import POLICY_VERSION
from bosai_studio.contracts import Action, AuthorityGrant, Proposal
from bosai_studio.durable_store import FirestoreAuthorityStateStore
from bosai_studio.persistent_authority import PersistentAuthorityExecutor
from bosai_studio.pipeline import MediaPipelineSim


class ReplayProbePipeline(MediaPipelineSim):
    def __init__(self) -> None:
        super().__init__()
        self.mutation_calls = 0

    def _execute_authorized(self, action: Action, target: str):
        self.mutation_calls += 1
        return super()._execute_authorized(action, target)


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: python -m scripts.firestore_replay_probe <namespace> <permit_id> <proposal_id>"
        )

    namespace, permit_id, proposal_id = sys.argv[1:]
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required")

    now = datetime.now(timezone.utc)
    grant = AuthorityGrant(
        grant_id="phase7-replay-probe-grant",
        allowed_actions=frozenset(Action),
        expires_at=now + timedelta(minutes=10),
        policy_version=POLICY_VERSION,
    )
    proposal = Proposal(
        proposal_id=proposal_id,
        incident_id="incident-demo-001",
        action=Action.RESTART_TRANSCODE_WORKER,
        target="transcode-a",
        reason="Fresh-process replay probe.",
        evidence_refs=("phase7:replay-probe",),
        expected_postconditions=("no replay side effect",),
    )

    store = FirestoreAuthorityStateStore(project=project, namespace=namespace)
    pipeline = ReplayProbePipeline()
    executor = PersistentAuthorityExecutor(
        pipeline,
        grant=grant,
        store=store,
    )

    receipt = executor.execute(proposal, permit_id, now=now)
    permit = store.get_permit(permit_id)
    print(
        json.dumps(
            {
                "fresh_process": True,
                "decision": receipt.decision.value,
                "reason_code": receipt.reason_code,
                "permit_state": permit.status.value if permit else None,
                "mutation_calls": pipeline.mutation_calls,
                "audit_chain_valid": store.verify_audit(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
