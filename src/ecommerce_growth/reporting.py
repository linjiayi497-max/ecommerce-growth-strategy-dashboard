from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analytics import (
    ab_test_result,
    cohort_retention,
    coupon_strategy,
    funnel_metrics,
    kpi_snapshot,
    monthly_revenue,
    rfm_segments,
)
from .data import load_demo_dataset


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_outputs(data_dir: str | Path, output_dir: str | Path) -> dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    orders, events, ab_test = load_demo_dataset(data_dir)

    kpis = kpi_snapshot(orders, events)
    monthly = monthly_revenue(orders)
    rfm = rfm_segments(orders)
    retention = cohort_retention(orders)
    funnel = funnel_metrics(events)
    experiment = ab_test_result(ab_test)
    coupon = coupon_strategy(orders, rfm)

    _write_json(output_path / "kpi_snapshot.json", kpis)
    monthly.to_csv(output_path / "monthly_revenue.csv", index=False)
    rfm.to_csv(output_path / "rfm_segments.csv", index=False)
    retention.to_csv(output_path / "cohort_retention.csv", index=False)
    funnel.to_csv(output_path / "funnel_metrics.csv", index=False)
    _write_json(output_path / "ab_test_result.json", experiment)
    coupon.to_csv(output_path / "coupon_strategy.csv", index=False)
    write_insights_summary(output_path / "insights_summary.md", kpis, monthly, rfm, funnel, experiment, coupon)

    return {
        "kpi_snapshot": kpis,
        "monthly_revenue": monthly,
        "rfm_segments": rfm,
        "cohort_retention": retention,
        "funnel_metrics": funnel,
        "ab_test_result": experiment,
        "coupon_strategy": coupon,
    }


def write_insights_summary(
    path: Path,
    kpis: dict[str, object],
    monthly: pd.DataFrame,
    rfm: pd.DataFrame,
    funnel: pd.DataFrame,
    experiment: dict[str, object],
    coupon: pd.DataFrame,
) -> None:
    best_month = monthly.sort_values("net_revenue", ascending=False).iloc[0]
    champion_share = (
        rfm.loc[rfm["segment"] == "Champions", "monetary"].sum() / rfm["monetary"].sum()
        if not rfm.empty
        else 0
    )
    checkout_step = funnel.loc[funnel["stage"] == "checkout", "step_conversion"].iloc[0]
    purchase_step = funnel.loc[funnel["stage"] == "purchase", "step_conversion"].iloc[0]
    top_coupon = coupon.iloc[0]

    lines = [
        "# Insights Summary",
        "",
        "## KPI Snapshot",
        f"- Net revenue: {kpis['net_revenue']:,}",
        f"- Orders: {kpis['orders']:,}",
        f"- Active customers: {kpis['active_customers']:,}",
        f"- Gross margin rate: {kpis['gross_margin_rate']:.2%}",
        f"- Repeat purchase rate: {kpis['repeat_purchase_rate']:.2%}",
        "",
        "## Growth Findings",
        f"- Best revenue month is {best_month['month']} with net revenue {best_month['net_revenue']:,.0f}.",
        f"- Champions contribute {champion_share:.2%} of customer monetary value, so blanket couponing would dilute margin.",
        f"- Checkout step conversion is {checkout_step:.2%}; purchase step conversion is {purchase_step:.2%}.",
        f"- Treatment conversion rate is {experiment['treatment_conversion_rate']:.2%}, versus {experiment['control_conversion_rate']:.2%} for control.",
        f"- A/B decision: {experiment['recommendation']} with p-value {experiment['p_value']}.",
        "",
        "## Coupon Strategy Priority",
        f"- Largest segment by revenue: {top_coupon['segment']}.",
        f"- Recommended action: {top_coupon['recommended_action']}.",
        f"- Growth lever: {top_coupon['expected_growth_lever']}.",
        "",
        "## Resume Evidence",
        "- Built a reproducible e-commerce growth analytics system covering KPI monitoring, RFM segmentation, cohort retention, funnel diagnosis, A/B testing, and coupon strategy.",
        "- Converted event and order data into business actions for CRM, user operations, and growth strategy roles.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

