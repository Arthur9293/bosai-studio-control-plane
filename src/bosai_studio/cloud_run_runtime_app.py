from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, parse, request

METADATA_IDENTITY_ENDPOINT = (
    "http://metadata.google.internal/computeMetadata/v1/instance/"
    "service-accounts/default/identity"
)

SERVICE_NAME_ENV = "BOSAI_SERVICE_NAME"
AUTHORITY_URL_ENV = "BOSAI_AUTHORITY_URL"
PIPELINE_URL_ENV = "BOSAI_PIPELINE_URL"
DEFAULT_PORT = 8080


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def fetch_identity_token(audience: str) -> str:
    url = f"{METADATA_IDENTITY_ENDPOINT}?audience={parse.quote(audience, safe='')}"
    req = request.Request(url, headers={"Metadata-Flavor": "Google"})
    with request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")


def call_authenticated(base_url: str, path: str) -> dict[str, Any]:
    audience = base_url.rstrip("/")
    target = f"{audience}{path}"
    try:
        token = fetch_identity_token(audience)
        req = request.Request(
            target,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "bosai-phase9-runtime-proof",
            },
        )
        with request.urlopen(req, timeout=20) as response:
            body_text = response.read().decode("utf-8")
            try:
                body: Any = json.loads(body_text)
            except json.JSONDecodeError:
                body = body_text
            return {"status": response.status, "ok": 200 <= response.status < 300, "body": body}
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "ok": False, "body": body_text[:500]}
    except Exception as exc:  # pragma: no cover - exercised only in Cloud Run runtime failures
        return {"status": 0, "ok": False, "error_type": type(exc).__name__, "body": str(exc)[:500]}


class BosaiPhase9Handler(BaseHTTPRequestHandler):
    server_version = "BOSAIPhase9/1.0"

    @property
    def service_name(self) -> str:
        return os.getenv(SERVICE_NAME_ENV, "unknown-service")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path in {"/", "/health"}:
            self.send_json(
                200,
                {
                    "ok": True,
                    "service": self.service_name,
                    "phase": "PHASE_9_RUNTIME_ENFORCEMENT_PROOF",
                },
            )
            return

        if self.path == "/execute-pipeline":
            self.handle_execute_pipeline()
            return

        if self.path == "/call-pipeline-direct":
            self.handle_direct_pipeline_call()
            return

        self.send_json(404, {"ok": False, "service": self.service_name, "error": "NOT_FOUND"})

    def handle_execute_pipeline(self) -> None:
        if self.service_name == "studio-control-plane":
            authority_url = os.getenv(AUTHORITY_URL_ENV)
            if not authority_url:
                self.send_json(500, {"ok": False, "service": self.service_name, "error": "AUTHORITY_URL_MISSING"})
                return
            authority_response = call_authenticated(authority_url, "/execute-pipeline")
            self.send_json(
                200,
                {
                    "ok": authority_response.get("ok") is True,
                    "service": self.service_name,
                    "edge": "studio-control-plane -> authority-executor",
                    "authority_response": authority_response,
                },
            )
            return

        if self.service_name == "authority-executor":
            pipeline_url = os.getenv(PIPELINE_URL_ENV)
            if not pipeline_url:
                self.send_json(500, {"ok": False, "service": self.service_name, "error": "PIPELINE_URL_MISSING"})
                return
            pipeline_response = call_authenticated(pipeline_url, "/health")
            self.send_json(
                200,
                {
                    "ok": pipeline_response.get("ok") is True,
                    "service": self.service_name,
                    "edge": "authority-executor -> media-pipeline-sim",
                    "pipeline_response": pipeline_response,
                },
            )
            return

        self.send_json(
            403,
            {
                "ok": False,
                "service": self.service_name,
                "error": "SERVICE_NOT_ALLOWED_TO_EXECUTE_PIPELINE_PATH",
            },
        )

    def handle_direct_pipeline_call(self) -> None:
        if self.service_name != "studio-control-plane":
            self.send_json(403, {"ok": False, "service": self.service_name, "error": "ONLY_STUDIO_PROBES_DIRECT_EDGE"})
            return
        pipeline_url = os.getenv(PIPELINE_URL_ENV)
        if not pipeline_url:
            self.send_json(500, {"ok": False, "service": self.service_name, "error": "PIPELINE_URL_MISSING"})
            return
        pipeline_response = call_authenticated(pipeline_url, "/health")
        self.send_json(
            200,
            {
                "ok": pipeline_response.get("ok") is False,
                "service": self.service_name,
                "edge": "studio-control-plane -> media-pipeline-sim",
                "expected": "DENIED_BY_CLOUD_RUN_IAM",
                "pipeline_response": pipeline_response,
            },
        )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        return


def main() -> None:
    port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer(("0.0.0.0", port), BosaiPhase9Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
