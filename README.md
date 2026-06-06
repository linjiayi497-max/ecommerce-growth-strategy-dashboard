# GrowthLens 电商增长策略分析看板

GrowthLens 是一个面向互联网运营、增长分析、商业分析和数据分析实习岗位的电商增长分析产品。它既支持内置演示数据，也支持用户上传自己的 CSV/XLSX 数据，在浏览器中完成 KPI、RFM 用户分层、月度留存、转化漏斗、A/B 实验和优惠券策略分析。

在线访问链接：待部署后更新。

上传数据只用于当前会话分析，不写入服务器文件或仓库。演示数据为本地生成的模拟数据，代码为原创实现。

## 项目亮点

- 构造订单、用户行为事件和 A/B 实验曝光数据。
- 计算收入、订单数、AOV、复购率、毛利率、退货率等核心指标。
- 基于 RFM 识别高价值用户、潜力用户、流失风险用户等客群。
- 生成月度 cohort 留存矩阵，判断用户长期价值。
- 计算访问、商品浏览、加购、结算、购买漏斗转化和流失。
- 评估 A/B 实验转化率 uplift、p-value 和每 session 收入。
- 输出分客群优惠券与 CRM 策略建议。
- 提供 SQL 样例，便于面试讨论指标口径和数据分析逻辑。
- 支持上传订单表、用户行为表和可选 A/B 实验表。
- 支持字段映射，兼容不同公司常见字段命名。
- 支持导出 Excel 分析结果和 PDF 报告。

## 项目结构

```text
.
|-- app.py                         # Streamlit 产品入口
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
|   |-- exports.py                 # Excel/PDF 导出
|   `-- reporting.py               # 报告输出
|   `-- upload.py                  # 上传数据读取、字段映射和标准化
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

## 上传数据格式

订单表必填字段：

- 用户ID
- 下单时间
- 订单金额

用户行为表必填字段：

- 用户ID
- 事件类型
- 事件时间

A/B 实验表可选，若上传则必填：

- 实验组别
- 转化结果
- 用户ID 或 会话ID 至少一个

上传后系统会显示字段映射选择器，并自动识别 `user_id`、`amount`、`created_at`、`event_type` 等常见字段名。

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
