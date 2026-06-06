from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd


@dataclass(frozen=True)
class FieldSpec:
    label: str
    required: bool
    aliases: tuple[str, ...]


ORDER_FIELDS: dict[str, FieldSpec] = {
    "customer_id": FieldSpec("用户ID", True, ("customer_id", "user_id", "uid", "buyer_id", "member_id", "用户id", "用户ID", "客户id", "客户ID")),
    "order_date": FieldSpec("下单时间", True, ("order_date", "created_at", "paid_at", "pay_time", "order_time", "下单时间", "支付时间", "订单时间")),
    "net_revenue": FieldSpec("订单金额", True, ("net_revenue", "amount", "order_amount", "gmv", "revenue", "sales", "订单金额", "支付金额", "实付金额", "销售额")),
    "order_id": FieldSpec("订单ID", False, ("order_id", "trade_id", "transaction_id", "订单id", "订单ID", "交易id")),
    "gross_margin": FieldSpec("毛利", False, ("gross_margin", "margin", "profit", "gross_profit", "毛利", "利润")),
    "coupon_spend": FieldSpec("优惠券成本", False, ("coupon_spend", "discount", "coupon", "coupon_amount", "优惠金额", "优惠券", "折扣")),
    "returned": FieldSpec("是否退货", False, ("returned", "is_returned", "refund", "refund_flag", "是否退货", "是否退款", "退货")),
    "channel": FieldSpec("渠道", False, ("channel", "source", "traffic_source", "渠道", "来源")),
    "category": FieldSpec("品类", False, ("category", "cat", "product_category", "品类", "类目")),
    "device": FieldSpec("设备", False, ("device", "terminal", "platform", "设备", "终端")),
    "session_id": FieldSpec("会话ID", False, ("session_id", "sid", "session", "会话id", "会话ID")),
}

EVENT_FIELDS: dict[str, FieldSpec] = {
    "customer_id": FieldSpec("用户ID", True, ORDER_FIELDS["customer_id"].aliases),
    "event_type": FieldSpec("事件类型", True, ("event_type", "event", "action", "behavior", "事件类型", "行为类型", "事件")),
    "event_time": FieldSpec("事件时间", True, ("event_time", "time", "created_at", "timestamp", "事件时间", "行为时间", "发生时间")),
    "session_id": FieldSpec("会话ID", False, ORDER_FIELDS["session_id"].aliases),
    "channel": FieldSpec("渠道", False, ORDER_FIELDS["channel"].aliases),
    "device": FieldSpec("设备", False, ORDER_FIELDS["device"].aliases),
    "category": FieldSpec("品类", False, ORDER_FIELDS["category"].aliases),
}

AB_FIELDS: dict[str, FieldSpec] = {
    "variant": FieldSpec("实验组别", True, ("variant", "group", "ab_variant", "experiment_group", "实验组", "实验组别", "分组")),
    "converted": FieldSpec("转化结果", True, ("converted", "conversion", "is_converted", "purchase", "转化", "是否转化", "购买")),
    "customer_id": FieldSpec("用户ID", False, ORDER_FIELDS["customer_id"].aliases),
    "session_id": FieldSpec("会话ID", False, ORDER_FIELDS["session_id"].aliases),
    "net_revenue": FieldSpec("收入", False, ORDER_FIELDS["net_revenue"].aliases),
    "coupon_spend": FieldSpec("优惠券成本", False, ORDER_FIELDS["coupon_spend"].aliases),
}


def read_table(file: BinaryIO, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file)
    if suffix in {".xlsx", ".xls"}:
        data = file.read()
        return pd.read_excel(BytesIO(data))
    raise ValueError("仅支持 CSV、XLSX 或 XLS 文件")


def guess_mapping(df: pd.DataFrame, specs: dict[str, FieldSpec]) -> dict[str, str | None]:
    normalized = {_normalize_column(col): col for col in df.columns}
    mapping: dict[str, str | None] = {}
    for field, spec in specs.items():
        selected = None
        for alias in spec.aliases:
            selected = normalized.get(_normalize_column(alias))
            if selected is not None:
                break
        mapping[field] = selected
    return mapping


