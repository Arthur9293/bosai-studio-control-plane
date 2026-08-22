import unittest

from bosai_studio.judge_demo_surface import (
    CONTEST_REPOSITORY_CREATED_AT,
    HOSTED_SURFACE_URL,
    LOCKED_THESIS,
    WORKFLOW,
    proof_summary,
    render_demo_html,
)


class JudgeDemoSurfaceTests(unittest.TestCase):
    def test_locked_thesis_and_workflow_are_visible(self) -> None:
        html = render_demo_html()
        self.assertIn(LOCKED_THESIS, html)
        self.assertIn(WORKFLOW, html)
        self.assertIn("OBSERVE", html)
        self.assertIn("PROVE", html)

    def test_demo_contains_required_authority_and_partner_claims(self) -> None:
        html = render_demo_html()
        required = [
            "Gemini proposes only",
            "BOSAI deterministic executor",
            "Firestore authority state",
            "Cloud Run / IAM enforced",
            "Grafana Cloud + official MCP",
            "QC bypass is denied",
            "studio-control-plane → authority-executor → media-pipeline-sim",
            "studio-control-plane ↛ media-pipeline-sim",
            "IBM Bob — development-process partner",
            "Contest-built clean-room implementation",
        ]
        for text in required:
            self.assertIn(text, html)

    def test_interactive_replay_is_explicitly_non_live(self) -> None:
        html = render_demo_html()
        required = [
            "Recorded evidence replay",
            "Run governed restart",
            "Try unsafe QC bypass",
            "Try permit replay",
            "This surface does not call live cloud services",
            "no customer production workload",
        ]
        for text in required:
            self.assertIn(text, html)

    def test_summary_matches_current_public_contest_state(self) -> None:
        summary = proof_summary()
        self.assertTrue(summary["public_url_claimed"])
        self.assertEqual(summary["hosted_surface_url"], HOSTED_SURFACE_URL)
        self.assertTrue(summary["interactive_replay"])
        self.assertFalse(summary["live_cloud_mutation"])
        self.assertFalse(summary["customer_workload_claimed"])
        self.assertFalse(summary["secret_values_expected"])
        self.assertFalse(summary["identity_tokens_expected"])
        self.assertTrue(summary["unsupported_claims_absent"])
        self.assertTrue(summary["contest_clean_room_claimed"])
        self.assertEqual(summary["contest_repository_created_at"], CONTEST_REPOSITORY_CREATED_AT)
        self.assertEqual(len(summary["replay_scenarios"]), 3)

    def test_demo_avoids_secret_markers(self) -> None:
        html = render_demo_html().lower()
        forbidden = ["bearer ", "sk-", "grafana_service_account_token", "otel_exporter_otlp_headers"]
        for marker in forbidden:
            self.assertNotIn(marker, html)


if __name__ == "__main__":
    unittest.main()
