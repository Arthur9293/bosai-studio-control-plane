from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from bosai_studio.agent_contracts import AgentProposalEnvelope
from bosai_studio.contracts import Action
from bosai_studio.gemini_agent import GRAFANA_TOOL_ALLOWLIST, MUTATION_TOOLS_EXPOSED, _same_origin
from bosai_studio.gemini_config import load_gemini_runtime_config
from scripts.gemini_agent_readback import _extract_json_payload


VALID_OUTPUT = {
    "proposal_id": "proposal-gemini-001",
    "incident_id": "incident-demo-001",
    "action": "RESTART_TRANSCODE_WORKER",
    "target": "transcode-a",
    "reason": "Grafana shows a codec initialization timeout on the primary transcode worker.",
    "evidence_refs": ["grafana:loki:TRANSCODE_A_CODEC_INIT_TIMEOUT"],
    "expected_postconditions": ["transcode-a health improves"],
    "authority_decision": "NOT_EVALUATED",
    "proposal_only": True,
}


class GeminiProposalContractTests(unittest.TestCase):
    def test_valid_model_output_converts_to_domain_proposal_without_authority(self) -> None:
        envelope = AgentProposalEnvelope.model_validate(VALID_OUTPUT)
        proposal = envelope.to_domain_proposal()
        self.assertEqual(proposal.action, Action.RESTART_TRANSCODE_WORKER)
        self.assertEqual(proposal.target, "transcode-a")
        self.assertEqual(envelope.authority_decision, "NOT_EVALUATED")
        self.assertTrue(envelope.proposal_only)

    def test_model_cannot_claim_authorized(self) -> None:
        invalid = dict(VALID_OUTPUT)
        invalid["authority_decision"] = "AUTHORIZED"
        with self.assertRaises(ValidationError):
            AgentProposalEnvelope.model_validate(invalid)

    def test_model_cannot_add_hidden_fields(self) -> None:
        invalid = dict(VALID_OUTPUT)
        invalid["permit_id"] = "permit-model-invented"
        with self.assertRaises(ValidationError):
            AgentProposalEnvelope.model_validate(invalid)

    def test_agent_tool_surface_is_read_only_and_minimal(self) -> None:
        self.assertEqual(GRAFANA_TOOL_ALLOWLIST, ("query_loki_logs",))
        self.assertEqual(MUTATION_TOOLS_EXPOSED, ())
        self.assertNotIn("execute", GRAFANA_TOOL_ALLOWLIST)
        self.assertNotIn("restart", GRAFANA_TOOL_ALLOWLIST)
        self.assertNotIn("reroute", GRAFANA_TOOL_ALLOWLIST)

    def test_markdown_json_fence_is_tolerated_but_commentary_is_not(self) -> None:
        raw = '{"proposal_only":true}'
        payload, fenced = _extract_json_payload(raw)
        self.assertEqual(payload, raw)
        self.assertFalse(fenced)

        fenced_payload, fenced = _extract_json_payload(f"```json\n{raw}\n```")
        self.assertEqual(fenced_payload, raw)
        self.assertTrue(fenced)

        with self.assertRaisesRegex(RuntimeError, "standalone JSON object"):
            _extract_json_payload(f"Here is the result:\n{raw}")

    def test_same_origin_is_derived_without_path(self) -> None:
        self.assertEqual(_same_origin("http://127.0.0.1:8010/mcp"), "http://127.0.0.1:8010")
        self.assertEqual(_same_origin("https://mcp.example.com/path"), "https://mcp.example.com")
        with self.assertRaisesRegex(RuntimeError, "invalid Grafana MCP URL"):
            _same_origin("not-a-url")


class GeminiRuntimeConfigTests(unittest.TestCase):
    def test_vertex_ai_mode_is_required(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GOOGLE_GENAI_USE_VERTEXAI=true"):
                load_gemini_runtime_config()

    def test_runtime_config_uses_local_mcp_without_grafana_secrets(self) -> None:
        env = {
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_CLOUD_PROJECT": "bosai-hackathon-project",
            "GOOGLE_CLOUD_LOCATION": "global",
            "GRAFANA_URL": "https://example.grafana.net",
            "GRAFANA_SERVICE_ACCOUNT_TOKEN": "secret-value",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_gemini_runtime_config()

        self.assertEqual(config.model, "gemini-2.5-flash")
        self.assertEqual(config.loki_datasource_uid, "grafanacloud-logs")
        self.assertEqual(config.grafana_mcp_url, "http://127.0.0.1:8010/mcp")
        self.assertFalse(hasattr(config, "grafana_service_account_token"))
        self.assertNotIn("secret-value", repr(config))

    def test_local_mcp_url_can_be_overridden_without_credentials(self) -> None:
        env = {
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_CLOUD_PROJECT": "bosai-hackathon-project",
            "GOOGLE_CLOUD_LOCATION": "global",
            "BOSAI_GRAFANA_MCP_URL": "http://localhost:8123/mcp",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_gemini_runtime_config()

        self.assertEqual(config.grafana_mcp_url, "http://localhost:8123/mcp")


if __name__ == "__main__":
    unittest.main()