def validate_mapping(mapping: dict[str, str | None], specs: dict[str, FieldSpec], table_name: str) -> list[str]:
    errors = []
    for field, spec in specs.items():
        if spec.required and not mapping.get(field):
            errors.append(f"{table_name} 缺少必填字段：{spec.label}")
    if specs is AB_FIELDS and not (mapping.get("customer_id") or mapping.get("session_id")):
        errors.append("A/B实验表至少需要 用户ID 或 会话ID 之一")
    return errors


def canonicalize_orders(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    out = pd.DataFrame()
    out["customer_id"] = _as_text(df[mapping["customer_id"]])
    out["order_date"] = pd.to_datetime(df[mapping["order_date"]], errors="coerce")
    out["net_revenue"] = _as_number(df[mapping["net_revenue"]])
    out["order_id"] = _optional_text(df, mapping, "order_id", prefix="O")
    out["gross_margin"] = _optional_number(df, mapping, "gross_margin", out["net_revenue"] * 0.35)
    out["coupon_spend"] = _optional_number(df, mapping, "coupon_spend", 0.0)
    out["returned"] = _optional_bool(df, mapping, "returned", 0)
    out["channel"] = _optional_text(df, mapping, "channel", default="unknown")
    out["category"] = _optional_text(df, mapping, "category", default="unknown")
    out["device"] = _optional_text(df, mapping, "device", default="unknown")
    out["session_id"] = _optional_text(df, mapping, "session_id", prefix="S")
    out = out.dropna(subset=["customer_id", "order_date", "net_revenue"])
    return out.reset_index(drop=True)


def canonicalize_events(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    out = pd.DataFrame()
    out["customer_id"] = _as_text(df[mapping["customer_id"]])
    out["event_type"] = _as_text(df[mapping["event_type"]]).str.strip().str.lower()
    out["event_time"] = pd.to_datetime(df[mapping["event_time"]], errors="coerce")
    out["session_id"] = _optional_text(df, mapping, "session_id", prefix="S")
    out["channel"] = _optional_text(df, mapping, "channel", default="unknown")
    out["device"] = _optional_text(df, mapping, "device", default="unknown")
    out["category"] = _optional_text(df, mapping, "category", default="unknown")
    out = out.dropna(subset=["customer_id", "event_type", "event_time"])
    return out.reset_index(drop=True)


def canonicalize_ab_test(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    out = pd.DataFrame()
    out["variant"] = _as_text(df[mapping["variant"]]).str.strip().str.lower()
    out["converted"] = _as_bool(df[mapping["converted"]])
    out["customer_id"] = _optional_text(df, mapping, "customer_id", default="")
    out["session_id"] = _optional_text(df, mapping, "session_id", prefix="S")
    out["net_revenue"] = _optional_number(df, mapping, "net_revenue", 0.0)
    out["coupon_spend"] = _optional_number(df, mapping, "coupon_spend", 0.0)
    out = out.dropna(subset=["variant", "converted"])
    return out.reset_index(drop=True)


def _normalize_column(value: object) -> str:
    return str(value).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _as_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().replace({"nan": ""})


def _as_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(float)


def _as_bool(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip().str.lower()
    truthy = {"1", "true", "yes", "y", "是", "已转化", "购买", "purchase", "converted"}
    return text.isin(truthy).astype(int)


def _optional_text(df: pd.DataFrame, mapping: dict[str, str | None], field: str, default: str | None = None, prefix: str | None = None) -> pd.Series:
    column = mapping.get(field)
    if column:
        return _as_text(df[column])
    if prefix:
        return pd.Series([f"{prefix}{idx + 1:06d}" for idx in range(len(df))])
    return pd.Series([default or "unknown"] * len(df))


def _optional_number(df: pd.DataFrame, mapping: dict[str, str | None], field: str, default: float | pd.Series) -> pd.Series:
    column = mapping.get(field)
    if column:
        return _as_number(df[column])
    if isinstance(default, pd.Series):
        return default.astype(float)
    return pd.Series([float(default)] * len(df))


def _optional_bool(df: pd.DataFrame, mapping: dict[str, str | None], field: str, default: int) -> pd.Series:
    column = mapping.get(field)
    if column:
        return _as_bool(df[column])
    return pd.Series([int(default)] * len(df))

