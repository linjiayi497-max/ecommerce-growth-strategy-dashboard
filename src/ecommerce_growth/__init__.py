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
from .exports import build_analysis_outputs, excel_report_bytes, pdf_report_bytes

__all__ = [
    "ab_test_result",
    "build_analysis_outputs",
    "cohort_retention",
    "coupon_strategy",
    "funnel_metrics",
    "generate_demo_dataset",
    "kpi_snapshot",
    "monthly_revenue",
    "excel_report_bytes",
    "pdf_report_bytes",
    "rfm_segments",
    "save_demo_dataset",
]
