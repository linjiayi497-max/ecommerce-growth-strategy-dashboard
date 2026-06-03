from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.data import generate_demo_dataset, save_demo_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce growth data.")
    parser.add_argument("--customers", type=int, default=3600)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    args = parser.parse_args()

    orders, events, ab_test = generate_demo_dataset(
        months=args.months,
        n_customers=args.customers,
        seed=args.seed,
    )
    save_demo_dataset(orders, events, ab_test, args.data_dir)
    print(f"generated orders={len(orders):,} events={len(events):,} exposures={len(ab_test):,}")


if __name__ == "__main__":
    main()

