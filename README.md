# E-commerce Growth Strategy Dashboard

A reproducible e-commerce growth analytics project for data operations, business analysis, and growth strategy interviews. It converts order, event, and experiment data into KPI monitoring, RFM segmentation, cohort retention, funnel diagnosis, A/B test decisions, and coupon strategy recommendations.

The dataset is synthetic and generated locally. The implementation is original; no external project code is copied.

## Why This Project

This project targets JD keywords often seen in internet operations, strategy, commercial analytics, and data analyst internships:

- KPI monitoring: revenue, orders, AOV, repeat rate, margin rate, return rate.
- User analysis: RFM segmentation and segment-level growth actions.
- Growth analytics: session funnel, cohort retention, and A/B test uplift.
- CRM strategy: coupon efficiency and segment-specific recommendations.
- SQL communication: interview-ready query examples for funnel, cohort, and experiment analysis.

## Open-source Inspiration

The design borrows product ideas from public GitHub projects, while the code and dataset are built from scratch:

- [streamlit/example-app-cohort-analysis](https://github.com/streamlit/example-app-cohort-analysis): cohort analysis and Streamlit heatmap presentation.
- [AmirhosseinHonardoust/Data-Storytelling-Dashboard](https://github.com/AmirhosseinHonardoust/Data-Storytelling-Dashboard): Streamlit/Plotly dashboard narrative style for e-commerce KPIs.
- [growthbook/growthbook-python](https://github.com/growthbook/growthbook-python): experiment assignment and A/B testing workflow inspiration.

## Project Structure

```text
.
|-- app.py
|-- data/
|   |-- demo_ab_test.csv
|   |-- demo_events.csv
|   `-- demo_orders.csv
|-- outputs/
|   |-- ab_test_result.json
|   |-- cohort_retention.csv
|   |-- coupon_strategy.csv
|   |-- funnel_metrics.csv
|   |-- insights_summary.md
|   |-- kpi_snapshot.json
|   |-- monthly_revenue.csv
|   `-- rfm_segments.csv
|-- scripts/
|   |-- generate_demo_data.py
|   `-- run_analysis.py
|-- sql/
|   `-- business_analysis_queries.sql
|-- src/ecommerce_growth/
|   |-- analytics.py
|   |-- data.py
|   `-- reporting.py
`-- tests/
    `-- test_analytics.py
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python scripts/generate_demo_data.py
python scripts/run_analysis.py
streamlit run app.py
python -m unittest discover -s tests
```

## Analysis Outputs

Running `python scripts/run_analysis.py` writes:

- `outputs/kpi_snapshot.json`: executive KPI snapshot.
- `outputs/monthly_revenue.csv`: revenue, margin, coupon, and return-rate trend.
- `outputs/rfm_segments.csv`: customer-level RFM scores and segment labels.
- `outputs/cohort_retention.csv`: monthly retention matrix.
- `outputs/funnel_metrics.csv`: stage-by-stage conversion and drop-off.
- `outputs/ab_test_result.json`: conversion uplift, p-value, revenue per session, and decision.
- `outputs/coupon_strategy.csv`: segment-level coupon actions and growth levers.
- `outputs/insights_summary.md`: concise business findings for interview discussion.

## Resume Evidence Draft

Use only after the repository is uploaded and reviewed:

> Built an e-commerce growth analytics system with Python and Streamlit, generating synthetic order/event/A-B test data and analyzing KPI trends, RFM segmentation, cohort retention, conversion funnels, experiment uplift, and coupon efficiency; produced SQL examples and action-oriented CRM recommendations for user operations and growth strategy scenarios.

## Interview Talking Points

- How to define north-star and guardrail metrics for an e-commerce growth campaign.
- How RFM segments translate into differentiated CRM and coupon actions.
- How to diagnose funnel drop-off and decide whether the problem is traffic quality, page conversion, checkout friction, or pricing.
- How to read A/B test uplift, p-value, revenue per session, and coupon spend together.
- How to prevent growth tactics from sacrificing gross margin.
