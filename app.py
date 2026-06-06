from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.analytics import monthly_revenue
from ecommerce_growth.data import generate_demo_dataset, load_demo_dataset, save_demo_dataset
from ecommerce_growth.exports import build_analysis_outputs, excel_report_bytes, has_valid_ab_test, pdf_report_bytes
from ecommerce_growth.upload import (
    AB_FIELDS,
    EVENT_FIELDS,
    ORDER_FIELDS,
    canonicalize_ab_test,
    canonicalize_events,
    canonicalize_orders,
    guess_mapping,
    read_table,
    validate_mapping,
)


DATA_DIR = ROOT / "data"
BRAND_BLUE = "#17324d"
BRAND_ORANGE = "#f28c28"


@st.cache_data
def load_or_create_demo_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not (DATA_DIR / "demo_orders.csv").exists():
        orders, events, ab_test = generate_demo_dataset()
        save_demo_dataset(orders, events, ab_test, DATA_DIR)
    return load_demo_dataset(DATA_DIR)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
          .stApp {{
            background: #f7f9fb;
          }}
          .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 18px;
            background: {BRAND_BLUE};
            color: white;
            border-radius: 6px;
            margin-bottom: 18px;
          }}
          .topbar h1 {{
            font-size: 24px;
            margin: 0;
            letter-spacing: 0;
          }}
          .status-pill {{
            border: 1px solid rgba(255,255,255,.35);
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 13px;
          }}
          .metric-card {{
            background: white;
            border: 1px solid #e3e8ef;
            border-left: 4px solid {BRAND_ORANGE};
            border-radius: 6px;
            padding: 14px 14px 10px 14px;
            min-height: 96px;
            box-shadow: 0 2px 10px rgba(23, 50, 77, .06);
          }}
          .metric-label {{
            color: #607088;
            font-size: 13px;
            margin-bottom: 4px;
          }}
          .metric-value {{
            color: {BRAND_BLUE};
            font-size: 24px;
            font-weight: 700;
          }}
          .metric-delta {{
            font-size: 13px;
            margin-top: 4px;
          }}
          .privacy-note {{
            margin-top: 18px;
            color: #607088;
            font-size: 12px;
            text-align: center;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_intro_once() -> None:
    if "intro_seen" in st.session_state:
        return
    st.session_state["intro_seen"] = True
    if hasattr(st, "dialog"):
        @st.dialog("GrowthLens")
        def intro() -> None:
            st.write("上传订单、行为和实验数据后，系统会生成 KPI、RFM、留存、漏斗、A/B 实验和优惠券策略分析。")
            st.write("未上传时默认使用内置演示数据。上传文件只用于当前会话分析，不会写入本地文件。")
        intro()
    else:
        st.info("GrowthLens 支持上传订单、行为和实验数据；未上传时默认使用演示数据。")


def render_topbar(data_status: str) -> None:
    st.markdown(
        f"""
        <div class="topbar">
          <h1>GrowthLens</h1>
          <div class="status-pill">{data_status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mapping_form(label: str, df: pd.DataFrame, specs: dict[str, Any], key_prefix: str) -> dict[str, str | None]:
    st.markdown(f"#### {label}字段映射")
    guesses = guess_mapping(df, specs)
    mapping: dict[str, str | None] = {}
    options = [""] + list(df.columns)
    cols = st.columns(2)
    for idx, (field, spec) in enumerate(specs.items()):
        with cols[idx % 2]:
            default = guesses.get(field)
            default_index = options.index(default) if default in options else 0
            selected = st.selectbox(
                f"{spec.label}{' *' if spec.required else ''}",
                options,
                index=default_index,
                key=f"{key_prefix}_{field}",
            )
            mapping[field] = selected or None
    return mapping


def load_uploaded_table(uploaded_file: Any) -> pd.DataFrame | None:
    if uploaded_file is None:
        return None
    try:
        return read_table(uploaded_file, uploaded_file.name)
    except Exception as exc:
        st.error(f"{uploaded_file.name} 读取失败：{exc}")
        return None


def upload_workflow() -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None, str]:
    st.markdown("### 上传数据")
    st.caption("支持 CSV、XLSX。数据只保存在当前浏览器会话的内存中，不写入服务器文件。")
    order_file = st.file_uploader("订单表", type=["csv", "xlsx", "xls"], key="orders_upload")
    event_file = st.file_uploader("用户行为表", type=["csv", "xlsx", "xls"], key="events_upload")
    ab_file = st.file_uploader("A/B实验表（可选）", type=["csv", "xlsx", "xls"], key="ab_upload")

    orders_raw = load_uploaded_table(order_file)
    events_raw = load_uploaded_table(event_file)
    ab_raw = load_uploaded_table(ab_file)

    if orders_raw is None or events_raw is None:
        st.info("上传订单表和用户行为表后即可配置字段映射；A/B 实验表可选。")
        return None, None, None, "演示数据"

    with st.form("mapping_form"):
        orders_mapping = render_mapping_form("订单表", orders_raw, ORDER_FIELDS, "orders")
        st.divider()
        events_mapping = render_mapping_form("用户行为表", events_raw, EVENT_FIELDS, "events")
        ab_mapping = None
        if ab_raw is not None:
            st.divider()
            ab_mapping = render_mapping_form("A/B实验表", ab_raw, AB_FIELDS, "ab")
        submitted = st.form_submit_button("确认映射并开始分析", type="primary")

    if not submitted:
        st.info("确认字段映射后，分析看板会切换到上传数据。")
        return None, None, None, "演示数据"

    errors = []
    errors.extend(validate_mapping(orders_mapping, ORDER_FIELDS, "订单表"))
    errors.extend(validate_mapping(events_mapping, EVENT_FIELDS, "用户行为表"))
    if ab_raw is not None and ab_mapping is not None:
        errors.extend(validate_mapping(ab_mapping, AB_FIELDS, "A/B实验表"))
    if errors:
        for error in errors:
            st.error(error)
        return None, None, None, "演示数据"

    try:
        orders = canonicalize_orders(orders_raw, orders_mapping)
        events = canonicalize_events(events_raw, events_mapping)
        ab_test = canonicalize_ab_test(ab_raw, ab_mapping) if ab_raw is not None and ab_mapping is not None else None
    except Exception as exc:
        st.error(f"字段转换失败：{exc}")
        return None, None, None, "演示数据"

    if orders.empty or events.empty:
        st.error("字段转换后订单表或行为表为空，请检查字段映射和日期/金额格式。")
        return None, None, None, "演示数据"

    st.session_state["custom_data"] = (orders, events, ab_test)
    st.success("字段映射已确认，当前看板使用上传数据。")
    return orders, events, ab_test, "上传数据"


def get_active_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None, str]:
    if "custom_data" in st.session_state:
        orders, events, ab_test = st.session_state["custom_data"]
        return orders, events, ab_test, "上传数据"
    orders, events, ab_test = load_or_create_demo_data()
    return orders, events, ab_test, "演示数据"


def render_metric_card(label: str, value: str, delta: str | None = None, positive: bool | None = None) -> None:
    color = "#0f8a4b" if positive else "#c0392b" if positive is False else "#607088"
    delta_html = f'<div class="metric-delta" style="color:{color};">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def monthly_delta(outputs: dict[str, Any], column: str) -> tuple[str | None, bool | None]:
    monthly = outputs["monthly_revenue"]
    if len(monthly) < 2:
        return None, None
    previous = float(monthly.iloc[-2][column])
    current = float(monthly.iloc[-1][column])
    if previous == 0:
        return None, None
    delta = (current - previous) / previous
    arrow = "↑" if delta >= 0 else "↓"
    return f"{arrow} {abs(delta):.1%} vs last month", delta >= 0


def render_dashboard(orders: pd.DataFrame, events: pd.DataFrame, ab_test: pd.DataFrame | None, data_status: str) -> None:
    channel_options = sorted(orders["channel"].dropna().astype(str).unique())
    category_options = sorted(orders["category"].dropna().astype(str).unique())
    channel_filter = st.sidebar.multiselect("渠道", channel_options, default=channel_options)
    category_filter = st.sidebar.multiselect("品类", category_options, default=category_options)

    filtered_orders = orders[orders["channel"].isin(channel_filter) & orders["category"].isin(category_filter)].copy()
    filtered_events = events[events["channel"].isin(channel_filter)].copy() if "channel" in events else events.copy()
    filtered_ab = ab_test.copy() if ab_test is not None else None

    if filtered_orders.empty or filtered_events.empty:
        st.warning("当前筛选条件下没有足够数据。")
        return

    outputs = build_analysis_outputs(filtered_orders, filtered_events, filtered_ab)
    render_exports(outputs, data_status)

    kpis = outputs["kpi_snapshot"]
    delta_revenue, revenue_positive = monthly_delta(outputs, "net_revenue")
    delta_orders, orders_positive = monthly_delta(outputs, "orders")
    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card("Net Revenue", f"{kpis['net_revenue']:,.0f}", delta_revenue, revenue_positive)
    with metric_cols[1]:
        render_metric_card("Orders", f"{kpis['orders']:,}", delta_orders, orders_positive)
    with metric_cols[2]:
        render_metric_card("AOV", f"{kpis['aov']:,.0f}")
    with metric_cols[3]:
        render_metric_card("Repeat Rate", f"{kpis['repeat_purchase_rate']:.1%}")
    with metric_cols[4]:
        render_metric_card("Visit to Purchase", f"{kpis['visit_to_purchase_rate']:.1%}")

    tabs = ["Overview", "RFM Segments", "Cohort Retention", "Funnel", "Coupon Strategy"]
    if "ab_test_result" in outputs:
        tabs.insert(4, "A/B Test")
    overview_tab, rfm_tab, cohort_tab, funnel_tab, *remaining_tabs = st.tabs(tabs)

    with overview_tab:
        monthly = outputs["monthly_revenue"]
        st.plotly_chart(px.line(monthly, x="month", y=["net_revenue", "gross_margin"], markers=True, title="Monthly Revenue and Margin"), use_container_width=True)
        channel_summary = (
            filtered_orders.groupby("channel")
            .agg(net_revenue=("net_revenue", "sum"), orders=("order_id", "count"), gross_margin=("gross_margin", "sum"))
            .reset_index()
        )
        channel_summary["gross_margin_rate"] = channel_summary["gross_margin"] / channel_summary["net_revenue"]
        st.plotly_chart(px.bar(channel_summary, x="channel", y="net_revenue", color="gross_margin_rate", title="Channel Revenue"), use_container_width=True)

    with rfm_tab:
        rfm = outputs["rfm_segments"]
        segment_summary = (
            rfm.groupby("segment")
            .agg(customers=("customer_id", "count"), monetary=("monetary", "sum"), avg_recency=("recency_days", "mean"))
            .reset_index()
            .sort_values("monetary", ascending=False)
        )
        st.plotly_chart(px.bar(segment_summary, x="segment", y="monetary", color="customers", title="RFM Segment Value"), use_container_width=True)
        st.dataframe(rfm.head(150), use_container_width=True)

    with cohort_tab:
        retention = outputs["cohort_retention"]
        st.plotly_chart(px.imshow(retention.set_index("cohort_month"), aspect="auto", color_continuous_scale="Teal", title="Monthly Cohort Retention"), use_container_width=True)
        st.dataframe(retention, use_container_width=True)

    with funnel_tab:
        funnel = outputs["funnel_metrics"]
        st.plotly_chart(px.funnel(funnel, y="stage", x="sessions", title="Session Funnel"), use_container_width=True)
        st.dataframe(funnel, use_container_width=True)

    next_tab_idx = 0
    if "ab_test_result" in outputs:
        with remaining_tabs[next_tab_idx]:
            experiment = outputs["ab_test_result"]
            st.dataframe(pd.DataFrame([experiment]), use_container_width=True)
            st.metric("Relative Uplift", f"{experiment['relative_uplift']:.1%}", f"p={experiment['p_value']}")
        next_tab_idx += 1
    elif ab_test is not None and not has_valid_ab_test(ab_test):
        st.info("已上传 A/B 实验表，但缺少 control/treatment 两组，A/B 分析暂不展示。")
    elif ab_test is None:
        st.info("未上传 A/B 实验表，当前隐藏 A/B 实验模块。")

    with remaining_tabs[next_tab_idx]:
        coupon = outputs["coupon_strategy"]
        st.plotly_chart(px.scatter(coupon, x="coupon_to_revenue", y="margin_rate", size="net_revenue", color="segment", title="Coupon Efficiency by Segment"), use_container_width=True)
        st.dataframe(coupon, use_container_width=True)


def render_exports(outputs: dict[str, Any], data_status: str) -> None:
    st.sidebar.markdown("### 导出")
    excel_data = excel_report_bytes(outputs)
    st.sidebar.download_button(
        "下载 Excel 结果",
        data=excel_data,
        file_name="growthlens_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    try:
        pdf_data = pdf_report_bytes(outputs, "GrowthLens E-commerce Growth Report", data_status)
        st.sidebar.download_button(
            "下载 PDF 报告",
            data=pdf_data,
            file_name="growthlens_report.pdf",
            mime="application/pdf",
        )
    except Exception as exc:
        st.sidebar.warning(f"PDF 生成不可用：{exc}")


def main() -> None:
    st.set_page_config(page_title="GrowthLens", layout="wide")
    inject_css()
    show_intro_once()
    orders, events, ab_test, data_status = get_active_data()
    render_topbar(f"当前数据：{data_status}")

    upload_tab, dashboard_tab = st.tabs(["上传数据", "分析看板"])
    with upload_tab:
        uploaded_orders, uploaded_events, uploaded_ab, uploaded_status = upload_workflow()
        if uploaded_orders is not None and uploaded_events is not None:
            orders, events, ab_test, data_status = uploaded_orders, uploaded_events, uploaded_ab, uploaded_status
        if st.button("清除上传数据，恢复演示数据"):
            st.session_state.pop("custom_data", None)
            st.rerun()

    with dashboard_tab:
        if data_status == "演示数据":
            st.info("当前为演示数据。上传自定义订单表和行为表后，可生成专属分析结果。")
        render_dashboard(orders, events, ab_test, data_status)
        st.markdown('<div class="privacy-note">数据仅用于当前会话分析，不会写入服务器文件或仓库。</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

