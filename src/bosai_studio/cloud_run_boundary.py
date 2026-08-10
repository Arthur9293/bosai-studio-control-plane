from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


PROJECT_ID_ENV = "GOOGLE_CLOUD_PROJECT"
REGION_ENV = "GOOGLE_CLOUD_LOCATION"
DEFAULT_REGION = "europe-west1"


class ServiceName(StrEnum):
    STUDIO_CONTROL_PLANE = "studio-control-plane"
    AUTHORITY_EXECUTOR = "authority-executor"
    MEDIA_PIPELINE_SIM = "media-pipeline-sim"
    MCP_GRAFANA = "mcp-grafana"
    GEMINI_ADK = "gemini-adk"
    PUBLIC_INTERNET = "public-internet"


@dataclass(frozen=True)
class ServiceIdentity:
    service: ServiceName
    account_id: str

    def email(self, project_id: str) -> str:
        return f"{self.account_id}@{project_id}.iam.gserviceaccount.com"


@dataclass(frozen=True)
class InvocationEdge:
    caller: ServiceName
    target: ServiceName
    allowed: bool
    reason_code: str


@dataclass(frozen=True)
class CloudRunServiceSpec:
    service: ServiceName
    service_account: ServiceIdentity
    ingress: str
    allow_unauthenticated: bool


STUDIO_IDENTITY = ServiceIdentity(ServiceName.STUDIO_CONTROL_PLANE, "sa-studio-control-plane")
AUTHORITY_IDENTITY = ServiceIdentity(ServiceName.AUTHORITY_EXECUTOR, "sa-authority-executor")
PIPELINE_IDENTITY = ServiceIdentity(ServiceName.MEDIA_PIPELINE_SIM, "sa-media-pipeline-sim")


CANONICAL_SERVICE_IDENTITIES: tuple[ServiceIdentity, ...] = (
    STUDIO_IDENTITY,
    AUTHORITY_IDENTITY,
    PIPELINE_IDENTITY,
)


CANONICAL_CLOUD_RUN_SERVICES: tuple[CloudRunServiceSpec, ...] = (
    CloudRunServiceSpec(
        service=ServiceName.STUDIO_CONTROL_PLANE,
        service_account=STUDIO_IDENTITY,
        ingress="all",
        allow_unauthenticated=True,
    ),
    CloudRunServiceSpec(
        service=ServiceName.AUTHORITY_EXECUTOR,
        service_account=AUTHORITY_IDENTITY,
        ingress="internal-and-cloud-load-balancing",
        allow_unauthenticated=False,
    ),
    CloudRunServiceSpec(
        service=ServiceName.MEDIA_PIPELINE_SIM,
        service_account=PIPELINE_IDENTITY,
        ingress="internal-and-cloud-load-balancing",
        allow_unauthenticated=False,
    ),
)


CANONICAL_INVOCATION_EDGES: tuple[InvocationEdge, ...] = (
    InvocationEdge(
        ServiceName.STUDIO_CONTROL_PLANE,
        ServiceName.AUTHORITY_EXECUTOR,
        True,
        "STUDIO_MAY_REQUEST_AUTHORITY_EVALUATION",
    ),
    InvocationEdge(
        ServiceName.AUTHORITY_EXECUTOR,
        ServiceName.MEDIA_PIPELINE_SIM,
        True,
        "AUTHORITY_MAY_EXECUTE_WITH_VALID_PERMIT",
    ),
    InvocationEdge(
        ServiceName.STUDIO_CONTROL_PLANE,
        ServiceName.MEDIA_PIPELINE_SIM,
        False,
        "STUDIO_HAS_NO_PIPELINE_MUTATION_EDGE",
    ),
    InvocationEdge(
        ServiceName.GEMINI_ADK,
        ServiceName.MEDIA_PIPELINE_SIM,
        False,
        "GEMINI_HAS_NO_PIPELINE_CREDENTIAL",
    ),
    InvocationEdge(
        ServiceName.MCP_GRAFANA,
        ServiceName.MEDIA_PIPELINE_SIM,
        False,
        "GRAFANA_MCP_IS_OBSERVATION_ONLY",
    ),
    InvocationEdge(
        ServiceName.PUBLIC_INTERNET,
        ServiceName.AUTHORITY_EXECUTOR,
        False,
        "AUTHORITY_EXECUTOR_IS_PRIVATE",
    ),
    InvocationEdge(
        ServiceName.PUBLIC_INTERNET,
        ServiceName.MEDIA_PIPELINE_SIM,
        False,
        "MEDIA_PIPELINE_IS_PRIVATE",
    ),
)


class CloudRunBoundaryContract:
    """Deterministic Phase 8 contract for Cloud Run IAM invocation edges.

    This contract is not a substitute for real GCP IAM proof. It is the local
    source of truth used to generate plans and tests before any cloud mutation.
    """

    def __init__(self, edges: tuple[InvocationEdge, ...] = CANONICAL_INVOCATION_EDGES) -> None:
        self._edges = {(edge.caller, edge.target): edge for edge in edges}

    def decide(self, caller: ServiceName, target: ServiceName) -> InvocationEdge:
        edge = self._edges.get((caller, target))
        if edge is not None:
            return edge
        return InvocationEdge(
            caller,
            target,
            False,
            "EDGE_NOT_DECLARED_FAIL_CLOSED",
        )

    def is_allowed(self, caller: ServiceName, target: ServiceName) -> bool:
        return self.decide(caller, target).allowed

    def denied_edges(self) -> tuple[InvocationEdge, ...]:
        return tuple(edge for edge in self._edges.values() if not edge.allowed)

    def allowed_edges(self) -> tuple[InvocationEdge, ...]:
        return tuple(edge for edge in self._edges.values() if edge.allowed)


def service_account_map(project_id: str) -> dict[str, str]:
    return {identity.service.value: identity.email(project_id) for identity in CANONICAL_SERVICE_IDENTITIES}


def cloud_run_plan(project_id: str, region: str = DEFAULT_REGION) -> dict[str, object]:
    return {
        "project_id": project_id,
        "region": region,
        "service_accounts": service_account_map(project_id),
        "services": [
            {
                "name": spec.service.value,
                "service_account": spec.service_account.email(project_id),
                "ingress": spec.ingress,
                "allow_unauthenticated": spec.allow_unauthenticated,
            }
            for spec in CANONICAL_CLOUD_RUN_SERVICES
        ],
        "allowed_invocations": [
            {
                "caller": edge.caller.value,
                "target": edge.target.value,
                "reason_code": edge.reason_code,
            }
            for edge in CloudRunBoundaryContract().allowed_edges()
        ],
        "denied_invocations": [
            {
                "caller": edge.caller.value,
                "target": edge.target.value,
                "reason_code": edge.reason_code,
            }
            for edge in CloudRunBoundaryContract().denied_edges()
        ],
        "deployment_authorized": False,
        "runtime_iam_enforcement_proven": False,
    }
