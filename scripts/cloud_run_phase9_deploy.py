from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

from bosai_studio.cloud_run_phase9 import (
    AUTHORITY_SA,
    AUTHORITY_SERVICE,
    DEFAULT_PHASE9_REGION,
    DEPLOYMENT_GO_ENV,
    PHASE9_REGION_ENV,
    PIPELINE_SA,
    PIPELINE_SERVICE,
    PRIVATE_SERVICE_INGRESS,
    PROJECT_ID_ENV,
    STUDIO_INGRESS,
    STUDIO_SA,
    STUDIO_SERVICE,
    deployment_human_go_valid,
    phase9_deployment_plan,
    service_account_email,
)


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def run_visible(cmd: list[str], *, check: bool = True) -> dict[str, Any]:
    completed = run(cmd, check=check)
    return {
        "command": cmd[:3],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip()[-2000:],
        "stderr": completed.stderr.strip()[-2000:],
    }


def service_account_exists(project: str, email: str) -> bool:
    completed = subprocess.run(
        ["gcloud", "iam", "service-accounts", "describe", email, "--project", project],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def ensure_service_account(project: str, account_id: str, display_name: str) -> dict[str, Any]:
    email = service_account_email(account_id, project)
    if service_account_exists(project, email):
        return {"email": email, "created": False}
    result = run_visible(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            account_id,
            "--project",
            project,
            "--display-name",
            display_name,
        ]
    )
    return {"email": email, "created": True, "result": result}


def service_url(project: str, region: str, service: str) -> str:
    completed = run(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            service,
            "--project",
            project,
            "--region",
            region,
            "--format=value(status.url)",
        ]
    )
    url = completed.stdout.strip()
    if not url:
        raise RuntimeError(f"missing Cloud Run URL for {service}")
    return url


def deploy_service(
    *,
    project: str,
    region: str,
    name: str,
    service_account: str,
    allow_unauthenticated: bool,
    ingress: str,
    env_vars: dict[str, str],
) -> dict[str, Any]:
    auth_flag = "--allow-unauthenticated" if allow_unauthenticated else "--no-allow-unauthenticated"
    env_arg = ",".join(f"{key}={value}" for key, value in env_vars.items())
    command = [
        "gcloud",
        "run",
        "deploy",
        name,
        "--source",
        ".",
        "--project",
        project,
        "--region",
        region,
        "--service-account",
        service_account,
        "--ingress",
        ingress,
        auth_flag,
        "--set-env-vars",
        env_arg,
        "--quiet",
    ]
    result = run_visible(command)
    return {"service": name, "result": result, "url": service_url(project, region, name)}


def add_invoker(project: str, region: str, target_service: str, caller_service_account: str) -> dict[str, Any]:
    return run_visible(
        [
            "gcloud",
            "run",
            "services",
            "add-iam-policy-binding",
            target_service,
            "--project",
            project,
            "--region",
            region,
            "--member",
            f"serviceAccount:{caller_service_account}",
            "--role",
            "roles/run.invoker",
            "--quiet",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy the isolated Phase 9 Cloud Run IAM proof topology.")
    parser.add_argument("--apply", action="store_true", help="Actually mutate Google Cloud resources.")
    args = parser.parse_args()

    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(PHASE9_REGION_ENV, DEFAULT_PHASE9_REGION)
    go_value = os.getenv(DEPLOYMENT_GO_ENV)

    plan = phase9_deployment_plan(project, region)
    if not args.apply:
        print(json.dumps({"dry_run": True, "plan": plan}, indent=2, sort_keys=True))
        return

    if not deployment_human_go_valid(go_value):
        raise RuntimeError(f"{DEPLOYMENT_GO_ENV} must equal HUMAN GO PHASE 9 DEPLOYMENT")

    studio_email = service_account_email(STUDIO_SA, project)
    authority_email = service_account_email(AUTHORITY_SA, project)
    pipeline_email = service_account_email(PIPELINE_SA, project)

    proof: dict[str, Any] = {
        "phase": "PHASE_9_DEPLOYMENT",
        "project_id": project,
        "region": region,
        "human_go_verified": True,
        "secret_values_printed": False,
        "service_accounts": [],
        "deployments": [],
        "iam_bindings": [],
    }

    proof["service_accounts"].append(ensure_service_account(project, PIPELINE_SA, "BOSAI Phase 9 media pipeline sim"))
    proof["service_accounts"].append(ensure_service_account(project, AUTHORITY_SA, "BOSAI Phase 9 authority executor"))
    proof["service_accounts"].append(ensure_service_account(project, STUDIO_SA, "BOSAI Phase 9 studio control plane"))

    pipeline = deploy_service(
        project=project,
        region=region,
        name=PIPELINE_SERVICE,
        service_account=pipeline_email,
        allow_unauthenticated=False,
        ingress=PRIVATE_SERVICE_INGRESS,
        env_vars={"BOSAI_SERVICE_NAME": PIPELINE_SERVICE},
    )
    proof["deployments"].append(pipeline)
    pipeline_url = pipeline["url"]

    authority = deploy_service(
        project=project,
        region=region,
        name=AUTHORITY_SERVICE,
        service_account=authority_email,
        allow_unauthenticated=False,
        ingress=PRIVATE_SERVICE_INGRESS,
        env_vars={"BOSAI_SERVICE_NAME": AUTHORITY_SERVICE, "BOSAI_PIPELINE_URL": pipeline_url},
    )
    proof["deployments"].append(authority)
    authority_url = authority["url"]

    studio = deploy_service(
        project=project,
        region=region,
        name=STUDIO_SERVICE,
        service_account=studio_email,
        allow_unauthenticated=True,
        ingress=STUDIO_INGRESS,
        env_vars={
            "BOSAI_SERVICE_NAME": STUDIO_SERVICE,
            "BOSAI_AUTHORITY_URL": authority_url,
            "BOSAI_PIPELINE_URL": pipeline_url,
        },
    )
    proof["deployments"].append(studio)

    proof["iam_bindings"].append(add_invoker(project, region, AUTHORITY_SERVICE, studio_email))
    proof["iam_bindings"].append(add_invoker(project, region, PIPELINE_SERVICE, authority_email))
    proof["intentionally_absent_binding"] = {
        "caller": studio_email,
        "target": PIPELINE_SERVICE,
        "reason_code": "STUDIO_HAS_NO_DIRECT_PIPELINE_EDGE",
    }

    print(json.dumps(proof, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise
