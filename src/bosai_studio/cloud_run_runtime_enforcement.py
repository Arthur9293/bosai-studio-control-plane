from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .cloud_run_boundary import (
    AUTHORITY_IDENTITY,
    DEFAULT_REGION,
    PIPELINE_IDENTITY,
    PROJECT_ID_ENV,
    REGION_ENV,
    ServiceName,
    STUDIO_IDENTITY,
)

HUMAN_GO_ENV = "BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO"
HUMAN_GO_VALUE = "HUMAN GO PHASE 9 DEPLOYMENT"
RUNTIME_IMAGE = "us-docker.pkg.dev/cloudrun/container/hello"


class RuntimeProofStatus(StrEnum):
    PREPARED_ONLY = "PREPARED_ONLY"
    DEPLOYED_NOT_PROVEN = "DEPLOYED_NOT_PROVEN"
    RUNTIME_ENFORCEMENT_PROVEN = "RUNTIME_ENFORCEMENT_PROVEN"


@dataclass(frozen=True)
class RuntimeCommand:
    name: str
    argv: tuple[str, ...]
    mutates_cloud: bool

    def as_list(self) -> list[str]:
        return list(self.argv)


@dataclass(frozen=True)
class RuntimeService:
    name: ServiceName
    service_account_id: str
    allow_unauthenticated: bool
    ingress: str

    def service_account_email(self, project_id: str) -> str:
        return f"{self.service_account_id}@{project_id}.iam.gserviceaccount.com"


RUNTIME_SERVICES: tuple[RuntimeService, ...] = (
    RuntimeService(
        name=ServiceName.STUDIO_CONTROL_PLANE,
        service_account_id=STUDIO_IDENTITY.account_id,
        allow_unauthenticated=True,
        ingress="all",
    ),
    RuntimeService(
        name=ServiceName.AUTHORITY_EXECUTOR,
        service_account_id=AUTHORITY_IDENTITY.account_id,
        allow_unauthenticated=False,
        ingress="all",
    ),
    RuntimeService(
        name=ServiceName.MEDIA_PIPELINE_SIM,
        service_account_id=PIPELINE_IDENTITY.account_id,
        allow_unauthenticated=False,
        ingress="all",
    ),
)


def require_human_go(value: str | None) -> None:
    if value != HUMAN_GO_VALUE:
        raise RuntimeError(
            f'{HUMAN_GO_ENV} must exactly equal "{HUMAN_GO_VALUE}" before Phase 9 deployment mutation.'
        )


def service_accounts(project_id: str) -> dict[str, str]:
    return {
        service.name.value: service.service_account_email(project_id)
        for service in RUNTIME_SERVICES
    }


def service_account_create_commands(project_id: str) -> tuple[RuntimeCommand, ...]:
    commands: list[RuntimeCommand] = []
    for service in RUNTIME_SERVICES:
        email = service.service_account_email(project_id)
        commands.append(
            RuntimeCommand(
                name=f"describe-sa-{service.name.value}",
                argv=(
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "describe",
                    email,
                    "--project",
                    project_id,
                ),
                mutates_cloud=False,
            )
        )
        commands.append(
            RuntimeCommand(
                name=f"create-sa-{service.name.value}",
                argv=(
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "create",
                    service.service_account_id,
                    "--project",
                    project_id,
                    "--display-name",
                    f"BOSAI Phase 9 {service.name.value}",
                ),
                mutates_cloud=True,
            )
        )
    return tuple(commands)


def cloud_run_deploy_commands(project_id: str, region: str) -> tuple[RuntimeCommand, ...]:
    commands: list[RuntimeCommand] = []
    for service in RUNTIME_SERVICES:
        unauth = "--allow-unauthenticated" if service.allow_unauthenticated else "--no-allow-unauthenticated"
        commands.append(
            RuntimeCommand(
                name=f"deploy-{service.name.value}",
                argv=(
                    "gcloud",
                    "run",
                    "deploy",
                    service.name.value,
                    "--image",
                    RUNTIME_IMAGE,
                    "--project",
                    project_id,
                    "--region",
                    region,
                    "--service-account",
                    service.service_account_email(project_id),
                    "--ingress",
                    service.ingress,
                    unauth,
                    "--quiet",
                ),
                mutates_cloud=True,
            )
        )
    return tuple(commands)


