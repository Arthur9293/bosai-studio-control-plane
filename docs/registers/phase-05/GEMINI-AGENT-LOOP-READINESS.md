# BOSAI Studio Control Plane — Phase 5 Gemini Agent Loop Readback

Status: **PASS — RUNTIME PROVEN ON STRENGTHENED CONTRACT**  
Issue: **#10 — PHASE 5 — Gemini Agent Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `aff85d6118f6b9dbe2cf37c6dbc9c5dee13beeee`  
Working branch: `phase/05-gemini-agent-loop`

---

## 1. Phase decision

Phase 5 is **PASS**.

The complete real bounded Gemini reasoning loop has been observed on the operator Mac using Vertex AI, Google ADK, the official Grafana MCP runtime, and real Grafana Cloud Loki evidence. The final successful run was performed after strengthening the proposal schema so `expected_postconditions` must contain at least one non-blank observable verification condition.

```text
PHASE_5_CODE_PREPARATION=PASS
VERTEX_AI_AUTH_PROVEN=true
VERTEX_AI_API_ENABLED=true
ADK_DEPENDENCY_BINDING=PASS
DIRECT_GRAFANA_MCP_STDIO=PASS
LOCAL_GRAFANA_MCP_HTTP_HEALTH=PASS
DIRECT_PYTHON_MCP_HTTP_PROBE=PASS
ADK_MCP_SESSION=PASS
REAL_GEMINI_INVOCATION=PASS
REAL_GEMINI_GRAFANA_MCP_TOOL_USE_PROVEN=true
REAL_GRAFANA_EVIDENCE_MATCH=PASS
STRUCTURED_PROPOSAL_RUNTIME_PROVEN=true
POSTCONDITION_CONTRACT_PROVEN=true
AUTHORITY_ENGINE_INVOKED=false
PERMIT_ISSUED=false
MUTATION_ATTEMPTED=false
REGRESSION_TESTS=23_PASS
PHASE_5=PASS
```

No mocked model response is used for the runtime proof.

---

## 2. Google / Gemini runtime

Pinned Phase 5 runtime dependencies:

- `google-adk[mcp]==2.5.0`
- `google-auth[aiohttp]>=2.56,<3`

Observed model:

`gemini-2.5-flash`

Vertex AI mode is mandatory:

`GOOGLE_GENAI_USE_VERTEXAI=true`

Operator preflight proved:

- Google Cloud CLI available;
- Application Default Credentials available;
- project `bosai-gemini-xprize` selected;
- Vertex AI API `aiplatform.googleapis.com` enabled;
- `GOOGLE_CLOUD_LOCATION=global` configured.

The successful runner reports:

`vertex_ai=true`

No Google credential JSON or access token is committed.

---

## 3. Grafana MCP transport and security boundary

Google ADK connects only to the local read-only official Grafana MCP sidecar over Streamable HTTP.

Local endpoint:

`http://127.0.0.1:8010/mcp`

The sidecar is launched with:

- `grafana/mcp-grafana:1.0.0`;
- `--disable-write`;
- explicit Host allowlists;
- explicit same-origin allowlists;
- no wildcard Host/Origin bypass.

The sidecar owns Grafana credentials. The Gemini runtime configuration does not receive the Grafana service-account token.

Observed transport proof:

```text
MCP_HTTP_HEALTH=200
MCP_HTTP_INITIALIZE=PASS
MCP_HTTP_TARGET_TOOL_PRESENT=true
```

---

## 4. Agent authority boundary

Gemini receives only one external tool:

`query_loki_logs`

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

The final readback reports:

```text
authority_engine_invoked=false
permit_issued=false
mutation_attempted=false
```

This preserves:

`Intelligence is not authority.`

---

## 5. Locked Grafana retrieval contract

The first incident read is bounded to the exact Loki shape already proven during Phase 4.

Observed successful tool call:

```text
tool=query_loki_logs
datasourceUid=grafanacloud-logs
logql={service_name="bosai-studio-media-pipeline"} |= "TRANSCODE_A_CODEC_INIT_TIMEOUT"
startRfc3339=now-24h
limit=20
direction=backward
```

The real MCP response contained:

- `TRANSCODE_A_CODEC_INIT_TIMEOUT`;
- `bosai-studio-media-pipeline`;
- worker `transcode-a`.

The runner reports:

```text
grafana_mcp_required_tool_observed=true
grafana_mcp_evidence_verified=true
```

---

## 6. Strengthened structured proposal proof

Gemini's final response is validated deterministically against `AgentProposalEnvelope` before conversion to the existing BOSAI `Proposal` dataclass.

The strengthened envelope requires:

- `proposal_id`;
- `incident_id`;
- one existing BOSAI `Action`;
- `target`;
- `reason`;
- at least one non-blank `evidence_ref`;
- at least one non-blank `expected_postcondition`;
- `authority_decision=NOT_EVALUATED`;
- `proposal_only=true`.

The final real runtime proposal passed that stronger schema:

```text
incident_id=incident-demo-001
action=RESTART_TRANSCODE_WORKER
target=transcode-a
authority_decision=NOT_EVALUATED
proposal_only=true
```

Observed postconditions were concrete and verification-oriented, including:

1. `transcode-a` successfully restarts;
2. subsequent `transcode-a` logs show successful codec initialization and forward media-processing progress;
3. subsequent telemetry shows recovery or resolution of `FINAL_TRAILER_DELIVERY_SLA_AT_RISK`.

This closes the red-team gap found in the previous successful runtime, where `expected_postconditions` was empty.

Extra fields remain rejected. A model output containing `authority_decision=AUTHORIZED`, an invented `permit_id`, an empty postcondition list, or blank postconditions fails deterministic validation.

---

## 7. Proven real trajectory

```text
FINAL_TRAILER_DELIVERY_SLA_AT_RISK
        ↓
Gemini 2.5 Flash on Vertex AI
        ↓
Google ADK
        ↓
McpToolset: query_loki_logs only
        ↓
local official mcp-grafana 1.0.0 / Streamable HTTP
        ↓
Grafana Cloud Loki
        ↓
real TRANSCODE_A_CODEC_INIT_TIMEOUT evidence
        ↓
Gemini proposes RESTART_TRANSCODE_WORKER / transcode-a
        ↓
AgentProposalEnvelope deterministic validation
        ↓
non-empty observable postconditions
        ↓
BOSAI Proposal
        ↓
STOP
```

No BOSAI authority evaluation or mutation is invoked by Gemini in Phase 5.

---

## 8. Regression proof

After the strengthened postcondition contract, the full repository suite returned:

```text
Ran 23 tests in 0.004s
OK
```

This includes the governed-execution and telemetry tests plus Phase 5 agent, transport, same-origin, retrieval-contract, and postcondition-contract tests.

---

## 9. Closure state

```text
PHASE_5=PASS
G5_A_GOOGLE_CLOUD_AUTH=PASS
G5_A_VERTEX_AI_API=PASS
G5_A_DEPENDENCY_BINDING=PASS
G5_B_DIRECT_PYTHON_MCP_HTTP_PROBE=PASS
G5_C_REAL_GEMINI_ADK_GRAFANA_TRAJECTORY=PASS
G5_D_REAL_GRAFANA_EVIDENCE=PASS
G5_E_STRUCTURED_PROPOSAL=PASS
G5_F_POSTCONDITION_CONTRACT=PASS
G5_G_AUTHORITY_BOUNDARY=PASS
G5_H_REGRESSION=23_PASS
```

Phase 5 is ready for final PR diff/readback and merge against the expected head SHA. No Phase 6 work should begin until the canonical `air` branch advances.