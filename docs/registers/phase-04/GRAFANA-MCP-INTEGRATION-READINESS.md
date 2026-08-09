# BOSAI Studio Control Plane — Phase 4 Grafana MCP Integration Readiness

Status: **PARTIAL — READY_FOR_GRAFANA_CREDENTIAL_BINDING**  
Issue: **#8 — PHASE 4 — Grafana MCP Integration**  
Topology mode: **ISOLATE**  
Base branch: `air`  
Base SHA: `014a839bf165727ac532f725b5985f523f751fa8`  
Working branch: `phase/04-grafana-mcp-integration`  
Prepared-code head before this register: `442df2eee5175fac133dc25f21f642789c70bc94`

---

## 1. Phase decision

Phase 4 is **not PASS yet**.

The repository now contains the bounded instrumentation and read-only MCP client/runtime preparation required to perform a real Grafana Cloud integration, but no Grafana Cloud credential has been bound and no real Grafana MCP query has been observed in this phase.

Therefore:

- `GRAFANA_OTLP_CODE_READY=true`
- `OFFICIAL_MCP_GRAFANA_CONFIG_READY=true`
- `MCP_READ_ONLY_ENFORCED_BY_CONFIG=true`
- `REAL_GRAFANA_OTLP_INGESTION_PROVEN=false`
- `REAL_MCP_GRAFANA_HEALTH_PROVEN=false`
- `REAL_MCP_GRAFANA_QUERY_PROVEN=false`
- `PHASE_4_PASS=false`

No synthetic/fake MCP result may satisfy the missing runtime gates.

---

## 2. Official integration contract revalidated

Primary sources:

- Devpost Grafana resources: `https://agentic-cinema.devpost.com/details/grafana-resources`
- Grafana MCP docs: `https://grafana.com/docs/grafana/latest/developer-resources/mcp/`
- Grafana MCP read-only flags: `https://grafana.com/docs/grafana/latest/developer-resources/mcp/configure/command-line-flags/`
- Grafana Cloud OTLP: `https://grafana.com/docs/grafana-cloud/send-data/otlp/`
- Grafana Cloud OTel setup: `https://grafana.com/docs/opentelemetry/grafana-cloud/`
- Official MCP repository: `https://github.com/grafana/mcp-grafana`

The track requires active Grafana runtime use, primarily through the official Grafana MCP server or hosted Grafana Cloud MCP endpoint. AI Observability alone is not sufficient.

For our unattended architecture, the target remains the open-source official MCP server authenticated to Grafana Cloud by service-account token.

Current pinned MCP release for this phase: **`mcp-grafana v1.0.0`** / Docker image **`grafana/mcp-grafana:1.0.0`**.

Initial runtime mode: **read-only** via `--disable-write`.

---

## 3. Implemented Phase 4 surface

### OpenTelemetry runtime

`src/bosai_studio/telemetry.py`

- OpenTelemetry resource identifies `service.name=bosai-studio-media-pipeline`.
- Workload is explicitly labelled `bosai.synthetic=true`.
- Emits traces, logs, a pipeline event counter, and transcode-latency histogram.
- Uses OTLP HTTP/protobuf exporters.
- Reads standard `OTEL_EXPORTER_OTLP_*` environment variables.
- Fails closed when `OTEL_EXPORTER_OTLP_ENDPOINT` is absent.
- No Grafana secret enters a Python object as a literal or committed value.

### Governed telemetry source

`src/bosai_studio/observed_pipeline.py`

Telemetry is attached to the actual Phase 3 governed pipeline mutation path. It observes:

- `TRANSCODE_A_CODEC_INIT_TIMEOUT`
- `TRANSCODE_A_RESTARTED_DEGRADED`
- `WORKLOAD_REROUTED_TO_HEALTHY_CAPACITY`
- `QC_REQUIRED_AFTER_LATEST_TRANSFORM`

The target demo QC-bypass remains denied by BOSAI, so an executed `QC_VALIDATION_DISABLED` event is not generated during the winning path.

### End-to-end telemetry scenario

`src/bosai_studio/telemetry_scenario.py`

The scenario calls the existing deterministic `AuthorityExecutor` and drives:

`incident → governed restart → denied QC bypass → governed reroute → OTLP flush`

Thus Grafana telemetry will be produced from the same governed state transitions used by the product thesis rather than from detached demo log fixtures.

### MCP client/readback

`scripts/mcp_stdio_readback.py`

- Minimal JSON-RPC MCP stdio client.
- Performs `initialize` + `notifications/initialized` + `tools/list`.
- Can describe an advertised tool and its `inputSchema` before calling it.
- Refuses to launch without `GRAFANA_URL` and `GRAFANA_SERVICE_ACCOUNT_TOKEN`.
- Default server command uses `mcp-grafana -t stdio --disable-write`.
- Optional tool calls use only the argument object supplied after schema discovery.

Tool-schema discovery is required before the first real query so Phase 4 does not guess the `query_loki_logs` v1.0.0 input contract.

