from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .contracts import Action, Proposal


AuthorityState = Literal["NOT_EVALUATED"]


class AgentProposalEnvelope(BaseModel):
    """Structured output produced by Gemini before BOSAI authority evaluation.

    This object is intentionally incapable of carrying an AUTHORIZED/DENIED state.
    Authority is evaluated later by the deterministic BOSAI authority engine.
    """

    model_config = ConfigDict(extra="forbid")

    proposal_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    action: Action
    target: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    expected_postconditions: list[str] = Field(default_factory=list)
    authority_decision: AuthorityState = "NOT_EVALUATED"
    proposal_only: Literal[True] = True

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_must_be_nonempty_strings(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("evidence_refs must contain non-empty strings")
        return value

    def to_domain_proposal(self) -> Proposal:
        """Convert model output to the existing BOSAI Proposal contract only.

        No authority decision is produced and no execution method is called here.
        """
        return Proposal(
            proposal_id=self.proposal_id,
            incident_id=self.incident_id,
            action=self.action,
            target=self.target,
            reason=self.reason,
            evidence_refs=tuple(self.evidence_refs),
            expected_postconditions=tuple(self.expected_postconditions),
        )
