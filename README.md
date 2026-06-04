# 电商增长策略分析看板

这是一个面向互联网运营、增长分析、商业分析和数据分析实习岗位的电商增长分析项目。项目使用 Python 生成可复现的模拟电商数据，并通过 Streamlit 看板展示 KPI、RFM 用户分层、月度留存、转化漏斗、A/B 实验和优惠券策略。

数据为本地生成的模拟数据，代码为原创实现，未复制外部项目代码。

## 项目亮点

- 构造订单、用户行为事件和 A/B 实验曝光数据。
- 计算收入、订单数、AOV、复购率、毛利率、退货率等核心指标。
- 基于 RFM 识别高价值用户、潜力用户、流失风险用户等客群。
- 生成月度 cohort 留存矩阵，判断用户长期价值。
- 计算访问、商品浏览、加购、结算、购买漏斗转化和流失。
- 评估 A/B 实验转化率 uplift、p-value 和每 session 收入。
- 输出分客群优惠券与 CRM 策略建议。
- 提供 SQL 样例，便于面试讨论指标口径和数据分析逻辑。

## 项目结构

```text
.
|-- app.py                         # Streamlit 看板
|-- data/                          # 模拟订单、事件、实验数据
|-- outputs/                       # 分析结果与洞察报告
|-- scripts/
|   |-- generate_demo_data.py      # 生成模拟数据
|   `-- run_analysis.py            # 运行分析流水线
|-- sql/
|   `-- business_analysis_queries.sql
|-- src/ecommerce_growth/
|   |-- analytics.py               # KPI、RFM、留存、漏斗、A/B 分析
|   |-- data.py                    # 数据生成与读取
|   `-- reporting.py               # 报告输出
`-- tests/
    `-- test_analytics.py
```

## 快速开始

```bash
python -m pip install -r requirements.txt
python scripts/generate_demo_data.py
python scripts/run_analysis.py
streamlit run app.py
python -m unittest discover -s tests
```

## 已生成样例结果

- 订单数：4,446
- 行为事件：115,915
- 实验曝光：47,571
- 净收入：1,129,187.81
- 复购率：51.28%
- 实验组相对转化提升：15.52%
- A/B 实验 p-value：4.5e-07

## 输出文件

- `outputs/kpi_snapshot.json`：核心 KPI。
- `outputs/monthly_revenue.csv`：月度收入与毛利趋势。
- `outputs/rfm_segments.csv`：用户 RFM 分层。
- `outputs/cohort_retention.csv`：月度留存矩阵。
- `outputs/funnel_metrics.csv`：漏斗转化。
- `outputs/ab_test_result.json`：A/B 实验结果。
- `outputs/coupon_strategy.csv`：优惠券策略建议。
- `outputs/insights_summary.md`：业务洞察摘要。

## 适配岗位

- 数据分析实习
- 商业分析实习
- 互联网运营实习
- 策略数据运营实习
- 增长分析实习
- 用户运营 / CRM 运营实习

## 可写入简历的表述

搭建电商增长策略分析系统，使用 Python 和 Streamlit 生成并分析订单、用户行为与 A/B 实验数据，覆盖 KPI 监控、RFM 用户分层、月度留存、访问-购买漏斗、实验 uplift 与优惠券效率评估；基于 4,446 笔订单、115,915 条行为事件和 47,571 条实验曝光生成策略报告，识别高价值用户贡献与实验组转化提升，并输出分客群 CRM 策略建议。

