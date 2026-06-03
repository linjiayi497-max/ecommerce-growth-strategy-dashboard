from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


CHANNELS = ["paid_search", "organic", "social", "email", "affiliate", "direct"]
CATEGORIES = ["beauty", "electronics", "home", "apparel", "sports", "food"]
REGIONS = ["North", "East", "South", "West", "Central"]
AGE_BANDS = ["18-24", "25-34", "35-44", "45+"]
DEVICES = ["mobile", "desktop", "tablet"]


@dataclass(frozen=True)
class SegmentProfile:
    session_lambda: float
    product_view_rate: float
    cart_rate: float
    checkout_rate: float
    purchase_rate: float
    order_value_mean: float
    order_value_sigma: float
    margin_rate: float
    return_rate: float
    discount_rate: float


SEGMENT_PROFILES = {
    "champion": SegmentProfile(2.8, 0.86, 0.52, 0.68, 0.56, 360, 0.32, 0.42, 0.035, 0.05),
    "steady": SegmentProfile(1.7, 0.76, 0.38, 0.56, 0.39, 245, 0.38, 0.35, 0.055, 0.08),
    "deal_seeker": SegmentProfile(1.9, 0.81, 0.44, 0.58, 0.34, 210, 0.45, 0.29, 0.070, 0.15),
    "new_or_low": SegmentProfile(0.9, 0.64, 0.27, 0.46, 0.22, 160, 0.50, 0.31, 0.050, 0.11),
}


def _month_starts(start_date: str, months: int) -> pd.DatetimeIndex:
    return pd.date_range(pd.to_datetime(start_date), periods=months, freq="MS")


def _sample_order_value(rng: np.random.Generator, profile: SegmentProfile) -> float:
    mean_log = np.log(profile.order_value_mean) - profile.order_value_sigma**2 / 2
    value = rng.lognormal(mean_log, profile.order_value_sigma)
    return float(np.clip(value, 38, 2200))


def _event_row(
    session_id: str,
    customer_id: str,
    event_time: pd.Timestamp,
    channel: str,
    device: str,
    category: str,
    campaign: str,
    variant: str,
    event_type: str,
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "customer_id": customer_id,
        "event_time": event_time.isoformat(),
        "channel": channel,
        "device": device,
        "category": category,
        "campaign": campaign,
        "ab_variant": variant,
        "event_type": event_type,
    }


