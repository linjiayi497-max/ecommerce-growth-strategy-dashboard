from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd


FUNNEL_STAGES = ["visit", "product_view", "add_to_cart", "checkout", "purchase"]


def _safe_divide(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else float(numerator / denominator)


def _ensure_datetime(data: pd.DataFrame, column: str) -> pd.DataFrame:
    frame = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(frame[column]):
        frame[column] = pd.to_datetime(frame[column])
    return frame


def _score_quantile(series: pd.Series, labels: Iterable[int], ascending: bool) -> pd.Series:
    ranked = series.rank(method="first", ascending=ascending)
    unique_count = ranked.nunique()
    bins = min(5, unique_count)
    if bins <= 1:
        return pd.Series([3] * len(series), index=series.index, dtype="int64")
    scored = pd.qcut(ranked, q=bins, labels=list(labels)[:bins])
    return scored.astype(int)


def kpi_snapshot(orders: pd.DataFrame, events: pd.DataFrame) -> dict[str, float | int]:
    customer_orders = orders.groupby("customer_id")["order_id"].count()
    return {
        "orders": int(len(orders)),
        "active_customers": int(orders["customer_id"].nunique()),
        "sessions": int(events["session_id"].nunique()),
        "net_revenue": round(float(orders["net_revenue"].sum()), 2),
        "gross_margin": round(float(orders["gross_margin"].sum()), 2),
        "gross_margin_rate": round(_safe_divide(float(orders["gross_margin"].sum()), float(orders["net_revenue"].sum())), 4),
        "aov": round(float(orders["net_revenue"].mean()), 2),
        "repeat_purchase_rate": round(float((customer_orders >= 2).mean()), 4),
        "return_rate": round(float(orders["returned"].mean()), 4),
        "visit_to_purchase_rate": round(
            _safe_divide(
                events.loc[events["event_type"] == "purchase", "session_id"].nunique(),
                events.loc[events["event_type"] == "visit", "session_id"].nunique(),
            ),
            4,
        ),
    }


def monthly_revenue(orders: pd.DataFrame) -> pd.DataFrame:
    data = _ensure_datetime(orders, "order_date")
    data["month"] = data["order_date"].dt.to_period("M").astype(str)
    monthly = (
        data.groupby("month")
        .agg(
            orders=("order_id", "count"),
            customers=("customer_id", "nunique"),
            net_revenue=("net_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            coupon_spend=("coupon_spend", "sum"),
            return_rate=("returned", "mean"),
        )
        .reset_index()
    )
    monthly["aov"] = monthly["net_revenue"] / monthly["orders"]
    monthly["gross_margin_rate"] = monthly["gross_margin"] / monthly["net_revenue"]
    return monthly.round(4)


def rfm_segments(orders: pd.DataFrame, as_of_date: pd.Timestamp | None = None) -> pd.DataFrame:
    data = _ensure_datetime(orders, "order_date")
    as_of = as_of_date or (data["order_date"].max() + pd.Timedelta(days=1))
    rfm = (
        data.groupby("customer_id")
        .agg(
            recency_days=("order_date", lambda x: (as_of - x.max()).days),
            frequency=("order_id", "count"),
            monetary=("net_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            coupon_spend=("coupon_spend", "sum"),
            return_rate=("returned", "mean"),
        )
        .reset_index()
    )
    rfm["r_score"] = _score_quantile(rfm["recency_days"], labels=[5, 4, 3, 2, 1], ascending=True)
    rfm["f_score"] = _score_quantile(rfm["frequency"], labels=[1, 2, 3, 4, 5], ascending=True)
    rfm["m_score"] = _score_quantile(rfm["monetary"], labels=[1, 2, 3, 4, 5], ascending=True)
    rfm["rfm_score"] = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)
    rfm["segment"] = rfm.apply(_label_rfm_segment, axis=1)
    return rfm.sort_values(["rfm_score", "monetary"], ascending=False).reset_index(drop=True)


def _label_rfm_segment(row: pd.Series) -> str:
    r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if f >= 4 and m >= 4:
        return "Loyal High Value"
    if r >= 4 and f <= 2:
        return "New Potential"
    if r <= 2 and f >= 3:
        return "At Risk"
    if m >= 4 and f <= 2:
        return "Big Ticket One-Off"
    if r <= 2 and f <= 2:
        return "Cold Low Activity"
    return "Core Customers"


def cohort_retention(orders: pd.DataFrame) -> pd.DataFrame:
    data = _ensure_datetime(orders, "order_date")
    data["order_month"] = data["order_date"].dt.to_period("M")
    first_order = data.groupby("customer_id")["order_month"].min().rename("cohort_month")
    data = data.merge(first_order, on="customer_id")
    data["cohort_index"] = (data["order_month"].dt.year - data["cohort_month"].dt.year) * 12 + (
        data["order_month"].dt.month - data["cohort_month"].dt.month
    )
    cohort_counts = (
        data.groupby(["cohort_month", "cohort_index"])["customer_id"]
        .nunique()
        .reset_index(name="customers")
    )
    cohort_size = cohort_counts.loc[cohort_counts["cohort_index"] == 0, ["cohort_month", "customers"]].rename(
        columns={"customers": "cohort_size"}
    )
    cohort_counts = cohort_counts.merge(cohort_size, on="cohort_month")
    cohort_counts["retention_rate"] = cohort_counts["customers"] / cohort_counts["cohort_size"]
    matrix = cohort_counts.pivot(index="cohort_month", columns="cohort_index", values="retention_rate").fillna(0)
    matrix.index = matrix.index.astype(str)
    matrix.columns = [f"month_{int(col)}" for col in matrix.columns]
    return matrix.round(4).reset_index().rename(columns={"cohort_month": "cohort_month"})


def funnel_metrics(events: pd.DataFrame) -> pd.DataFrame:
    stage_sessions = {
        stage: events.loc[events["event_type"] == stage, "session_id"].nunique()
        for stage in FUNNEL_STAGES
    }
    visit_count = stage_sessions.get("visit", 0)
    rows = []
    previous_count = None
    for stage in FUNNEL_STAGES:
        sessions = stage_sessions[stage]
        rows.append(
            {
                "stage": stage,
                "sessions": int(sessions),
                "conversion_from_visit": round(_safe_divide(sessions, visit_count), 4),
                "step_conversion": round(_safe_divide(sessions, previous_count), 4) if previous_count else 1.0,
                "drop_off_sessions": int((previous_count - sessions) if previous_count else 0),
            }
        )
        previous_count = sessions
    return pd.DataFrame(rows)


def ab_test_result(ab_test: pd.DataFrame) -> dict[str, float | int | str]:
    summary = (
        ab_test.groupby("variant")
        .agg(
            users=("customer_id", "nunique"),
            sessions=("session_id", "nunique"),
            conversions=("converted", "sum"),
            net_revenue=("net_revenue", "sum"),
            coupon_spend=("coupon_spend", "sum"),
        )
        .reset_index()
    )
    metrics = {row.variant: row for row in summary.itertuples(index=False)}
    control = metrics["control"]
    treatment = metrics["treatment"]
    c_rate = _safe_divide(control.conversions, control.sessions)
    t_rate = _safe_divide(treatment.conversions, treatment.sessions)
    pooled_rate = _safe_divide(control.conversions + treatment.conversions, control.sessions + treatment.sessions)
    std_error = math.sqrt(pooled_rate * (1 - pooled_rate) * (1 / control.sessions + 1 / treatment.sessions))
    z_score = _safe_divide(t_rate - c_rate, std_error)
    p_value = math.erfc(abs(z_score) / math.sqrt(2))
    revenue_per_session_control = _safe_divide(control.net_revenue, control.sessions)
    revenue_per_session_treatment = _safe_divide(treatment.net_revenue, treatment.sessions)
    return {
        "control_sessions": int(control.sessions),
        "treatment_sessions": int(treatment.sessions),
        "control_conversion_rate": round(c_rate, 4),
        "treatment_conversion_rate": round(t_rate, 4),
        "absolute_uplift": round(t_rate - c_rate, 4),
        "relative_uplift": round(_safe_divide(t_rate - c_rate, c_rate), 4),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 8),
        "control_revenue_per_session": round(revenue_per_session_control, 2),
        "treatment_revenue_per_session": round(revenue_per_session_treatment, 2),
        "incremental_revenue_per_session": round(revenue_per_session_treatment - revenue_per_session_control, 2),
        "treatment_coupon_spend": round(float(treatment.coupon_spend), 2),
        "recommendation": "ship" if p_value < 0.05 and t_rate > c_rate else "review",
    }


def coupon_strategy(orders: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    data = orders.merge(rfm[["customer_id", "segment"]], on="customer_id", how="left")
    segment_summary = (
        data.groupby("segment")
        .agg(
            customers=("customer_id", "nunique"),
            orders=("order_id", "count"),
            net_revenue=("net_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            coupon_spend=("coupon_spend", "sum"),
            return_rate=("returned", "mean"),
        )
        .reset_index()
    )
    segment_summary["margin_rate"] = segment_summary["gross_margin"] / segment_summary["net_revenue"]
    segment_summary["coupon_to_revenue"] = segment_summary["coupon_spend"] / segment_summary["net_revenue"]
    segment_summary["recommended_action"] = segment_summary.apply(_coupon_action, axis=1)
    segment_summary["expected_growth_lever"] = segment_summary.apply(_expected_growth_lever, axis=1)
    return segment_summary.sort_values("net_revenue", ascending=False).round(4).reset_index(drop=True)


def _coupon_action(row: pd.Series) -> str:
    segment = row["segment"]
    if segment == "Champions":
        return "Protect margin with early access and member-only bundles"
    if segment == "Loyal High Value":
        return "Use threshold coupon only when basket size exceeds segment AOV"
    if segment == "New Potential":
        return "Send welcome journey with small coupon and category guide"
    if segment == "At Risk":
        return "Run win-back coupon with expiration and remarketing audience"
    if segment == "Big Ticket One-Off":
        return "Cross-sell replenishment and service add-ons before discounting"
    if segment == "Cold Low Activity":
        return "Suppress heavy coupons; test low-cost content retargeting"
    return "Maintain CRM cadence and test personalized category offers"


def _expected_growth_lever(row: pd.Series) -> str:
    if row["margin_rate"] < 0.22:
        return "margin recovery"
    if row["return_rate"] > 0.09:
        return "return reduction"
    if row["coupon_to_revenue"] > 0.13:
        return "coupon efficiency"
    return "revenue expansion"
