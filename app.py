from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.analytics import (
    ab_test_result,
    cohort_retention,
    coupon_strategy,
    funnel_metrics,
    kpi_snapshot,
    monthly_revenue,
    rfm_segments,
)
from ecommerce_growth.data import generate_demo_dataset, load_demo_dataset, save_demo_dataset


DATA_DIR = ROOT / "data"


@st.cache_data
def load_or_create_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not (DATA_DIR / "demo_orders.csv").exists():
        orders, events, ab_test = generate_demo_dataset()
        save_demo_dataset(orders, events, ab_test, DATA_DIR)
    return load_demo_dataset(DATA_DIR)


st.set_page_config(page_title="E-commerce Growth Analytics", layout="wide")
st.title("E-commerce Growth Analytics")

orders, events, ab_test = load_or_create_data()
channel_filter = st.sidebar.multiselect("Channel", sorted(orders["channel"].unique()), default=sorted(orders["channel"].unique()))
category_filter = st.sidebar.multiselect("Category", sorted(orders["category"].unique()), default=sorted(orders["category"].unique()))

filtered_orders = orders[orders["channel"].isin(channel_filter) & orders["category"].isin(category_filter)].copy()
filtered_events = events[events["session_id"].isin(filtered_orders["session_id"].unique()) | events["channel"].isin(channel_filter)].copy()
filtered_ab = ab_test[ab_test["channel"].isin(channel_filter)].copy()

kpis = kpi_snapshot(filtered_orders, filtered_events)
metric_cols = st.columns(5)
metric_cols[0].metric("Net Revenue", f"{kpis['net_revenue']:,.0f}")
metric_cols[1].metric("Orders", f"{kpis['orders']:,}")
metric_cols[2].metric("AOV", f"{kpis['aov']:,.0f}")
metric_cols[3].metric("Repeat Rate", f"{kpis['repeat_purchase_rate']:.1%}")
metric_cols[4].metric("Visit to Purchase", f"{kpis['visit_to_purchase_rate']:.1%}")

overview_tab, rfm_tab, cohort_tab, funnel_tab, experiment_tab, coupon_tab = st.tabs(
    ["Overview", "RFM Segments", "Cohort Retention", "Funnel", "A/B Test", "Coupon Strategy"]
)

with overview_tab:
    monthly = monthly_revenue(filtered_orders)
    st.plotly_chart(
        px.line(monthly, x="month", y=["net_revenue", "gross_margin"], markers=True, title="Monthly Revenue and Margin"),
        use_container_width=True,
    )
    channel_summary = (
        filtered_orders.groupby("channel")
        .agg(net_revenue=("net_revenue", "sum"), orders=("order_id", "count"), margin_rate=("gross_margin", lambda x: x.sum()))
        .reset_index()
    )
    channel_summary["margin_rate"] = channel_summary["margin_rate"] / channel_summary["net_revenue"]
    st.plotly_chart(px.bar(channel_summary, x="channel", y="net_revenue", color="margin_rate", title="Channel Revenue"), use_container_width=True)

with rfm_tab:
    rfm = rfm_segments(filtered_orders)
    segment_summary = (
        rfm.groupby("segment")
        .agg(customers=("customer_id", "count"), monetary=("monetary", "sum"), avg_recency=("recency_days", "mean"))
        .reset_index()
        .sort_values("monetary", ascending=False)
    )
    st.plotly_chart(px.bar(segment_summary, x="segment", y="monetary", color="customers", title="RFM Segment Value"), use_container_width=True)
    st.dataframe(rfm.head(150), use_container_width=True)

with cohort_tab:
    retention = cohort_retention(filtered_orders)
    heatmap_df = retention.set_index("cohort_month")
    st.plotly_chart(px.imshow(heatmap_df, aspect="auto", color_continuous_scale="Teal", title="Monthly Cohort Retention"), use_container_width=True)
    st.dataframe(retention, use_container_width=True)

with funnel_tab:
    funnel = funnel_metrics(filtered_events)
    st.plotly_chart(px.funnel(funnel, y="stage", x="sessions", title="Session Funnel"), use_container_width=True)
    st.dataframe(funnel, use_container_width=True)

with experiment_tab:
    experiment = ab_test_result(filtered_ab)
    exp_df = pd.DataFrame([experiment])
    st.dataframe(exp_df, use_container_width=True)
    st.metric("Relative Uplift", f"{experiment['relative_uplift']:.1%}", f"p={experiment['p_value']}")

with coupon_tab:
    rfm = rfm_segments(filtered_orders)
    coupon = coupon_strategy(filtered_orders, rfm)
    st.plotly_chart(px.scatter(coupon, x="coupon_to_revenue", y="margin_rate", size="net_revenue", color="segment", title="Coupon Efficiency by Segment"), use_container_width=True)
    st.dataframe(coupon, use_container_width=True)

