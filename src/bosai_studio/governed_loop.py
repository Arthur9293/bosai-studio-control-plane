from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from hashlib import sha256

from .authority import AuthorityExecutor
from .contracts import AuthorityDecision, Decision, ExecutionReceipt, Proposal
from .pipeline import PipelineState
from .verification import VerificationResult, verify_authorized_execution


class GovernedControlLoop:
    """Deterministic coordinator around the existing BOSAI authority boundary.

    This class does not expose a model tool and never mutates the pipeline directly.
    Every side effect still flows through AuthorityExecutor and a valid permit.
    """

    def __init__(self, authority: AuthorityExecutor) -> None:
        self.authority = authority

    @staticmethod
    def _evidence_digest(proposal: Proposal) -> str:
        material = "\n".join(proposal.evidence_refs).encode("utf-8")
        return sha256(material).hexdigest()

    def submit(self, proposal: Proposal, *, now: datetime | None = None) -> AuthorityDecision:
        self.authority.audit.append(
            "OBSERVATION_CAPTURED",
            {
                "proposal_id": proposal.proposal_id,
                "incident_id": proposal.incident_id,
                "evidence_ref_count": len(proposal.evidence_refs),
                "evidence_digest": self._evidence_digest(proposal),
            },
        )
        self.authority.audit.append(
            "PROPOSAL_CREATED",
            {
                "proposal_id": proposal.proposal_id,
                "incident_id": proposal.incident_id,
                "action": proposal.action.value,
                "target": proposal.target,
                "expected_postcondition_count": len(proposal.expected_postconditions),
            },
        )
        return self.authority.evaluate(proposal, now=now)

    def execute_authorized(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        *,
        now: datetime | None = None,
    ) -> ExecutionReceipt:
        if decision.decision is not Decision.AUTHORIZED or not decision.permit_id:
            state_version = self.authority.pipeline.snapshot().state_version
            receipt = ExecutionReceipt(
                decision=Decision.DENIED,
                proposal_id=proposal.proposal_id,
                permit_id=decision.permit_id,
                reason_code="EXECUTION_BLOCKED_WITHOUT_AUTHORIZED_DECISION",
                state_version_before=state_version,
                state_version_after=state_version,
            )
            self.authority.audit.append("EXECUTION_DENIED", receipt.__dict__)
            return receipt
        return self.authority.execute(proposal, decision.permit_id, now=now)

    def verify(
        self,
        proposal: Proposal,
        receipt: ExecutionReceipt,
        before: PipelineState,
        after: PipelineState,
        evidence_text: str,
    ) -> VerificationResult:
        result = verify_authorized_execution(proposal, receipt, before, after, evidence_text)
        event_type = "POSTCONDITION_VERIFIED" if result.verified else "POSTCONDITION_FAILED"
        self.authority.audit.append(
            event_type,
            {
                "proposal_id": result.proposal_id,
                "action": result.action.value,
                "target": result.target,
                "reason_code": result.reason_code,
                "evidence_digest": result.evidence_digest,
                "missing_evidence_tokens": list(result.missing_evidence_tokens),
                "checks": [asdict(item) for item in result.checks],
            },
        )
        return result

    def audit_proof(self) -> dict[str, object]:
        events = self.authority.audit.events
        return {
            "audit_chain_valid": self.authority.audit.verify(),
            "audit_event_count": len(events),
            "audit_event_types": [event.event_type for event in events],
            "audit_chain_head": events[-1].event_hash if events else "GENESIS",
        }
