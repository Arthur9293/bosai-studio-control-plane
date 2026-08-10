from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from bosai_studio.cloud_run_boundary import DEFAULT_REGION, PROJECT_ID_ENV, REGION_ENV, ServiceName
from bosai_studio.cloud_run_runtime_enforcement import service_accounts


EXPECTED_SUCCESS = {200, 201, 202, 204}
EXPECTED_DENIAL = {401, 403, 404}


def run(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(argv, check=False, capture_output=True, text=True)
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def service_url(project: str, region: str, service: str) -> str:
    result = run([
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
    ])
    if result["returncode"] != 0 or not result["stdout"]:
        raise RuntimeError(f"could not resolve Cloud Run URL for {service}: {result}")
    return str(result["stdout"]).splitlines()[-1].strip()


def identity_token(service_account_email: str, audience: str) -> str:
    result = run([
        "gcloud",
        "auth",
        "print-identity-token",
        f"--impersonate-service-account={service_account_email}",
        f"--audiences={audience}",
    ])
    if result["returncode"] != 0 or not result["stdout"]:
        raise RuntimeError(f"could not mint identity token for {service_account_email}: {result['stderr']}")
    return str(result["stdout"]).splitlines()[-1].strip()


def curl_status(url: str, token: str | None = None) -> dict[str, Any]:
    argv = ["curl", "-sS", "-o", "/tmp/bosai_phase9_probe_body.txt", "-w", "%{http_code}"]
    if token:
        argv.extend(["-H", f"Authorization: Bearer {token}"])
    argv.append(url)
    result = run(argv)
    try:
        status = int(str(result["stdout"]).strip()[-3:])
    except ValueError:
        status = 0
    return {
        "returncode": result["returncode"],
        "status": status,
        "stderr": result["stderr"],
    }


def main() -> None:
    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(REGION_ENV, DEFAULT_REGION)

    accounts = service_accounts(project)
    urls = {
        ServiceName.STUDIO_CONTROL_PLANE.value: service_url(project, region, ServiceName.STUDIO_CONTROL_PLANE.value),
        ServiceName.AUTHORITY_EXECUTOR.value: service_url(project, region, ServiceName.AUTHORITY_EXECUTOR.value),
        ServiceName.MEDIA_PIPELINE_SIM.value: service_url(project, region, ServiceName.MEDIA_PIPELINE_SIM.value),
    }

    authority_url = urls[ServiceName.AUTHORITY_EXECUTOR.value]
    pipeline_url = urls[ServiceName.MEDIA_PIPELINE_SIM.value]

    studio_token_for_authority = identity_token(accounts[ServiceName.STUDIO_CONTROL_PLANE.value], authority_url)
    authority_token_for_pipeline = identity_token(accounts[ServiceName.AUTHORITY_EXECUTOR.value], pipeline_url)
    studio_token_for_pipeline = identity_token(accounts[ServiceName.STUDIO_CONTROL_PLANE.value], pipeline_url)

    probes = {
        "public_to_authority": curl_status(authority_url),
        "public_to_pipeline": curl_status(pipeline_url),
        "studio_to_authority": curl_status(authority_url, studio_token_for_authority),
        "authority_to_pipeline": curl_status(pipeline_url, authority_token_for_pipeline),
        "studio_to_pipeline": curl_status(pipeline_url, studio_token_for_pipeline),
    }

    verification = {
        "public_to_authority_denied": probes["public_to_authority"]["status"] in EXPECTED_DENIAL,
        "public_to_pipeline_denied": probes["public_to_pipeline"]["status"] in EXPECTED_DENIAL,
        "studio_to_authority_allowed": probes["studio_to_authority"]["status"] in EXPECTED_SUCCESS,
        "authority_to_pipeline_allowed": probes["authority_to_pipeline"]["status"] in EXPECTED_SUCCESS,
        "studio_to_pipeline_denied": probes["studio_to_pipeline"]["status"] in EXPECTED_DENIAL,
    }

    output = {
        "phase": "PHASE_9_CLOUD_RUN_RUNTIME_IAM_PROBE",
        "project_id": project,
        "region": region,
        "urls": urls,
        "probes": probes,
        "verification": verification,
        "runtime_iam_enforcement_proven": all(verification.values()),
        "identity_tokens_printed": False,
        "secret_values_printed": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
