# BOSAI Studio Control Plane — Phase 5 Gemini Agent Loop Readiness

Status: **PARTIAL — READY_FOR_VERTEX_AI_AUTH_BINDING**  
Issue: **#10 — PHASE 5 — Gemini Agent Loop**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `aff85d6118f6b9dbe2cf37c6dbc9c5dee13beeee`  
Working branch: `phase/05-gemini-agent-loop`

---

## 1. Phase decision

Phase 5 is not PASS yet.

The repository now contains the bounded Google ADK/Gemini agent surface required for the first real reasoning loop, but no Vertex AI credential/project binding or real Gemini invocation has yet been read back.

Therefore:

```text
PHASE_5_CODE_PREPARATION=PASS
VERTEX_AI_AUTH_PROVEN=false
REAL_GEMINI_INVOCATION_PROVEN=false
REAL_GEMINI_GRAFANA_MCP_TOOL_USE_PROVEN=false
STRUCTURED_PROPOSAL_RUNTIME_PROVEN=false
PHASE_5=PARTIAL
```

No mocked model response may satisfy the missing runtime gates.

---

## 2. Current Google runtime contract

Primary official references:

- ADK: `https://adk.dev/`
- ADK Python quickstart: `https://adk.dev/get-started/python/`
- ADK MCP tools: `https://adk.dev/tools/mcp-tools/`
- Vertex AI Gemini quickstart: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart`
- Vertex AI release notes: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes`
- Google ADK PyPI: `https://pypi.org/project/google-adk/`

Pinned Phase 5 runtime dependency:

`google-adk[mcp]==2.5.0`

Model target:

`gemini-2.5-flash`

Reason for the model choice:

- Google-hosted Gemini model;
- generally available on Vertex AI;
- sufficient reasoning/tool-use capability for the incident investigator;
- current published retirement date is after the 7 September 2026 hackathon deadline.

Vertex AI mode is mandatory in Phase 5:

`GOOGLE_GENAI_USE_VERTEXAI=true`

The runtime rejects missing Vertex AI project/location configuration.

---

## 3. Agent authority boundary

Gemini receives only one external tool:

`query_loki_logs`

through Google ADK `McpToolset` connected over stdio to:

`grafana/mcp-grafana:1.0.0 -t stdio --disable-write`

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

This enforces the Phase 5 form of:

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

Extra fields are rejected.

A model output containing `authority_decision=AUTHORIZED` or an invented `permit_id` fails deterministic schema validation.

Conversion only creates a `Proposal`; it does not call BOSAI authority evaluation or execution.

---

## 5. Target real trajectory

User/incident input:

`FINAL_TRAILER_DELIVERY_SLA_AT_RISK / incident-demo-001`

Expected runtime trajectory:

```text
Gemini / ADK
  -> query_loki_logs via official Grafana MCP
  -> real Loki response
  -> reason from observed incident evidence
  -> raw JSON proposal
  -> deterministic AgentProposalEnvelope validation
  -> BOSAI Proposal
  -> STOP
```

For the current Phase 4 telemetry, the expected first proposal is normally:

```text
action=RESTART_TRANSCODE_WORKER
target=transcode-a
authority_decision=NOT_EVALUATED
```

A different proposal is not automatically treated as failure if its reasoning is grounded in real Grafana evidence; it must be reviewed rather than retrofitted to the expected result.

---

## 6. Runtime evidence required

Phase 5 closure requires a real runner readback proving:

1. Vertex AI authentication succeeds.
2. Gemini responds from the configured Google model.
3. ADK trajectory contains `query_loki_logs`.
4. No non-allowlisted tool is invoked.
5. Final Gemini response validates against `AgentProposalEnvelope`.
6. `authority_decision=NOT_EVALUATED`.
7. `authority_engine_invoked=false`.
8. `permit_issued=false`.
9. `mutation_attempted=false`.
10. Repository tests remain green after ADK dependency binding.

---

## 7. External gate

The repository currently contains no Google Cloud project ID, Application Default Credential, or service-account secret.

Required local/development setup must occur outside Git:

- select/create an admissible Google Cloud project;
- enable Vertex AI API;
- configure Application Default Credentials for local smoke testing;
- export `GOOGLE_CLOUD_PROJECT`;
- export `GOOGLE_CLOUD_LOCATION=global`;
- export `GOOGLE_GENAI_USE_VERTEXAI=true`.

No credential JSON or access token may be committed.

---

## 8. Current closure state

```text
PHASE_5=PARTIAL
PHASE_5_CODE_PREPARATION=PASS
PHASE_5_TOOL_BOUNDARY=PASS_BY_CODE_REVIEW
PHASE_5_STRUCTURED_CONTRACT=PASS_BY_CODE_REVIEW
REAL_VERTEX_AI=false
REAL_GEMINI=false
REAL_ADK_MCP_TRAJECTORY=false
NEXT_GATE=G5_A_GOOGLE_CLOUD_AUTH_AND_DEPENDENCY_BINDING
```

The Phase 5 branch must remain unmerged until real Gemini + ADK + Grafana MCP evidence and regression tests exist.
