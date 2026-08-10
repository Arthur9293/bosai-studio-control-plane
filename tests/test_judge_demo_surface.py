import unittest

from bosai_studio.judge_demo_surface import LOCKED_THESIS, WORKFLOW, proof_summary, render_demo_html


class JudgeDemoSurfaceTests(unittest.TestCase):
    def test_locked_thesis_and_workflow_are_visible(self) -> None:
        html = render_demo_html()
        self.assertIn(LOCKED_THESIS, html)
        self.assertIn(WORKFLOW, html)
        self.assertIn("OBSERVE", html)
        self.assertIn("PROVE", html)

    def test_demo_contains_required_authority_claims(self) -> None:
        html = render_demo_html()
        required = [
            "Gemini proposes only",
            "BOSAI deterministic executor",
            "Firestore authority state",
            "Cloud Run / IAM enforced",
            "QC bypass is denied",
            "studio-control-plane → authority-executor → media-pipeline-sim",
            "studio-control-plane ↛ media-pipeline-sim",
        ]
        for text in required:
            self.assertIn(text, html)

    def test_summary_does_not_claim_public_url_or_customer_workload(self) -> None:
        summary = proof_summary()
        self.assertFalse(summary["public_url_claimed"])
        self.assertFalse(summary["customer_workload_claimed"])
        self.assertFalse(summary["secret_values_expected"])
        self.assertFalse(summary["identity_tokens_expected"])
        self.assertTrue(summary["unsupported_claims_absent"])

    def test_demo_avoids_secret_markers(self) -> None:
        html = render_demo_html().lower()
        forbidden = ["bearer ", "sk-", "grafana_service_account_token", "otel_exporter_otlp_headers"]
        for marker in forbidden:
            self.assertNotIn(marker, html)


if __name__ == "__main__":
    unittest.main()
