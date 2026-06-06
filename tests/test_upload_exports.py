from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.data import generate_demo_dataset
from ecommerce_growth.exports import build_analysis_outputs, excel_report_bytes, pdf_report_bytes
from ecommerce_growth.upload import (
    EVENT_FIELDS,
    ORDER_FIELDS,
    canonicalize_events,
    canonicalize_orders,
    guess_mapping,
    validate_mapping,
)


class UploadAndExportTest(unittest.TestCase):
    def test_guess_mapping_and_canonicalize_orders(self) -> None:
        raw = pd.DataFrame(
            {
                "user_id": ["u1", "u2"],
                "created_at": ["2026-01-01", "2026-01-02"],
                "amount": [120, 180],
            }
        )
        mapping = guess_mapping(raw, ORDER_FIELDS)
        self.assertEqual(mapping["customer_id"], "user_id")
        self.assertEqual(mapping["order_date"], "created_at")
        self.assertEqual(mapping["net_revenue"], "amount")
        self.assertEqual(validate_mapping(mapping, ORDER_FIELDS, "订单表"), [])
        orders = canonicalize_orders(raw, mapping)
        self.assertEqual(list(orders.columns)[0], "customer_id")
        self.assertEqual(float(orders["net_revenue"].sum()), 300.0)
        self.assertIn("gross_margin", orders.columns)

    def test_missing_required_field_is_reported(self) -> None:
        raw = pd.DataFrame({"user_id": ["u1"], "amount": [100]})
        mapping = guess_mapping(raw, ORDER_FIELDS)
        errors = validate_mapping(mapping, ORDER_FIELDS, "订单表")
        self.assertTrue(any("下单时间" in error for error in errors))

    def test_canonicalize_events(self) -> None:
        raw = pd.DataFrame(
            {
                "user_id": ["u1", "u1"],
                "event": ["visit", "purchase"],
                "timestamp": ["2026-01-01 10:00:00", "2026-01-01 10:05:00"],
            }
        )
        mapping = guess_mapping(raw, EVENT_FIELDS)
        events = canonicalize_events(raw, mapping)
        self.assertEqual(events["session_id"].nunique(), 2)
        self.assertIn("event_time", events.columns)

    def test_excel_and_pdf_exports(self) -> None:
        orders, events, ab_test = generate_demo_dataset(months=4, n_customers=300, seed=3)
        outputs = build_analysis_outputs(orders, events, ab_test)
        excel = excel_report_bytes(outputs)
        pdf = pdf_report_bytes(outputs, "GrowthLens Test Report", "unit test")
        self.assertGreater(len(excel), 1000)
        self.assertGreater(len(pdf), 1000)
        self.assertTrue(pdf.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

