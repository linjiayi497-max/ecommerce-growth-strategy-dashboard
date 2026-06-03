from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_growth.reporting import build_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build e-commerce growth analysis outputs.")
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--output-dir", default=str(ROOT / "outputs"))
    args = parser.parse_args()

    outputs = build_outputs(args.data_dir, args.output_dir)
    kpis = outputs["kpi_snapshot"]
    experiment = outputs["ab_test_result"]
    print(
        "analysis complete "
        f"net_revenue={kpis['net_revenue']:,} "
        f"orders={kpis['orders']:,} "
        f"ab_decision={experiment['recommendation']}"
    )


if __name__ == "__main__":
    main()

