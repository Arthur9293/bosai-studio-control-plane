from __future__ import annotations

import unittest

from bosai_studio.cloud_run_boundary import (
    AUTHORITY_IDENTITY,
    PIPELINE_IDENTITY,
    STUDIO_IDENTITY,
    CANONICAL_CLOUD_RUN_SERVICES,
    CloudRunBoundaryContract,
    ServiceName,
    cloud_run_plan,
    service_account_map,
)


class CloudRunBoundaryContractTests(unittest.TestCase):
    def test_canonical_service_accounts_are_distinct_and_project_scoped(self) -> None:
        mapping = service_account_map("bosai-gemini-xprize")
        self.assertEqual(
            mapping[ServiceName.STUDIO_CONTROL_PLANE.value],
            "sa-studio-control-plane@bosai-gemini-xprize.iam.gserviceaccount.com",
        )
        self.assertEqual(
            mapping[ServiceName.AUTHORITY_EXECUTOR.value],
            "sa-authority-executor@bosai-gemini-xprize.iam.gserviceaccount.com",
        )
        self.assertEqual(
            mapping[ServiceName.MEDIA_PIPELINE_SIM.value],
            "sa-media-pipeline-sim@bosai-gemini-xprize.iam.gserviceaccount.com",
        )
        self.assertEqual(len(set(mapping.values())), 3)
        self.assertNotEqual(STUDIO_IDENTITY.account_id, AUTHORITY_IDENTITY.account_id)
        self.assertNotEqual(AUTHORITY_IDENTITY.account_id, PIPELINE_IDENTITY.account_id)

    def test_only_expected_service_to_service_invocation_edges_are_allowed(self) -> None:
        contract = CloudRunBoundaryContract()
        self.assertTrue(
            contract.is_allowed(ServiceName.STUDIO_CONTROL_PLANE, ServiceName.AUTHORITY_EXECUTOR)
        )
        self.assertTrue(
            contract.is_allowed(ServiceName.AUTHORITY_EXECUTOR, ServiceName.MEDIA_PIPELINE_SIM)
        )

        self.assertFalse(
            contract.is_allowed(ServiceName.STUDIO_CONTROL_PLANE, ServiceName.MEDIA_PIPELINE_SIM)
        )
        self.assertFalse(
            contract.is_allowed(ServiceName.GEMINI_ADK, ServiceName.MEDIA_PIPELINE_SIM)
        )
        self.assertFalse(
            contract.is_allowed(ServiceName.MCP_GRAFANA, ServiceName.MEDIA_PIPELINE_SIM)
        )
        self.assertFalse(
            contract.is_allowed(ServiceName.PUBLIC_INTERNET, ServiceName.AUTHORITY_EXECUTOR)
        )
        self.assertFalse(
            contract.is_allowed(ServiceName.PUBLIC_INTERNET, ServiceName.MEDIA_PIPELINE_SIM)
        )

    def test_undeclared_edges_fail_closed(self) -> None:
        decision = CloudRunBoundaryContract().decide(
            ServiceName.MEDIA_PIPELINE_SIM,
            ServiceName.AUTHORITY_EXECUTOR,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, "EDGE_NOT_DECLARED_FAIL_CLOSED")

    def test_private_services_are_not_configured_for_unauthenticated_public_access(self) -> None:
        by_name = {spec.service: spec for spec in CANONICAL_CLOUD_RUN_SERVICES}
        self.assertTrue(by_name[ServiceName.STUDIO_CONTROL_PLANE].allow_unauthenticated)
        self.assertFalse(by_name[ServiceName.AUTHORITY_EXECUTOR].allow_unauthenticated)
        self.assertFalse(by_name[ServiceName.MEDIA_PIPELINE_SIM].allow_unauthenticated)
        self.assertEqual(
            by_name[ServiceName.AUTHORITY_EXECUTOR].ingress,
            "internal-and-cloud-load-balancing",
        )
        self.assertEqual(
            by_name[ServiceName.MEDIA_PIPELINE_SIM].ingress,
            "internal-and-cloud-load-balancing",
        )

    def test_plan_is_readiness_only_until_real_runtime_iam_is_proven(self) -> None:
        plan = cloud_run_plan("bosai-gemini-xprize", "europe-west1")
        self.assertEqual(plan["project_id"], "bosai-gemini-xprize")
        self.assertEqual(plan["region"], "europe-west1")
        self.assertFalse(plan["deployment_authorized"])
        self.assertFalse(plan["runtime_iam_enforcement_proven"])
        self.assertEqual(len(plan["allowed_invocations"]), 2)
        self.assertGreaterEqual(len(plan["denied_invocations"]), 5)


if __name__ == "__main__":
    unittest.main()
