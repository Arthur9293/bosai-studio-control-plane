from __future__ import annotations

import json
import os
import subprocess

from bosai_studio.cloud_run_boundary import DEFAULT_REGION, PROJECT_ID_ENV, REGION_ENV, cloud_run_plan


def run_gcloud(args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        ["gcloud", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": ["gcloud", *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> None:
    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(REGION_ENV, DEFAULT_REGION)

    # Read-only commands only. This script must not create, deploy, bind, or delete anything.
    output = {
        "phase": "PHASE_8_CLOUD_RUN_IAM_PREFLIGHT",
        "project_id": project,
        "region": region,
        "mutation_attempted": False,
        "deployment_authorized": False,
        "plan": cloud_run_plan(project, region),
        "gcloud_account": run_gcloud(["auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]),
        "run_services": run_gcloud(["run", "services", "list", "--project", project, "--region", region, "--format=json"]),
        "service_accounts": run_gcloud([
            "iam",
            "service-accounts",
            "list",
            "--project",
            project,
            "--format=json",
        ]),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
