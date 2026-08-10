from __future__ import annotations

import json
import os
import subprocess
from typing import Any
from urllib import error, request

from bosai_studio.cloud_run_phase9 import (
    AUTHORITY_SERVICE,
    DEFAULT_PHASE9_REGION,
    PHASE9_REGION_ENV,
    PIPELINE_SERVICE,
    PROJECT_ID_ENV,
    STUDIO_SERVICE,
)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


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


def unauthenticated_get(url: str) -> dict[str, Any]:
    try:
        req = request.Request(url, headers={"User-Agent": "bosai-phase9-proof"})
        with request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            try:
                body: Any = json.loads(text)
            except json.JSONDecodeError:
                body = text[:500]
            return {"status": response.status, "ok": 200 <= response.status < 300, "body": body}
    except error.HTTPError as exc:
        return {"status": exc.code, "ok": False, "body": exc.read().decode("utf-8", errors="replace")[:500]}
    except Exception as exc:
        return {"status": 0, "ok": False, "error_type": type(exc).__name__, "body": str(exc)[:500]}


def nested_pipeline_status(payload: dict[str, Any]) -> int | None:
    authority_response = payload.get("authority_response")
    if not isinstance(authority_response, dict):
        return None
    authority_body = authority_response.get("body")
    if not isinstance(authority_body, dict):
        return None
    pipeline_response = authority_body.get("pipeline_response")
    if not isinstance(pipeline_response, dict):
        return None
    status = pipeline_response.get("status")
    return status if isinstance(status, int) else None


def main() -> None:
    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(PHASE9_REGION_ENV, DEFAULT_PHASE9_REGION)

    studio_url = service_url(project, region, STUDIO_SERVICE)
    authority_url = service_url(project, region, AUTHORITY_SERVICE)
    pipeline_url = service_url(project, region, PIPELINE_SERVICE)

    studio_health = unauthenticated_get(f"{studio_url}/health")
    authority_public = unauthenticated_get(f"{authority_url}/health")
    pipeline_public = unauthenticated_get(f"{pipeline_url}/health")
    positive_chain = unauthenticated_get(f"{studio_url}/execute-pipeline")
    direct_denial = unauthenticated_get(f"{studio_url}/call-pipeline-direct")

    positive_body = positive_chain.get("body") if isinstance(positive_chain.get("body"), dict) else {}
    direct_body = direct_denial.get("body") if isinstance(direct_denial.get("body"), dict) else {}
    direct_pipeline = direct_body.get("pipeline_response") if isinstance(direct_body, dict) else None

    checks = {
        "studio_public_health_ok": studio_health.get("status") == 200,
        "public_authority_denied": authority_public.get("status") != 200,
        "public_pipeline_denied": pipeline_public.get("status") != 200,
        "studio_to_authority_ok": isinstance(positive_body, dict)
        and isinstance(positive_body.get("authority_response"), dict)
        and positive_body["authority_response"].get("status") == 200,
        "authority_to_pipeline_ok": nested_pipeline_status(positive_body if isinstance(positive_body, dict) else {}) == 200,
        "studio_to_pipeline_direct_denied": isinstance(direct_pipeline, dict)
        and direct_pipeline.get("status") != 200,
    }
    proof = {
        "phase": "PHASE_9_RUNTIME_IAM_PROOF",
        "project_id": project,
        "region": region,
        "service_urls": {
            "studio-control-plane": studio_url,
            "authority-executor": authority_url,
            "media-pipeline-sim": pipeline_url,
        },
        "checks": checks,
        "runtime_iam_enforcement_proven": all(checks.values()),
        "secret_values_printed": False,
        "observations": {
            "studio_health": studio_health,
            "public_authority": authority_public,
            "public_pipeline": pipeline_public,
            "positive_chain": positive_chain,
            "direct_denial": direct_denial,
        },
    }
    print(json.dumps(proof, indent=2, sort_keys=True))
    if not proof["runtime_iam_enforcement_proven"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
