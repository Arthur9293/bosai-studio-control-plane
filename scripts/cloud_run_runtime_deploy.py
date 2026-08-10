from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Any

from bosai_studio.cloud_run_boundary import DEFAULT_REGION, PROJECT_ID_ENV, REGION_ENV
from bosai_studio.cloud_run_runtime_enforcement import (
    HUMAN_GO_ENV,
    deployment_commands,
    require_human_go,
    runtime_enforcement_plan,
)


def run_command(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy synthetic Phase 9 Cloud Run IAM proof resources.")
    parser.add_argument("--execute", action="store_true", help="Actually run mutating gcloud commands.")
    args = parser.parse_args()

    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(REGION_ENV, DEFAULT_REGION)

    plan = runtime_enforcement_plan(project, region)
    commands = deployment_commands(project, region)

    output: dict[str, Any] = {
        "phase": "PHASE_9_CLOUD_RUN_RUNTIME_DEPLOYMENT",
        "project_id": project,
        "region": region,
        "execute_requested": args.execute,
        "human_go_env_present": bool(os.getenv(HUMAN_GO_ENV)),
        "commands": [
            {
                "name": command.name,
                "argv": command.as_list(),
                "mutates_cloud": command.mutates_cloud,
            }
            for command in commands
        ],
        "plan": plan,
        "results": [],
        "secret_values_printed": False,
    }

    if not args.execute:
        output["deployment_performed"] = False
        output["reason_code"] = "PLAN_ONLY_REQUIRES_EXECUTE_FLAG"
        print(json.dumps(output, indent=2, sort_keys=True))
        return

    require_human_go(os.getenv(HUMAN_GO_ENV))

    results = []
    for command in commands:
        # Service-account describe is allowed to fail if the account does not exist yet.
        # In that case the following create command is expected to establish it.
        result = run_command(command.as_list())
        results.append({"name": command.name, **result})

    output["deployment_performed"] = True
    output["results"] = results
    output["all_returncodes_zero_or_describe_missing"] = all(
        result["returncode"] == 0 or str(result["name"]).startswith("describe-sa-")
        for result in results
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
