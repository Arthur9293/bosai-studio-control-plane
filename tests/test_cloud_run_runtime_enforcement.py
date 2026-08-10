import unittest

from bosai_studio.cloud_run_boundary import ServiceName
from bosai_studio.cloud_run_runtime_enforcement import (
    HUMAN_GO_VALUE,
    RuntimeProofStatus,
    deployment_commands,
    require_human_go,
    runtime_enforcement_plan,
    service_accounts,
)


class CloudRunRuntimeEnforcementTests(unittest.TestCase):
    def test_human_go_exact_phrase_is_required(self) -> None:
        with self.assertRaises(RuntimeError):
            require_human_go(None)
        with self.assertRaises(RuntimeError):
            require_human_go("GO")
        require_human_go(HUMAN_GO_VALUE)

    def test_service_accounts_are_distinct(self) -> None:
        accounts = service_accounts("bosai-gemini-xprize")
        self.assertEqual(len(accounts), 3)
        self.assertEqual(len(set(accounts.values())), 3)
        self.assertIn(ServiceName.STUDIO_CONTROL_PLANE.value, accounts)
        self.assertIn(ServiceName.AUTHORITY_EXECUTOR.value, accounts)
        self.assertIn(ServiceName.MEDIA_PIPELINE_SIM.value, accounts)

    def test_plan_starts_unproven_until_runtime_probe_passes(self) -> None:
        plan = runtime_enforcement_plan("bosai-gemini-xprize", "global")
        self.assertEqual(plan["status"], RuntimeProofStatus.PREPARED_ONLY.value)
        self.assertFalse(plan["runtime_iam_enforcement_proven"])
        self.assertFalse(plan["secrets_expected_in_output"])

    def test_deployment_commands_are_explicitly_mutating_or_read_only(self) -> None:
        commands = deployment_commands("bosai-gemini-xprize", "global")
        self.assertGreaterEqual(len(commands), 8)
        self.assertTrue(any(command.mutates_cloud for command in commands))
        self.assertTrue(any(not command.mutates_cloud for command in commands))
        command_names = {command.name for command in commands}
        self.assertIn("allow-studio-to-invoke-authority", command_names)
        self.assertIn("allow-authority-to-invoke-pipeline", command_names)
        self.assertNotIn("allow-studio-to-invoke-pipeline", command_names)

    def test_runtime_edges_match_expected_positive_and_negative_proofs(self) -> None:
        plan = runtime_enforcement_plan("bosai-gemini-xprize", "global")
        allowed = {(edge["caller"], edge["target"]) for edge in plan["allowed_runtime_edges"]}
        denied = {(edge["caller"], edge["target"]) for edge in plan["denied_runtime_edges"]}

        self.assertIn(("studio-control-plane", "authority-executor"), allowed)
        self.assertIn(("authority-executor", "media-pipeline-sim"), allowed)
        self.assertIn(("studio-control-plane", "media-pipeline-sim"), denied)
        self.assertIn(("public-internet", "authority-executor"), denied)
        self.assertIn(("public-internet", "media-pipeline-sim"), denied)
        self.assertNotIn(("studio-control-plane", "media-pipeline-sim"), allowed)


if __name__ == "__main__":
    unittest.main()
