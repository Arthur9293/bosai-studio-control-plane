from __future__ import annotations

import unittest

from bosai_studio.cloud_run_phase9 import (
    AUTHORITY_SERVICE,
    DEFAULT_PHASE9_REGION,
    PHASE9_HUMAN_GO,
    PHASE9_ROLLBACK_HUMAN_GO,
    PIPELINE_SERVICE,
    STUDIO_SERVICE,
    deployment_human_go_valid,
    phase9_deployment_plan,
    rollback_human_go_valid,
)


class Phase9CloudRunDeploymentContractTests(unittest.TestCase):
    def test_human_go_phrase_is_exact_for_deployment(self) -> None:
        self.assertTrue(deployment_human_go_valid(PHASE9_HUMAN_GO))
        self.assertFalse(deployment_human_go_valid(None))
        self.assertFalse(deployment_human_go_valid("GO PHASE 9"))
        self.assertFalse(deployment_human_go_valid("HUMAN GO PHASE 9"))

    def test_rollback_phrase_is_distinct_from_deployment_phrase(self) -> None:
        self.assertTrue(rollback_human_go_valid(PHASE9_ROLLBACK_HUMAN_GO))
        self.assertFalse(rollback_human_go_valid(PHASE9_HUMAN_GO))

    def test_plan_contains_expected_services_and_accounts(self) -> None:
        plan = phase9_deployment_plan("bosai-gemini-xprize", DEFAULT_PHASE9_REGION)
        self.assertEqual(plan["project_id"], "bosai-gemini-xprize")
        service_accounts = plan["service_accounts"]
        self.assertIn(STUDIO_SERVICE, service_accounts)
        self.assertIn(AUTHORITY_SERVICE, service_accounts)
        self.assertIn(PIPELINE_SERVICE, service_accounts)
        self.assertEqual(len(set(service_accounts.values())), 3)

    def test_plan_has_only_two_allowed_invoker_bindings(self) -> None:
        plan = phase9_deployment_plan("bosai-gemini-xprize")
        bindings = plan["allowed_invoker_bindings"]
        self.assertEqual(len(bindings), 2)
        targets = {(binding["caller"].split("@")[0], binding["target"]) for binding in bindings}
        self.assertIn(("sa-studio-control-plane", AUTHORITY_SERVICE), targets)
        self.assertIn(("sa-authority-executor", PIPELINE_SERVICE), targets)
        self.assertNotIn(("sa-studio-control-plane", PIPELINE_SERVICE), targets)

    def test_private_services_are_not_publicly_unauthenticated(self) -> None:
        plan = phase9_deployment_plan("bosai-gemini-xprize")
        services = {service["name"]: service for service in plan["services"]}
        self.assertTrue(services[STUDIO_SERVICE]["allow_unauthenticated"])
        self.assertFalse(services[AUTHORITY_SERVICE]["allow_unauthenticated"])
        self.assertFalse(services[PIPELINE_SERVICE]["allow_unauthenticated"])

    def test_plan_starts_with_runtime_proof_unclaimed(self) -> None:
        plan = phase9_deployment_plan("bosai-gemini-xprize")
        self.assertFalse(plan["deployment_authorized_by_required_phrase"])
        self.assertFalse(plan["runtime_iam_enforcement_proven"])


if __name__ == "__main__":
    unittest.main()
