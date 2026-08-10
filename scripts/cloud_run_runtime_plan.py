from __future__ import annotations

import json
import os

from bosai_studio.cloud_run_boundary import DEFAULT_REGION, PROJECT_ID_ENV, REGION_ENV
from bosai_studio.cloud_run_runtime_enforcement import runtime_enforcement_plan


def main() -> None:
    project = os.getenv(PROJECT_ID_ENV)
    if not project:
        raise RuntimeError(f"{PROJECT_ID_ENV} is required")
    region = os.getenv(REGION_ENV, DEFAULT_REGION)
    print(json.dumps(runtime_enforcement_plan(project, region), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
