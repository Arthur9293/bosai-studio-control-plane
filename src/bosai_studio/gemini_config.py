from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GRAFANA_LOKI_DATASOURCE_UID = "grafanacloud-logs"


@dataclass(frozen=True)
class GeminiRuntimeConfig:
    google_cloud_project: str
    google_cloud_location: str
    model: str
    grafana_url: str
    grafana_service_account_token: str
    loki_datasource_uid: str


def load_gemini_runtime_config() -> GeminiRuntimeConfig:
    """Load Phase 5 runtime configuration and fail closed on missing boundaries."""
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() != "true":
        raise RuntimeError("GOOGLE_GENAI_USE_VERTEXAI=true is required; Gemini Developer API mode is not allowed for Phase 5")

    required = (
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GRAFANA_URL",
        "GRAFANA_SERVICE_ACCOUNT_TOKEN",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("missing required environment variable(s): " + ", ".join(missing))

    return GeminiRuntimeConfig(
        google_cloud_project=os.environ["GOOGLE_CLOUD_PROJECT"],
        google_cloud_location=os.environ["GOOGLE_CLOUD_LOCATION"],
        model=os.getenv("BOSAI_GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        grafana_url=os.environ["GRAFANA_URL"],
        grafana_service_account_token=os.environ["GRAFANA_SERVICE_ACCOUNT_TOKEN"],
        loki_datasource_uid=os.getenv(
            "BOSAI_GRAFANA_LOKI_DATASOURCE_UID",
            DEFAULT_GRAFANA_LOKI_DATASOURCE_UID,
        ),
    )