def iam_binding_commands(project_id: str, region: str) -> tuple[RuntimeCommand, ...]:
    return (
        RuntimeCommand(
            name="allow-studio-to-invoke-authority",
            argv=(
                "gcloud",
                "run",
                "services",
                "add-iam-policy-binding",
                ServiceName.AUTHORITY_EXECUTOR.value,
                "--project",
                project_id,
                "--region",
                region,
                "--member",
                f"serviceAccount:{STUDIO_IDENTITY.email(project_id)}",
                "--role",
                "roles/run.invoker",
                "--quiet",
            ),
            mutates_cloud=True,
        ),
        RuntimeCommand(
            name="allow-authority-to-invoke-pipeline",
            argv=(
                "gcloud",
                "run",
                "services",
                "add-iam-policy-binding",
                ServiceName.MEDIA_PIPELINE_SIM.value,
                "--project",
                project_id,
                "--region",
                region,
                "--member",
                f"serviceAccount:{AUTHORITY_IDENTITY.email(project_id)}",
                "--role",
                "roles/run.invoker",
                "--quiet",
            ),
            mutates_cloud=True,
        ),
    )


def deployment_commands(project_id: str, region: str = DEFAULT_REGION) -> tuple[RuntimeCommand, ...]:
    return (
        *service_account_create_commands(project_id),
        *cloud_run_deploy_commands(project_id, region),
        *iam_binding_commands(project_id, region),
    )


def runtime_enforcement_plan(project_id: str, region: str = DEFAULT_REGION) -> dict[str, object]:
    commands = deployment_commands(project_id, region)
    return {
        "phase": "PHASE_9_CLOUD_RUN_RUNTIME_ENFORCEMENT",
        "project_id": project_id,
        "region": region,
        "human_go_env": HUMAN_GO_ENV,
        "human_go_required_value": HUMAN_GO_VALUE,
        "runtime_image": RUNTIME_IMAGE,
        "status": RuntimeProofStatus.PREPARED_ONLY.value,
        "deployment_mutation_commands_prepared": sum(1 for c in commands if c.mutates_cloud),
        "read_only_commands_prepared": sum(1 for c in commands if not c.mutates_cloud),
        "service_accounts": service_accounts(project_id),
        "allowed_runtime_edges": [
            {
                "caller": ServiceName.STUDIO_CONTROL_PLANE.value,
                "target": ServiceName.AUTHORITY_EXECUTOR.value,
                "proof_method": "identity-token invocation with studio service account",
            },
            {
                "caller": ServiceName.AUTHORITY_EXECUTOR.value,
                "target": ServiceName.MEDIA_PIPELINE_SIM.value,
                "proof_method": "identity-token invocation with authority service account",
            },
        ],
        "denied_runtime_edges": [
            {
                "caller": ServiceName.STUDIO_CONTROL_PLANE.value,
                "target": ServiceName.MEDIA_PIPELINE_SIM.value,
                "proof_method": "identity-token invocation with studio service account must return non-2xx",
            },
            {
                "caller": ServiceName.PUBLIC_INTERNET.value,
                "target": ServiceName.AUTHORITY_EXECUTOR.value,
                "proof_method": "unauthenticated request must return non-2xx",
            },
            {
                "caller": ServiceName.PUBLIC_INTERNET.value,
                "target": ServiceName.MEDIA_PIPELINE_SIM.value,
                "proof_method": "unauthenticated request must return non-2xx",
            },
        ],
        "runtime_iam_enforcement_proven": False,
        "secrets_expected_in_output": False,
    }
