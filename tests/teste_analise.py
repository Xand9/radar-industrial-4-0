"""Teste estrutural da análise exploratória."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analisar_dados import build_summaries, prepare_analysis  # noqa: E402
from gerar_base import generate_database  # noqa: E402


def main() -> None:
    raw = generate_database(
        days=7,
        machines_count=4,
        seed=404,
        end=datetime(2026, 11, 12, 18, tzinfo=timezone.utc),
        telemetry_interval_minutes=30,
        wear_interval_hours=4,
        production_interval_hours=2,
        sale_probability=0.8,
    )
    summaries = build_summaries(prepare_analysis(raw))
    required = {
        "executive_summary", "production_by_machine", "production_daily",
        "sales_by_product", "production_vs_sales", "telemetry_anomalies",
        "maintenance_priority", "wear_trends", "trends", "opportunities",
    }
    assert required.issubset(summaries)
    for name in required:
        assert not summaries[name].empty, name

    executive = summaries["executive_summary"].set_index("indicator")["value"]
    production = raw["production_events"]
    assert executive["Produção total"] == production["qty_produced"].sum()
    assert 0 <= executive["Taxa de rejeição"] <= 1
    assert len(summaries["opportunities"]) >= 3
    print("OK: estatísticas, tendências, anomalias e oportunidades geradas.")


if __name__ == "__main__":
    main()
