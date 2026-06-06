from __future__ import annotations

import json
from io import BytesIO
from typing import Any

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


def has_valid_ab_test(ab_test: pd.DataFrame | None) -> bool:
    if ab_test is None or ab_test.empty:
        return False
    variants = set(ab_test["variant"].astype(str).str.lower())
    return {"control", "treatment"}.issubset(variants)


def build_analysis_outputs(
    orders: pd.DataFrame,
    events: pd.DataFrame,
    ab_test: pd.DataFrame | None = None,
) -> dict[str, Any]:
    rfm = rfm_segments(orders)
    outputs: dict[str, Any] = {
        "kpi_snapshot": kpi_snapshot(orders, events),
        "monthly_revenue": monthly_revenue(orders),
        "rfm_segments": rfm,
        "cohort_retention": cohort_retention(orders),
        "funnel_metrics": funnel_metrics(events),
        "coupon_strategy": coupon_strategy(orders, rfm),
    }
    if has_valid_ab_test(ab_test):
        outputs["ab_test_result"] = ab_test_result(ab_test)
    return outputs


def excel_report_bytes(outputs: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, value in outputs.items():
            sheet_name = name[:31]
            if isinstance(value, pd.DataFrame):
                value.to_excel(writer, sheet_name=sheet_name, index=False)
            elif isinstance(value, dict):
                pd.DataFrame([value]).to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                pd.DataFrame({"value": [json.dumps(value, ensure_ascii=False)]}).to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()


def pdf_report_bytes(outputs: dict[str, Any], title: str, data_label: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.4 * cm, leftMargin=1.4 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm)
    styles = getSampleStyleSheet()
    story: list[Any] = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Data scope: {data_label}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    kpis = outputs["kpi_snapshot"]
    story.append(Paragraph("KPI Summary", styles["Heading2"]))
    story.append(_table_from_rows([["Metric", "Value"], *[[key, _format_value(value)] for key, value in kpis.items()]], colors.HexColor("#1f4e79")))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("RFM Segment Summary", styles["Heading2"]))
    rfm_summary = (
        outputs["rfm_segments"].groupby("segment")
        .agg(customers=("customer_id", "count"), monetary=("monetary", "sum"), avg_recency=("recency_days", "mean"))
        .reset_index()
        .sort_values("monetary", ascending=False)
        .round(2)
    )
    story.append(_dataframe_table(rfm_summary.head(8), colors.HexColor("#f28c28")))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Funnel Conversion", styles["Heading2"]))
    story.append(_dataframe_table(outputs["funnel_metrics"], colors.HexColor("#1f4e79")))
    story.append(PageBreak())

    story.append(Paragraph("Cohort Retention", styles["Heading2"]))
    story.append(_dataframe_table(outputs["cohort_retention"].head(10), colors.HexColor("#1f4e79")))
    story.append(Spacer(1, 0.4 * cm))

    if "ab_test_result" in outputs:
        story.append(Paragraph("A/B Test Conclusion", styles["Heading2"]))
        story.append(_table_from_rows([["Metric", "Value"], *[[key, _format_value(value)] for key, value in outputs["ab_test_result"].items()]], colors.HexColor("#f28c28")))
        story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Coupon Strategy", styles["Heading2"]))
    story.append(_dataframe_table(outputs["coupon_strategy"].head(8), colors.HexColor("#1f4e79")))
    doc.build(story)
    return buffer.getvalue()


def _dataframe_table(df: pd.DataFrame, header_color: Any) -> Any:
    rows = [list(df.columns)]
    for _, row in df.iterrows():
        rows.append([_format_value(value) for value in row.tolist()])
    return _table_from_rows(rows, header_color)


def _table_from_rows(rows: list[list[Any]], header_color: Any) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8dde6")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
            ]
        )
    )
    return table


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.4f}" if abs(value) < 1 else f"{value:,.2f}"
    return str(value)

