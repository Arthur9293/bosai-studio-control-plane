# BOSAI Studio Control Plane — Phase 5 Gemini Agent Loop Readback

Status: **HOLD — POSTCONDITION CONTRACT STRENGTHENED; RUNTIME REVALIDATION REQUIRED**  
Issue: **#10 — PHASE 5 — Gemini Agent Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `aff85d6118f6b9dbe2cf37c6dbc9c5dee13beeee`  
Working branch: `phase/05-gemini-agent-loop`

---

## 1. Phase decision

The complete real Gemini/ADK/Grafana trajectory has been proven, but final Phase 5 closure is temporarily held after red-team readback found one semantic weakness in the successful proposal: `expected_postconditions` was present but empty.

That is insufficient for the BOSAI control loop because `VERIFY` requires at least one concrete post-condition that can be checked after an authorized action.

The deterministic proposal schema and Gemini instruction have therefore been strengthened so that `expected_postconditions` must be non-empty and contain non-blank strings. The successful runtime must be repeated against this stronger contract before Phase 5 can be merged.

```text
PHASE_5_CODE_PREPARATION=PASS
VERTEX_AI_AUTH_PROVEN=true
VERTEX_AI_API_ENABLED=true
ADK_DEPENDENCY_BINDING=PASS
DIRECT_GRAFANA_MCP_STDIO=PASS
LOCAL_GRAFANA_MCP_HTTP_HEALTH=PASS
DIRECT_PYTHON_MCP_HTTP_PROBE=PASS
ADK_MCP_SESSION=PASS_PREVIOUS_BUILD
REAL_GEMINI_INVOCATION=PASS_PREVIOUS_BUILD
REAL_GEMINI_GRAFANA_MCP_TOOL_USE_PROVEN=true
REAL_GRAFANA_EVIDENCE_MATCH=PASS_PREVIOUS_BUILD
AUTHORITY_ENGINE_INVOKED=false
PERMIT_ISSUED=false
MUTATION_ATTEMPTED=false
POSTCONDITION_CONTRACT_STRENGTHENED=true
REGRESSION_AFTER_STRENGTHENING=PENDING
STRUCTURED_PROPOSAL_RUNTIME_PROVEN=REVALIDATION_REQUIRED
PHASE_5=HOLD
```

No mocked model response may satisfy the remaining gate.

---

## 2. Google / Gemini runtime

Pinned Phase 5 runtime dependencies:

- `google-adk[mcp]==2.5.0`
- `google-auth[aiohttp]>=2.56,<3`

Model target:

`gemini-2.5-flash`

Vertex AI mode is mandatory:

`GOOGLE_GENAI_USE_VERTEXAI=true`

Operator preflight has proven:

- Google Cloud CLI available;
- Application Default Credentials available;
- project `bosai-gemini-xprize` selected;
- Vertex AI API `aiplatform.googleapis.com` enabled;
- `GOOGLE_CLOUD_LOCATION=global` configured.

No Google credential JSON or access token is committed.

---

## 3. Grafana MCP transport and security boundary

Google ADK connects only to the local read-only official Grafana MCP sidecar over Streamable HTTP.

Local endpoint:

`http://127.0.0.1:8010/mcp`

The sidecar is launched with:

- `grafana/mcp-grafana:1.0.0`;
- `--disable-write`;
- an explicit host allowlist;
- an explicit local Origin allowlist;
- no wildcard host/origin bypass.

The sidecar owns Grafana credentials. The Gemini runtime configuration does not receive the Grafana service-account token.

Previously observed transport proof remains valid:

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

The successful previous-build readback reported:

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

```text
tool=query_loki_logs
datasourceUid=grafanacloud-logs
logql={service_name="bosai-studio-media-pipeline"} |= "TRANSCODE_A_CODEC_INIT_TIMEOUT"
startRfc3339=now-24h
limit=20
direction=backward
```

The successful previous-build MCP response contained:

- `TRANSCODE_A_CODEC_INIT_TIMEOUT`;
- `bosai-studio-media-pipeline`;
- worker `transcode-a`.

---

## 6. Strengthened structured proposal boundary

Gemini's final response must validate deterministically against `AgentProposalEnvelope` before conversion to the existing BOSAI `Proposal` dataclass.

The envelope requires:

- `proposal_id`;
- `incident_id`;
- one existing BOSAI `Action`;
- `target`;
- `reason`;
- at least one non-blank `evidence_ref`;
- **at least one non-blank `expected_postcondition`**;
- `authority_decision=NOT_EVALUATED`;
- `proposal_only=true`.

The new postcondition requirement is deliberate: a proposal is incomplete unless it states what later telemetry should prove if an authorized execution succeeds.

Extra fields remain rejected. A model output containing `authority_decision=AUTHORIZED`, an invented `permit_id`, an empty postcondition list, or blank postconditions fails deterministic validation.

---

## 7. Previous real trajectory proof

The previous build proved:

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
AgentProposalEnvelope validation
        ↓
BOSAI Proposal
        ↓
STOP
```

The only closure defect found during final red-team readback was the empty `expected_postconditions` list.

---

## 8. Remaining closure gate

Phase 5 may return to PASS only after:

1. the strengthened repository regression is green;
2. the real Gemini runner is repeated against the current head;
3. `query_loki_logs` again returns the required real BOSAI evidence;
4. the proposal again selects an evidence-grounded action/target;
5. `expected_postconditions` contains at least one concrete observable verification condition;
6. `authority_decision=NOT_EVALUATED`;
7. `authority_engine_invoked=false`;
8. `permit_issued=false`;
9. `mutation_attempted=false`.

---

## 9. Current closure state

```text
PHASE_5=HOLD
G5_A_GOOGLE_CLOUD_AUTH=PASS
G5_A_VERTEX_AI_API=PASS
G5_A_DEPENDENCY_BINDING=PASS
G5_B_DIRECT_PYTHON_MCP_HTTP_PROBE=PASS
G5_C_REAL_GEMINI_ADK_GRAFANA_TRAJECTORY=PASS_PREVIOUS_BUILD
G5_D_REAL_GRAFANA_EVIDENCE=PASS_PREVIOUS_BUILD
G5_E_STRUCTURED_PROPOSAL=REVALIDATION_REQUIRED
G5_F_AUTHORITY_BOUNDARY=PASS_PREVIOUS_BUILD
G5_G_REGRESSION=PENDING_CURRENT_HEAD
NEXT_GATE=POSTCONDITION_CONTRACT_REGRESSION_THEN_REAL_RUNTIME_RERUN
```

The Phase 5 branch must remain unmerged until the stronger proposal contract is proven by a fresh real runtime readback.
