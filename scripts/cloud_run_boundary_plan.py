from __future__ import annotations

import json
import os

from bosai_studio.cloud_run_boundary import DEFAULT_REGION, REGION_ENV, PROJECT_ID_ENV, cloud_run_plan


def main() -> None:
    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(REGION_ENV, DEFAULT_REGION)
    print(json.dumps(cloud_run_plan(project, region), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
