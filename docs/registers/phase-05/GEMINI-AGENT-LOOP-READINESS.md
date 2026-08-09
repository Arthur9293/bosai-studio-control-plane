# BOSAI Studio Control Plane — Phase 5 Gemini Agent Loop Readiness

Status: **PARTIAL — MCP_TRANSPORT_DIAGNOSTIC_IN_PROGRESS**  
Issue: **#10 — PHASE 5 — Gemini Agent Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `aff85d6118f6b9dbe2cf37c6dbc9c5dee13beeee`  
Working branch: `phase/05-gemini-agent-loop`

---

## 1. Phase decision

Phase 5 is not PASS yet.

The repository contains the bounded Google ADK/Gemini agent surface and the Google runtime preflight is proven locally. The direct official Grafana MCP runtime remains proven from Phase 4. The remaining gate is a successful Google ADK MCP session over the local read-only Streamable HTTP sidecar followed by a real Gemini tool trajectory and schema-valid proposal.

```text
PHASE_5_CODE_PREPARATION=PASS
VERTEX_AI_AUTH_PROVEN=true
VERTEX_AI_API_ENABLED=true
ADK_DEPENDENCY_BINDING=PASS
REGRESSION_TESTS=20_PASS
DIRECT_GRAFANA_MCP_STDIO=PASS
LOCAL_GRAFANA_MCP_HTTP_HEALTH=PASS
ADK_MCP_SESSION=NOT_YET_PROVEN
REAL_GEMINI_GRAFANA_MCP_TOOL_USE_PROVEN=false
STRUCTURED_PROPOSAL_RUNTIME_PROVEN=false
PHASE_5=PARTIAL
```

No mocked model response may satisfy the missing runtime gates.

---

## 2. Current Google runtime contract

Pinned Phase 5 runtime dependencies:

- `google-adk[mcp]==2.5.0`
- `google-auth[aiohttp]>=2.56,<3`

Model target:

`gemini-2.5-flash`

Vertex AI mode is mandatory:

`GOOGLE_GENAI_USE_VERTEXAI=true`

Local operator preflight has proven:

- Google Cloud CLI available;
- Application Default Credentials available;
- project `bosai-gemini-xprize` selected;
- Vertex AI API `aiplatform.googleapis.com` enabled;
- `GOOGLE_CLOUD_LOCATION=global` configured.

No Google credential JSON or access token is committed.

---

## 3. Agent authority boundary

Gemini receives only one external tool:

`query_loki_logs`

through Google ADK `McpToolset` connected to a local read-only Grafana MCP sidecar over Streamable HTTP.

Current local MCP endpoint contract:

`http://127.0.0.1:8010/`

The sidecar owns Grafana credentials; the Gemini/ADK runtime configuration does not require or receive the Grafana service-account token.

Explicit tool surface:

```text
GRAFANA_TOOL_ALLOWLIST=(query_loki_logs)
MUTATION_TOOLS_EXPOSED=()
```

Gemini does not receive:

- `AuthorityExecutor.execute`;
- permit issuance/consumption;
- pipeline mutation methods;
- restart/reroute mutation tools;
- Grafana write tools.

This enforces:

`Intelligence is not authority.`

---

## 4. Structured proposal boundary

Gemini's final response is not trusted as an authority artifact.

It must validate against `AgentProposalEnvelope` before conversion to the existing BOSAI `Proposal` dataclass.

The envelope requires:

- `proposal_id`;
- `incident_id`;
- one existing BOSAI `Action`;
- `target`;
- `reason`;
- non-empty `evidence_refs`;
- `expected_postconditions`;
- `authority_decision=NOT_EVALUATED`;
- `proposal_only=true`.

Extra fields are rejected. A model output containing `authority_decision=AUTHORIZED` or an invented `permit_id` fails deterministic schema validation.

The runner tolerates at most one JSON markdown fence around an otherwise standalone JSON object; surrounding commentary is rejected.

