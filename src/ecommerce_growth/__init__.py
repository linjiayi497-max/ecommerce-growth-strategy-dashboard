"""E-commerce growth analytics toolkit."""

from .analytics import (
    ab_test_result,
    cohort_retention,
    coupon_strategy,
    funnel_metrics,
    kpi_snapshot,
    monthly_revenue,
    rfm_segments,
)
from .data import generate_demo_dataset, save_demo_dataset

__all__ = [
    "ab_test_result",
    "cohort_retention",
    "coupon_strategy",
    "funnel_metrics",
    "generate_demo_dataset",
    "kpi_snapshot",
    "monthly_revenue",
    "rfm_segments",
    "save_demo_dataset",
]

