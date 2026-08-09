from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .contracts import Action, Decision, ExecutionReceipt, Proposal
from .pipeline import PipelineState
from .telemetry import SERVICE_NAME


@dataclass(frozen=True)
class VerificationCheck:
    code: str
    passed: bool
    expected: str
    observed: str


@dataclass(frozen=True)
class VerificationResult:
    proposal_id: str
    action: Action
    target: str
    verified: bool
    reason_code: str
    checks: tuple[VerificationCheck, ...]
    required_evidence_tokens: tuple[str, ...]
    missing_evidence_tokens: tuple[str, ...]
    proposal_expected_postconditions: tuple[str, ...]
    evidence_binding_token: str | None
    evidence_digest: str


def _check(code: str, passed: bool, *, expected: str, observed: object) -> VerificationCheck:
    return VerificationCheck(
        code=code,
        passed=passed,
        expected=expected,
        observed=str(observed),
    )


def verify_authorized_execution(
    proposal: Proposal,
    receipt: ExecutionReceipt,
    before: PipelineState,
    after: PipelineState,
    evidence_text: str,
    *,
    evidence_binding_token: str | None = None,
) -> VerificationResult:
    """Verify a governed side effect from authoritative state plus read-only telemetry evidence.

    Gemini prose is preserved as an expectation, but it is not treated as proof. The
    action-specific verification contract below is deterministic and fails closed when
    required state or telemetry evidence is absent. A supplied binding token (Phase 6
    uses a unique run_id) prevents stale historical telemetry from satisfying the gate.
    """

    checks: list[VerificationCheck] = [
        _check(
            "execution_authorized",
            receipt.decision is Decision.AUTHORIZED,
            expected=Decision.AUTHORIZED.value,
            observed=receipt.decision.value,
        ),
        _check(
            "permit_present",
            bool(receipt.permit_id),
            expected="non-empty single-use permit id",
            observed=receipt.permit_id or "NONE",
        ),
        _check(
            "state_version_advanced",
            after.state_version > before.state_version,
            expected=f"> {before.state_version}",
            observed=after.state_version,
        ),
        _check(
            "proposal_postconditions_present",
            bool(proposal.expected_postconditions)
            and all(item.strip() for item in proposal.expected_postconditions),
            expected="at least one non-blank expected postcondition",
            observed=len(proposal.expected_postconditions),
        ),
    ]

    required_tokens: tuple[str, ...]

    if proposal.action is Action.RESTART_TRANSCODE_WORKER:
        checks.extend(
            [
                _check(
                    "restart_target_is_transcode_a",
                    proposal.target == "transcode-a",
                    expected="transcode-a",
                    observed=proposal.target,
                ),
                _check(
                    "transcode_a_restart_state_observed",
                    after.transcode_a_health in {"DEGRADED", "HEALTHY"},
                    expected="DEGRADED or HEALTHY after restart",
                    observed=after.transcode_a_health,
                ),
            ]
        )
        required_tokens = (
            SERVICE_NAME,
            "TRANSCODE_A_RESTARTED_DEGRADED",
            "transcode-a",
        )

    elif proposal.action is Action.REROUTE_TRANSCODE_WORKLOAD:
        checks.extend(
            [
                _check(
                    "reroute_target_is_transcode_b",
                    proposal.target == "transcode-b",
                    expected="transcode-b",
                    observed=proposal.target,
                ),
                _check(
                    "active_worker_is_transcode_b",
                    after.active_worker == "transcode-b",
                    expected="transcode-b",
                    observed=after.active_worker,
                ),
                _check(
                    "sla_risk_cleared",
                    not after.sla_at_risk,
                    expected="false",
                    observed=after.sla_at_risk,
                ),
            ]
        )
        required_tokens = (
            SERVICE_NAME,
            "WORKLOAD_REROUTED_TO_HEALTHY_CAPACITY",
            "transcode-b",
        )

    elif proposal.action is Action.DISABLE_QUALITY_CONTROL_VALIDATION:
        checks.append(
            _check(
                "qc_validation_disabled",
                not after.qc_validation_enabled,
                expected="false",
                observed=after.qc_validation_enabled,
            )
        )
        required_tokens = (SERVICE_NAME, "QC_VALIDATION_DISABLED")

    else:  # defensive; Action is already a closed enum.
        checks.append(
            _check(
                "known_action",
                False,
                expected="known action verification contract",
                observed=proposal.action,
            )
        )
        required_tokens = ()

    if evidence_binding_token:
        required_tokens = (*required_tokens, evidence_binding_token)

    missing = tuple(token for token in required_tokens if token not in evidence_text)
    verified = all(item.passed for item in checks) and not missing
    digest = sha256(evidence_text.encode("utf-8")).hexdigest()

    return VerificationResult(
        proposal_id=proposal.proposal_id,
        action=proposal.action,
        target=proposal.target,
        verified=verified,
        reason_code="POSTCONDITIONS_VERIFIED" if verified else "POSTCONDITION_VERIFICATION_FAILED",
        checks=tuple(checks),
        required_evidence_tokens=required_tokens,
        missing_evidence_tokens=missing,
        proposal_expected_postconditions=proposal.expected_postconditions,
        evidence_binding_token=evidence_binding_token,
        evidence_digest=digest,
    )
