# BOSAI Studio Control Plane — Phase 5 Gemini Agent Loop Readback

Status: **PASS — RUNTIME PROVEN**  
Issue: **#10 — PHASE 5 — Gemini Agent Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `aff85d6118f6b9dbe2cf37c6dbc9c5dee13beeee`  
Working branch: `phase/05-gemini-agent-loop`

---

## 1. Phase decision

Phase 5 is **PASS**.

The real bounded Gemini reasoning loop has been observed on the operator Mac using Vertex AI, Google ADK, the official Grafana MCP runtime, and real Grafana Cloud Loki evidence.

```text
PHASE_5_CODE_PREPARATION=PASS
VERTEX_AI_AUTH_PROVEN=true
VERTEX_AI_API_ENABLED=true
ADK_DEPENDENCY_BINDING=PASS
REGRESSION_TESTS=22_PASS
DIRECT_GRAFANA_MCP_STDIO=PASS
LOCAL_GRAFANA_MCP_HTTP_HEALTH=PASS
DIRECT_PYTHON_MCP_HTTP_PROBE=PASS
ADK_MCP_SESSION=PASS
REAL_GEMINI_INVOCATION=PASS
REAL_GEMINI_GRAFANA_MCP_TOOL_USE_PROVEN=true
REAL_GRAFANA_EVIDENCE_MATCH=PASS
STRUCTURED_PROPOSAL_RUNTIME_PROVEN=true
AUTHORITY_ENGINE_INVOKED=false
PERMIT_ISSUED=false
MUTATION_ATTEMPTED=false
PHASE_5=PASS
```

No mocked model response is used for this runtime proof.

---

## 2. Google / Gemini runtime

Pinned Phase 5 runtime dependencies:

- `google-adk[mcp]==2.5.0`
- `google-auth[aiohttp]>=2.56,<3`

Model target observed in the successful readback:

`gemini-2.5-flash`

Vertex AI mode is mandatory:

`GOOGLE_GENAI_USE_VERTEXAI=true`

Operator preflight proved:

- Google Cloud CLI available;
- Application Default Credentials available;
- project `bosai-gemini-xprize` selected;
- Vertex AI API `aiplatform.googleapis.com` enabled;
- `GOOGLE_CLOUD_LOCATION=global` configured.

The successful runner readback reports:

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
- an explicit host allowlist for `localhost:8010` and `127.0.0.1:8010`;
- an explicit local Origin allowlist;
- no wildcard host/origin bypass.

The sidecar owns Grafana credentials. The Gemini runtime configuration does not receive the Grafana service-account token.

Observed transport proof:

```text
MCP_HTTP_HEALTH=200
MCP_HTTP_INITIALIZE=PASS
MCP_HTTP_TARGET_TOOL_PRESENT=true
```

The direct Python MCP HTTP probe succeeded before the ADK/Gemini run, proving the lower-level protocol path independently.

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

The successful readback reports:

```text
authority_engine_invoked=false
permit_issued=false
mutation_attempted=false
```

This preserves the Phase 2 rule:

`Intelligence is not authority.`

---

## 5. Locked Grafana retrieval contract

The first incident read is deliberately bounded to the exact Loki shape already proven during Phase 4.

Observed successful tool call:

```text
tool=query_loki_logs
datasourceUid=grafanacloud-logs
logql={service_name="bosai-studio-media-pipeline"} |= "TRANSCODE_A_CODEC_INIT_TIMEOUT"
startRfc3339=now-24h
limit=20
direction=backward
```

The MCP tool response contained both required proof values:

- `TRANSCODE_A_CODEC_INIT_TIMEOUT`
- `bosai-studio-media-pipeline`

and identified the affected worker as `transcode-a`.

The runner therefore reports:

```text
grafana_mcp_required_tool_observed=true
grafana_mcp_evidence_verified=true
```

---

## 6. Structured proposal proof

Gemini's final response is validated deterministically by `AgentProposalEnvelope` before conversion to the existing BOSAI `Proposal` dataclass.

Successful runtime proposal:

```text
incident_id=incident-demo-001
action=RESTART_TRANSCODE_WORKER
target=transcode-a
authority_decision=NOT_EVALUATED
proposal_only=true
```

The reasoning is grounded in the real Grafana log entry showing the codec initialization timeout on `transcode-a` while the delivery SLA is at risk.

The model returned its JSON inside one markdown JSON fence; the runner stripped that single wrapper and then applied strict schema validation. No surrounding prose or hidden fields are accepted.

The model cannot claim `AUTHORIZED`, invent a permit, or execute the proposal.

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
BOSAI Proposal
        ↓
STOP
```

No BOSAI authority evaluation or mutation is invoked by Gemini in Phase 5.

---

## 8. Regression proof

After the final retrieval-contract changes, the full repository suite returned:

```text
Ran 22 tests in 0.004s
OK
```

This includes the existing governed-execution and telemetry tests plus Phase 5 agent, transport, same-origin, and retrieval-contract tests.

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
G5_F_AUTHORITY_BOUNDARY=PASS
G5_G_REGRESSION=22_PASS
```

Phase 5 is ready for final PR readback and merge decision. No Phase 6 work should begin until the Phase 5 PR is reviewed and the canonical `air` branch is advanced.
