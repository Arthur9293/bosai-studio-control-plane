from __future__ import annotations

import argparse
import json
import os
import subprocess

from bosai_studio.cloud_run_phase9 import (
    AUTHORITY_SA,
    AUTHORITY_SERVICE,
    DEFAULT_PHASE9_REGION,
    PHASE9_REGION_ENV,
    PIPELINE_SA,
    PIPELINE_SERVICE,
    PROJECT_ID_ENV,
    ROLLBACK_GO_ENV,
    STUDIO_SA,
    STUDIO_SERVICE,
    rollback_human_go_valid,
    service_account_email,
)


def run(cmd: list[str]) -> dict[str, object]:
    print("$ " + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return {
        "command": cmd[:4],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip()[-1000:],
        "stderr": completed.stderr.strip()[-1000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rollback isolated Phase 9 Cloud Run proof resources.")
    parser.add_argument("--apply", action="store_true", help="Actually delete the isolated proof resources.")
    args = parser.parse_args()

    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(PHASE9_REGION_ENV, DEFAULT_PHASE9_REGION)
    go_value = os.getenv(ROLLBACK_GO_ENV)

    plan = {
        "phase": "PHASE_9_ROLLBACK",
        "project_id": project,
        "region": region,
        "services_to_delete": [STUDIO_SERVICE, AUTHORITY_SERVICE, PIPELINE_SERVICE],
        "service_accounts_to_delete": [
            service_account_email(STUDIO_SA, project),
            service_account_email(AUTHORITY_SA, project),
            service_account_email(PIPELINE_SA, project),
        ],
    }
    if not args.apply:
        print(json.dumps({"dry_run": True, "plan": plan}, indent=2, sort_keys=True))
        return

    if not rollback_human_go_valid(go_value):
        raise RuntimeError(f"{ROLLBACK_GO_ENV} must equal HUMAN GO PHASE 9 ROLLBACK")

    results: dict[str, object] = {"plan": plan, "human_go_verified": True, "service_deletes": [], "service_account_deletes": []}
    for service in [STUDIO_SERVICE, AUTHORITY_SERVICE, PIPELINE_SERVICE]:
        results["service_deletes"].append(
            run(["gcloud", "run", "services", "delete", service, "--project", project, "--region", region, "--quiet"])
        )
    for account in [STUDIO_SA, AUTHORITY_SA, PIPELINE_SA]:
        email = service_account_email(account, project)
        results["service_account_deletes"].append(
            run(["gcloud", "iam", "service-accounts", "delete", email, "--project", project, "--quiet"])
        )
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
