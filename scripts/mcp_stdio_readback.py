from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from typing import Any

PROTOCOL_VERSION = "2025-06-18"


class MCPStdioClient:
    def __init__(self, command: list[str], env: dict[str, str]) -> None:
        self._next_id = 1
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            bufsize=1,
            env=env,
        )
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("failed to open MCP stdio pipes")

    def _send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        assert self.process.stdout is not None
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError(f"MCP server terminated while waiting for {method}")
            message = json.loads(line)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"MCP {method} error: {message['error']}")
                return message["result"]

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "bosai-studio-grafana-readback", "version": "0.1.0"},
            },
        )
        self.notify("notifications/initialized")
        return result

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=3)


def sanitized_env() -> dict[str, str]:
    required = ("GRAFANA_URL", "GRAFANA_SERVICE_ACCOUNT_TOKEN")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("missing required environment variable(s): " + ", ".join(missing))
    return os.environ.copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal read-only MCP stdio smoke client for official mcp-grafana.")
    parser.add_argument(
        "--server-command",
        default=os.getenv("MCP_GRAFANA_COMMAND", "mcp-grafana -t stdio --disable-write"),
        help="Command used to launch official mcp-grafana.",
    )
    parser.add_argument("--tool", help="Optional MCP tool to invoke after initialization.")
    parser.add_argument("--arguments-json", default="{}", help="JSON object passed to --tool.")
    args = parser.parse_args()

    client = MCPStdioClient(shlex.split(args.server_command), sanitized_env())
    try:
        init = client.initialize()
        tools = client.request("tools/list")
        output: dict[str, Any] = {
            "protocol_version": init.get("protocolVersion"),
            "server_info": init.get("serverInfo"),
            "tool_names": [tool.get("name") for tool in tools.get("tools", [])],
        }
        if args.tool:
            arguments = json.loads(args.arguments_json)
            if not isinstance(arguments, dict):
                raise ValueError("--arguments-json must decode to a JSON object")
            started = time.time()
            result = client.request("tools/call", {"name": args.tool, "arguments": arguments})
            output["tool"] = args.tool
            output["duration_ms"] = round((time.time() - started) * 1000, 1)
            output["result"] = result
        print(json.dumps(output, indent=2, sort_keys=True, default=str))
    finally:
        client.close()


if __name__ == "__main__":
    main()
