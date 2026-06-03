from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.analytics import (
    ab_test_result,
    cohort_retention,
    coupon_strategy,
    funnel_metrics,
    kpi_snapshot,
    rfm_segments,
)
from ecommerce_growth.data import generate_demo_dataset


class AnalyticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.orders, cls.events, cls.ab_test = generate_demo_dataset(months=6, n_customers=800, seed=7)

    def test_generated_data_has_required_columns(self) -> None:
        self.assertIn("net_revenue", self.orders.columns)
        self.assertIn("event_type", self.events.columns)
        self.assertIn("variant", self.ab_test.columns)
        self.assertGreater(len(self.orders), 100)
        self.assertGreater(len(self.events), len(self.orders))

    def test_kpi_snapshot_ranges(self) -> None:
        kpis = kpi_snapshot(self.orders, self.events)
        self.assertGreater(kpis["net_revenue"], 0)
        self.assertGreaterEqual(kpis["repeat_purchase_rate"], 0)
        self.assertLessEqual(kpis["repeat_purchase_rate"], 1)
        self.assertGreater(kpis["visit_to_purchase_rate"], 0)

    def test_rfm_segments_cover_customers(self) -> None:
        rfm = rfm_segments(self.orders)
        self.assertEqual(rfm["customer_id"].nunique(), self.orders["customer_id"].nunique())
        self.assertIn("segment", rfm.columns)
        self.assertGreaterEqual(rfm["rfm_score"].min(), 3)

    def test_cohort_retention_has_month_zero(self) -> None:
        retention = cohort_retention(self.orders)
        self.assertIn("month_0", retention.columns)
        self.assertTrue((retention["month_0"] == 1.0).all())

    def test_funnel_is_monotonic(self) -> None:
        funnel = funnel_metrics(self.events)
        counts = list(funnel["sessions"])
        self.assertEqual(funnel.iloc[0]["stage"], "visit")
        self.assertTrue(all(left >= right for left, right in zip(counts, counts[1:])))

    def test_ab_test_result_contains_decision(self) -> None:
        result = ab_test_result(self.ab_test)
        self.assertIn(result["recommendation"], {"ship", "review"})
        self.assertGreaterEqual(result["p_value"], 0)
        self.assertLessEqual(result["p_value"], 1)

    def test_coupon_strategy_has_actions(self) -> None:
        rfm = rfm_segments(self.orders)
        strategy = coupon_strategy(self.orders, rfm)
        self.assertIn("recommended_action", strategy.columns)
        self.assertFalse(strategy["recommended_action"].isna().any())


if __name__ == "__main__":
    unittest.main()