Conversion only creates a `Proposal`; it does not call BOSAI authority evaluation or execution.

---

## 5. Target real trajectory

User/incident input:

`FINAL_TRAILER_DELIVERY_SLA_AT_RISK / incident-demo-001`

Expected runtime trajectory:

```text
Gemini / ADK
  -> local official mcp-grafana over Streamable HTTP
  -> query_loki_logs
  -> real Loki response
  -> deterministic evidence assertion
  -> structured recovery proposal
  -> AgentProposalEnvelope validation
  -> BOSAI Proposal
  -> STOP
```

Required real evidence in the MCP response:

- `TRANSCODE_A_CODEC_INIT_TIMEOUT`
- `bosai-studio-media-pipeline`

Expected first proposal for the current incident evidence:

```text
action=RESTART_TRANSCODE_WORKER
target=transcode-a
authority_decision=NOT_EVALUATED
```

A different proposal is acceptable only if grounded in the real Grafana evidence and reviewed rather than retrofitted.

---

## 6. Runtime diagnostics completed

### Direct official MCP

The existing direct MCP client succeeds against official `grafana/mcp-grafana:1.0.0` over stdio, including tool discovery for `query_loki_logs`.

### Streamable HTTP sidecar

The sidecar is running read-only with an explicit local host allowlist and health endpoint:

```text
MCP_HTTP_HEALTH=200
```

A previous `403 forbidden: host not allowed` was resolved by explicitly allowing only:

- `localhost:8010`
- `127.0.0.1:8010`

No wildcard host bypass is used.

### ADK Streamable HTTP session

Google ADK 2.5.0 initially attempted mTLS for the local HTTP endpoint. Setting the local development environment variable below removed the mTLS warning:

`GOOGLE_API_USE_CLIENT_CERTIFICATE=false`

The ADK session still terminates before tool discovery, so the current diagnostic gate is now lower-level: prove the same Streamable HTTP endpoint with the Python MCP SDK directly, outside ADK.

A dedicated probe exists at:

`scripts/mcp_http_probe.py`

It must prove initialization and `query_loki_logs` discovery using the same Python MCP dependency installed with ADK.

---

## 7. Runtime evidence still required

Phase 5 closure requires a real runner readback proving:

1. ADK establishes the local MCP session.
2. Gemini responds from Vertex AI using the configured Google model.
3. ADK trajectory contains `query_loki_logs`.
4. No non-allowlisted tool is invoked.
5. The MCP response contains the required BOSAI telemetry evidence.
6. Final Gemini response validates against `AgentProposalEnvelope`.
7. `authority_decision=NOT_EVALUATED`.
8. `authority_engine_invoked=false`.
9. `permit_issued=false`.
10. `mutation_attempted=false`.
11. Full repository regression remains green.

---

## 8. Current closure state

```text
PHASE_5=PARTIAL
PHASE_5_CODE_PREPARATION=PASS
PHASE_5_TOOL_BOUNDARY=PASS_BY_CODE_REVIEW
PHASE_5_STRUCTURED_CONTRACT=PASS_BY_CODE_REVIEW
G5_A_GOOGLE_CLOUD_AUTH=PASS
G5_A_VERTEX_AI_API=PASS
G5_A_DEPENDENCY_BINDING=PASS
REGRESSION_TESTS=20_PASS
DIRECT_GRAFANA_MCP_STDIO=PASS
LOCAL_GRAFANA_MCP_HTTP_HEALTH=PASS
DIRECT_PYTHON_MCP_HTTP_PROBE=PENDING
REAL_GEMINI_GRAFANA_MCP_TOOL_USE=false
NEXT_GATE=G5_B_DIRECT_PYTHON_MCP_HTTP_PROBE
```

The Phase 5 branch must remain unmerged until real Gemini + ADK + Grafana MCP evidence and final regression tests exist.
