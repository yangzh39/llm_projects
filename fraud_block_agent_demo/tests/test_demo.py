import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from run_evaluation import run_case  # noqa: E402


class FraudBlockDemoTests(unittest.TestCase):
    def test_generic_request_can_be_clarified(self):
        payload = run_case("clarified_block_removal")
        model_calls = [
            event
            for event in payload["result"]["trace"]
            if event.get("type") == "llm_call" and event.get("purpose") == "intent_classification"
        ]
        self.assertEqual(2, len(model_calls))
        self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_non_fraud_inquiry_offers_and_completes_transfer(self):
        payload = run_case("non_fraud_inquiry")
        trace = payload["result"]["trace"]
        tools = [event.get("tool") for event in trace]
        self.assertIn("transfer_to_department", tools)
        self.assertNotIn("authenticate_customer", tools)
        self.assertEqual("transferred", payload["result"]["disposition"])
        self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_success(self):
        payload = run_case("success")
        self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_reported_fraud_never_authenticates(self):
        payload = run_case("reported_fraud")
        tools = [event.get("tool") for event in payload["result"]["trace"]]
        self.assertNotIn("authenticate_customer", tools)
        self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_bad_auth_discloses_nothing(self):
        payload = run_case("failed_auth")
        tools = [event.get("tool") for event in payload["result"]["trace"]]
        self.assertNotIn("get_customer_cards", tools)
        self.assertNotIn("remove_fraud_block", tools)
        self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_unknown_card_discloses_nothing(self):
        payload = run_case("unknown_card")
        tools = [event.get("tool") for event in payload["result"]["trace"]]
        self.assertNotIn("get_customer_cards", tools)
        self.assertNotIn("remove_fraud_block", tools)
        self.assertEqual("escalated", payload["result"]["disposition"])

    def test_unrecognized_and_ineligible_do_not_remove(self):
        for name in ("unrecognized_transaction", "ineligible_case"):
            with self.subTest(name=name):
                payload = run_case(name)
                tools = [event.get("tool") for event in payload["result"]["trace"]]
                self.assertNotIn("remove_fraud_block", tools)
                self.assertEqual("PASS", payload["evaluation"]["overall_result"])

    def test_hidden_failure_is_caught(self):
        payload = run_case("hidden_failure")
        report = payload["evaluation"]
        self.assertEqual("PASS", report["outcome"])
        self.assertEqual("FAIL", report["trajectory"])
        self.assertEqual("FAIL", report["safety_gates"])
        self.assertTrue(report["critical_failure"])
        self.assertEqual("FAIL", report["overall_result"])


if __name__ == "__main__":
    unittest.main()