def generate_demo_dataset(
    start_date: str = "2025-01-01",
    months: int = 12,
    n_customers: int = 3600,
    seed: int = 2026,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate synthetic orders, event logs, and experiment exposure data."""
    rng = np.random.default_rng(seed)
    month_starts = _month_starts(start_date, months)
    customer_ids = [f"C{idx:05d}" for idx in range(1, n_customers + 1)]
    segments = rng.choice(
        list(SEGMENT_PROFILES.keys()),
        size=n_customers,
        p=[0.14, 0.38, 0.26, 0.22],
    )
    signup_offsets = rng.integers(0, max(months - 2, 1), size=n_customers)
    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "base_segment": segments,
            "signup_month": [month_starts[offset].strftime("%Y-%m") for offset in signup_offsets],
            "region": rng.choice(REGIONS, size=n_customers, p=[0.18, 0.28, 0.24, 0.16, 0.14]),
            "age_band": rng.choice(AGE_BANDS, size=n_customers, p=[0.22, 0.42, 0.24, 0.12]),
            "preferred_category": rng.choice(CATEGORIES, size=n_customers),
            "ab_variant": rng.choice(["control", "treatment"], size=n_customers, p=[0.5, 0.5]),
        }
    )

    events: list[dict[str, object]] = []
    orders: list[dict[str, object]] = []
    exposures: list[dict[str, object]] = []
    session_seq = 1
    order_seq = 1

    campaign_by_channel = {
        "paid_search": "always_on_search",
        "organic": "seo",
        "social": "summer_social",
        "email": "crm_lifecycle",
        "affiliate": "partner_cashback",
        "direct": "brand_direct",
    }

    for customer in customers.itertuples(index=False):
        signup_month = pd.to_datetime(f"{customer.signup_month}-01")
        active_months = [month for month in month_starts if month >= signup_month]
        profile = SEGMENT_PROFILES[customer.base_segment]

        for month_idx, month in enumerate(active_months):
            seasonality = 1.0 + 0.18 * np.sin((month.month - 1) / 12 * 2 * np.pi)
            lifecycle_boost = 1.25 if month_idx <= 1 else 1.0
            sessions_this_month = rng.poisson(profile.session_lambda * seasonality * lifecycle_boost)
            if sessions_this_month == 0 and rng.random() < 0.18:
                sessions_this_month = 1

            for _ in range(sessions_this_month):
                session_id = f"S{session_seq:07d}"
                session_seq += 1
                event_time = month + pd.Timedelta(days=int(rng.integers(0, 27)), hours=int(rng.integers(8, 23)))
                channel = rng.choice(CHANNELS, p=[0.24, 0.22, 0.18, 0.16, 0.10, 0.10])
                device = rng.choice(DEVICES, p=[0.68, 0.25, 0.07])
                category = rng.choice([customer.preferred_category, *CATEGORIES], p=[0.40, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10])
                campaign = campaign_by_channel[channel]
                variant = customer.ab_variant

                product_view_rate = profile.product_view_rate
                cart_rate = profile.cart_rate
                checkout_rate = profile.checkout_rate
                purchase_rate = profile.purchase_rate

                if variant == "treatment":
                    cart_rate += 0.035
                    checkout_rate += 0.025
                    purchase_rate += 0.030
                if channel in {"email", "affiliate"}:
                    purchase_rate += 0.025
                if device == "mobile":
                    checkout_rate -= 0.020

                event_types = ["visit"]
                if rng.random() < np.clip(product_view_rate, 0, 0.98):
                    event_types.append("product_view")
                    if rng.random() < np.clip(cart_rate, 0, 0.98):
                        event_types.append("add_to_cart")
                        if rng.random() < np.clip(checkout_rate, 0, 0.98):
                            event_types.append("checkout")
                            if rng.random() < np.clip(purchase_rate, 0, 0.98):
                                event_types.append("purchase")

                for step, event_type in enumerate(event_types):
                    events.append(
                        _event_row(
                            session_id,
                            customer.customer_id,
                            event_time + pd.Timedelta(minutes=step * int(rng.integers(1, 6))),
                            channel,
                            device,
                            category,
                            campaign,
                            variant,
                            event_type,
                        )
                    )

                converted = "purchase" in event_types
                gross_revenue = _sample_order_value(rng, profile) if converted else 0.0
                extra_discount = 0.035 if variant == "treatment" else 0.0
                channel_discount = 0.020 if channel == "affiliate" else 0.0
                discount_rate = np.clip(profile.discount_rate + extra_discount + channel_discount, 0.0, 0.35)
                coupon_spend = gross_revenue * discount_rate
                net_revenue = gross_revenue - coupon_spend
                gross_margin = net_revenue * profile.margin_rate - (8.0 if converted and device == "mobile" else 5.0)
                returned = bool(converted and rng.random() < profile.return_rate)

                exposures.append(
                    {
                        "session_id": session_id,
                        "customer_id": customer.customer_id,
                        "variant": variant,
                        "exposed_at": event_time.isoformat(),
                        "channel": channel,
                        "converted": int(converted),
                        "net_revenue": round(net_revenue, 2),
                        "coupon_spend": round(coupon_spend, 2),
                    }
                )

                if converted:
                    orders.append(
                        {
                            "order_id": f"O{order_seq:07d}",
                            "session_id": session_id,
                            "customer_id": customer.customer_id,
                            "order_date": event_time.isoformat(),
                            "channel": channel,
                            "device": device,
                            "category": category,
                            "campaign": campaign,
                            "ab_variant": variant,
                            "gross_revenue": round(gross_revenue, 2),
                            "coupon_spend": round(coupon_spend, 2),
                            "net_revenue": round(net_revenue, 2),
                            "gross_margin": round(gross_margin, 2),
                            "returned": int(returned),
                            "base_segment": customer.base_segment,
                        }
                    )
                    order_seq += 1

    orders_df = pd.DataFrame(orders)
    events_df = pd.DataFrame(events)
    ab_test_df = pd.DataFrame(exposures)
    return orders_df, events_df, ab_test_df


def save_demo_dataset(
    orders: pd.DataFrame,
    events: pd.DataFrame,
    ab_test: pd.DataFrame,
    data_dir: str | Path,
) -> None:
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    orders.to_csv(data_path / "demo_orders.csv", index=False)
    events.to_csv(data_path / "demo_events.csv", index=False)
    ab_test.to_csv(data_path / "demo_ab_test.csv", index=False)


def load_demo_dataset(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data_path = Path(data_dir)
    orders = pd.read_csv(data_path / "demo_orders.csv", parse_dates=["order_date"])
    events = pd.read_csv(data_path / "demo_events.csv", parse_dates=["event_time"])
    ab_test = pd.read_csv(data_path / "demo_ab_test.csv", parse_dates=["exposed_at"])
    return orders, events, ab_test

