from __future__ import annotations

PHASE9_HUMAN_GO = "HUMAN GO PHASE 9 DEPLOYMENT"
PHASE9_ROLLBACK_HUMAN_GO = "HUMAN GO PHASE 9 ROLLBACK"

DEFAULT_PHASE9_REGION = "europe-west1"
PHASE9_REGION_ENV = "BOSAI_PHASE9_REGION"
PROJECT_ID_ENV = "GOOGLE_CLOUD_PROJECT"
DEPLOYMENT_GO_ENV = "BOSAI_PHASE9_DEPLOYMENT_HUMAN_GO"
ROLLBACK_GO_ENV = "BOSAI_PHASE9_ROLLBACK_HUMAN_GO"

STUDIO_SERVICE = "studio-control-plane"
AUTHORITY_SERVICE = "authority-executor"
PIPELINE_SERVICE = "media-pipeline-sim"

STUDIO_SA = "sa-studio-control-plane"
AUTHORITY_SA = "sa-authority-executor"
PIPELINE_SA = "sa-media-pipeline-sim"

STUDIO_INGRESS = "all"
# Phase 9 proves IAM denial through Cloud Run service authentication, not ingress-level
# network denial. `run.app` invocation between services is required for the positive
# proof chain, while `--no-allow-unauthenticated` and explicit invoker bindings keep
# authority and pipeline non-public.
PRIVATE_SERVICE_INGRESS = "all"
RUNTIME_IMAGE_SOURCE = "."


def service_account_email(account_id: str, project_id: str) -> str:
    return f"{account_id}@{project_id}.iam.gserviceaccount.com"


def deployment_human_go_valid(value: str | None) -> bool:
    return value == PHASE9_HUMAN_GO


def rollback_human_go_valid(value: str | None) -> bool:
    return value == PHASE9_ROLLBACK_HUMAN_GO


def phase9_deployment_plan(project_id: str, region: str = DEFAULT_PHASE9_REGION) -> dict[str, object]:
    studio_email = service_account_email(STUDIO_SA, project_id)
    authority_email = service_account_email(AUTHORITY_SA, project_id)
    pipeline_email = service_account_email(PIPELINE_SA, project_id)
    return {
        "phase": "PHASE_9_CLOUD_RUN_RUNTIME_ENFORCEMENT",
        "project_id": project_id,
        "region": region,
        "deployment_authorized_by_required_phrase": False,
        "runtime_iam_enforcement_proven": False,
        "service_accounts": {
            STUDIO_SERVICE: studio_email,
            AUTHORITY_SERVICE: authority_email,
            PIPELINE_SERVICE: pipeline_email,
        },
        "services": [
            {
                "name": PIPELINE_SERVICE,
                "service_account": pipeline_email,
                "allow_unauthenticated": False,
                "ingress": PRIVATE_SERVICE_INGRESS,
                "private_by": "cloud-run-iam-no-allow-unauthenticated-and-explicit-invoker-binding",
            },
            {
                "name": AUTHORITY_SERVICE,
                "service_account": authority_email,
                "allow_unauthenticated": False,
                "ingress": PRIVATE_SERVICE_INGRESS,
                "private_by": "cloud-run-iam-no-allow-unauthenticated-and-explicit-invoker-binding",
            },
            {
                "name": STUDIO_SERVICE,
                "service_account": studio_email,
                "allow_unauthenticated": True,
                "ingress": STUDIO_INGRESS,
            },
        ],
        "allowed_invoker_bindings": [
            {
                "caller": studio_email,
                "target": AUTHORITY_SERVICE,
                "role": "roles/run.invoker",
            },
            {
                "caller": authority_email,
                "target": PIPELINE_SERVICE,
                "role": "roles/run.invoker",
            },
        ],
        "intentionally_absent_bindings": [
            {
                "caller": studio_email,
                "target": PIPELINE_SERVICE,
                "reason_code": "STUDIO_HAS_NO_DIRECT_PIPELINE_EDGE",
            },
            {
                "caller": "allUsers",
                "target": AUTHORITY_SERVICE,
                "reason_code": "AUTHORITY_EXECUTOR_IS_NOT_PUBLIC",
            },
            {
                "caller": "allUsers",
                "target": PIPELINE_SERVICE,
                "reason_code": "MEDIA_PIPELINE_IS_NOT_PUBLIC",
            },
        ],
    }
