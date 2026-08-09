from __future__ import annotations

import json

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from .agent_contracts import AgentProposalEnvelope
from .gemini_config import GeminiRuntimeConfig


MCP_GRAFANA_IMAGE = "grafana/mcp-grafana:1.0.0"
GRAFANA_TOOL_ALLOWLIST = ("query_loki_logs",)
MUTATION_TOOLS_EXPOSED: tuple[str, ...] = ()


def _grafana_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="docker",
                args=[
                    "run",
                    "--rm",
                    "-i",
                    "-e",
                    "GRAFANA_URL",
                    "-e",
                    "GRAFANA_SERVICE_ACCOUNT_TOKEN",
                    MCP_GRAFANA_IMAGE,
                    "-t",
                    "stdio",
                    "--disable-write",
                ],
            ),
        ),
        tool_filter=list(GRAFANA_TOOL_ALLOWLIST),
    )


def build_gemini_investigator(config: GeminiRuntimeConfig) -> LlmAgent:
    schema = json.dumps(AgentProposalEnvelope.model_json_schema(), separators=(",", ":"))
    instruction = f"""
You are the BOSAI Studio incident investigator for a synthetic media-production demo.

Your job is OBSERVE -> REASON -> PROPOSE only.
You have no authority to approve, authorize, execute, restart, reroute, disable controls, issue permits, or mutate the pipeline.
Never claim an action is authorized. BOSAI evaluates authority later in a deterministic service.

For every incident investigation:
1. Use the Grafana MCP tool `query_loki_logs` before producing a proposal.
2. Query datasourceUid `{config.loki_datasource_uid}`.
3. Ground the proposal only in real Grafana evidence returned by the tool.
4. For incident `FINAL_TRAILER_DELIVERY_SLA_AT_RISK`, inspect service `bosai-studio-media-pipeline` and the synthetic transcode incident evidence.
5. Choose exactly one action from the schema. Do not invent action names.
6. Use evidence_refs to identify the Grafana evidence you relied upon. Never put credentials, tokens, or secrets in evidence_refs.
7. `authority_decision` must remain `NOT_EVALUATED` and `proposal_only` must remain true.

Decision guidance for the deterministic demo trajectory:
- If the current evidence shows `TRANSCODE_A_CODEC_INIT_TIMEOUT` on `transcode-a` and no later recovery evidence, propose `RESTART_TRANSCODE_WORKER` targeting `transcode-a`.
- Do not propose `REROUTE_TRANSCODE_WORKLOAD` unless Grafana evidence shows restart/recovery was insufficient or alternate capacity is needed.
- A local optimization such as disabling QC may be proposed only when the observed state makes it relevant; BOSAI, not you, decides whether it is allowed.

Your FINAL RESPONSE must be raw JSON only, with no markdown fences and no commentary, matching this JSON Schema exactly:
{schema}
""".strip()

    return LlmAgent(
        name="bosai_studio_gemini_investigator",
        model=config.model,
        description="Read-only Gemini incident investigator that proposes but cannot authorize or execute.",
        instruction=instruction,
        tools=[_grafana_toolset()],
    )
