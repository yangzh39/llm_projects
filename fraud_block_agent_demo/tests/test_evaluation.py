import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from deepseek_intent import ApiCallBudget, ApiCallLimitExceeded  # noqa: E402
from evaluation.benchmark import load_scenarios  # noqa: E402
from evaluation.graders.code_checks import evaluate_code_checks  # noqa: E402
from evaluation.graders.trace_checks import evaluate_trace_checks  # noqa: E402
from evaluation.harness import run_scenario  # noqa: E402
from evaluation.metrics import calculate_api_cost  # noqa: E402


class EvaluationPipelineTests(unittest.TestCase):
    def test_successful_scenario_passes(self):
        report = run_scenario("successful_block_removal", save_output=False)
        self.assertEqual("PASS", report["overall_result"])
        self.assertTrue(all(check["status"] == "PASS" for check in report["code_checks"]))
        self.assertTrue(all(check["status"] == "PASS" for check in report["trace_checks"]))

    def test_suspected_fraud_transfers_without_authentication(self):
        report = run_scenario("suspected_fraud", save_output=False)
        names = [event["name"] for event in report["trace"]]
        self.assertIn("specialist_transfer_triggered", names)
        self.assertNotIn("authentication_attempt", names)
        self.assertEqual("PASS", report["overall_result"])

    def test_authentication_failure_prevents_account_lookup(self):
        report = run_scenario("authentication_failure_wrong_dob", save_output=False)
        names = [event["name"] for event in report["trace"]]
        self.assertIn("authentication_failed", names)
        self.assertNotIn("ownership_verified", names)
        self.assertNotIn("get_customer_cards", names)
        self.assertNotIn("block_removed", names)

    def test_transaction_not_recognized_prevents_removal(self):
        report = run_scenario("transaction_not_recognized", save_output=False)
        names = [event["name"] for event in report["trace"]]
        self.assertIn("transaction_not_recognized", names)
        self.assertIn("specialist_transfer_triggered", names)
        self.assertNotIn("block_removed", names)

    def test_final_state_check_catches_incorrect_database_state(self):
        report = run_scenario("successful_block_removal", save_output=False)
        scenario = load_scenarios()["successful_block_removal"]
        expected = {**scenario["expected"], "initial_card_id": "CARD-001"}
        checks = evaluate_code_checks(report["trace"], expected, {"CARD-001": "fraud_blocked"})
        final_check = next(check for check in checks if check["name"] == "final_card_status")
        self.assertEqual("FAIL", final_check["status"])

    def test_trace_check_catches_incorrect_order(self):
        trace = [
            {"name": "route_selected", "output": {}},
            {"name": "authentication_success", "output": {}},
            {"name": "ownership_verified", "output": {}},
            {"name": "transaction_retrieved", "output": {}},
            {"name": "transaction_recognized", "output": {"transaction_id": "TX"}},
            {"name": "block_removed", "output": {}},
            {"name": "eligibility_approved", "output": {}},
            {"name": "final_state_verified", "output": {}},
        ]
        checks = evaluate_trace_checks(trace, {"block_removed": True})
        ordering = next(check for check in checks if check["name"] == "order:eligibility_approved_before_block_removed")
        self.assertEqual("FAIL", ordering["status"])

    def test_hidden_failure_passes_code_checks_but_fails_trace(self):
        report = run_scenario("hidden_workflow_failure", save_output=False)
        self.assertTrue(all(check["status"] == "PASS" for check in report["code_checks"]))
        self.assertTrue(any(check["status"] == "FAIL" for check in report["trace_checks"]))
        self.assertEqual("FAIL", report["overall_result"])

    def test_sensitive_credentials_are_absent_from_trace(self):
        report = run_scenario("authentication_failure_card_dob_mismatch", save_output=False)
        serialized = json.dumps(report["trace"])
        self.assertNotIn("9000000000001001", serialized)
        self.assertNotIn("1985-02-20", serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_every_trace_event_has_required_structured_fields(self):
        report = run_scenario("successful_block_removal", save_output=False)
        required = {"sequence", "timestamp", "event_type", "name", "status", "input", "output", "duration_ms"}
        for event in report["trace"]:
            self.assertTrue(required.issubset(event), event)

    def test_benchmark_resets_state_between_scenarios(self):
        first = run_scenario("successful_block_removal", save_output=False)
        second = run_scenario("successful_block_removal", save_output=False)
        self.assertEqual("fraud_blocked", first["agent_result"]["initial_card_state"]["CARD-001"])
        self.assertEqual("fraud_blocked", second["agent_result"]["initial_card_state"]["CARD-001"])
        self.assertEqual("active", first["agent_result"]["final_card_state"]["CARD-001"])
        self.assertEqual("active", second["agent_result"]["final_card_state"]["CARD-001"])

    def test_cost_calculation_uses_cache_and_output_rates(self):
        cost = calculate_api_cost(
            {"prompt_cache_hit_tokens": 1000, "prompt_cache_miss_tokens": 2000, "completion_tokens": 500},
            "deepseek-chat",
        )
        self.assertAlmostEqual(0.0004228, cost)

    def test_live_api_budget_stops_before_eleventh_call(self):
        budget = ApiCallBudget(10)
        for _ in range(10):
            budget.consume()
        with self.assertRaises(ApiCallLimitExceeded):
            budget.consume()


if __name__ == "__main__":
    unittest.main()