### Official MCP container preparation

`ops/run_mcp_grafana_readonly.sh`

- Pins `grafana/mcp-grafana:1.0.0`.
- Binds HTTP exposure only on `127.0.0.1:8000` for the local smoke environment.
- Uses `-t streamable-http --disable-write --metrics`.
- Credentials are inherited only from process environment.

### Secret contract

`ops/grafana.env.example`

Contains placeholders only for:

- `GRAFANA_URL`
- `GRAFANA_SERVICE_ACCOUNT_TOKEN`
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_HEADERS`

`.gitignore` rejects local `.env`, token/key files, Python caches and virtual environments.

---

## 4. Dependency / compliance status

Phase 4 adds only non-AI OpenTelemetry runtime libraries:

- `opentelemetry-sdk>=1.42,<2`
- `opentelemetry-exporter-otlp-proto-http>=1.42,<2`

Devpost's restriction applies to AI/agent tooling; ordinary non-AI third-party libraries/services remain permitted.

Current Phase 4 AI state:

- `OpenAI=false`
- `Anthropic=false`
- `AWS_AI=false`
- `Microsoft_AI=false`
- `non_Google_agent_framework=false`
- `Gemini=false` — intentionally deferred to Phase 5
- `Google_ADK=false` — intentionally deferred to Phase 5

---

## 5. Local preparation evidence

The Phase 4 instrumentation was locally exercised before publication:

- telemetry contract test suite: **4 PASS**;
- Python compilation checks for telemetry/runtime/readback modules: **PASS**;
- in-memory OpenTelemetry smoke proves trace + metric + log emission without external network;
- no-endpoint test proves real OTLP export fails closed;
- MCP stdio client protocol was smoke-tested against a fake local MCP process only to validate client framing.

The fake MCP process is explicitly **NOT Grafana evidence** and cannot satisfy any Phase 4 exit criterion.

Phase 3 source files were not changed by this phase. A full Phase 3 regression re-run after dependency binding remains required before Phase 4 closure.

---

## 6. Real Grafana evidence contract

Phase 4 may be closed only after all of the following are read back:

### Gate G4-A — OTLP binding

Required:

- real Grafana Cloud stack selected;
- `OTEL_EXPORTER_OTLP_ENDPOINT` obtained from Grafana Cloud;
- `OTEL_EXPORTER_OTLP_HEADERS` generated/stored outside Git;
- governed telemetry scenario exports successfully;
- Grafana shows BOSAI telemetry.

Expected Loki service selector after native OTLP mapping:

`{service_name="bosai-studio-media-pipeline"}`

Initial target log content:

`TRANSCODE_A_CODEC_INIT_TIMEOUT`

### Gate G4-B — MCP authentication

Required:

- `GRAFANA_URL` bound to selected stack;
- Grafana service account/token stored outside Git;
- official `mcp-grafana v1.0.0` starts in read-only mode;
- `/healthz` returns HTTP 200 `ok` for HTTP transport OR stdio initialization advertises official server metadata.

### Gate G4-C — real MCP readback

Required sequence:

1. initialize official MCP server;
2. `tools/list`;
3. describe `query_loki_logs` and record its advertised `inputSchema`;
4. construct arguments from that schema — no guessed keys;
5. invoke `query_loki_logs` against the real Grafana Cloud Loki datasource;
6. result contains BOSAI-generated telemetry from this phase;
7. sanitize any identifiers before committing evidence.

A second query (Prometheus or Tempo) is desirable later but is **not required** for the first Phase 4 PASS gate.

---

## 7. Missing external authority / credentials

No Grafana Cloud stack URL, OTLP credential, or Grafana service-account token is present in the connected tools or repository.

The assistant cannot fabricate or infer these values.

Required human credential actions must occur in the user's Grafana Cloud account. Secrets must never be pasted into GitHub or committed to this repository.

The first external gate is **OTLP credential binding**. MCP service-account creation follows after telemetry ingestion is proven.

---

## 8. Accidental preflight object

During Phase 4 preflight, Draft PR #7 was accidentally created from the already-merged Phase 3 branch.

It was immediately renamed `CANCELLED — preflight no-op` and closed without merge.

- `PR_7_MERGED=false`
- `CANONICAL_AIR_CHANGED_BY_PR_7=false`
- `PHASE_4_SCOPE_IMPACT=false`

It is retained as transparent audit history rather than hidden.

---

## 9. Phase 4 current status

```text
PHASE_4=PARTIAL
PHASE_4_CODE_PREPARATION=PASS
PHASE_4_SECRET_HYGIENE=PASS
PHASE_4_REAL_GRAFANA_OTLP=NOT_YET_PROVEN
PHASE_4_REAL_MCP_GRAFANA=NOT_YET_PROVEN
PHASE_4_REAL_MCP_QUERY=NOT_YET_PROVEN
NEXT_GATE=G4_A_OTLP_CREDENTIAL_BINDING
```

The Phase 4 branch must remain unmerged until the real Grafana runtime evidence exists.
