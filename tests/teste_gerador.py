"""Teste estrutural do gerador oficial. Execute: python tests/teste_gerador.py"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gerar_base import generate_database  # noqa: E402


def main() -> None:
    args = dict(
        days=2,
        machines_count=3,
        seed=123,
        end=datetime(2026, 11, 12, 18, tzinfo=timezone.utc),
        telemetry_interval_minutes=30,
        wear_interval_hours=4,
        production_interval_hours=2,
        sale_probability=0.8,
    )
    first = generate_database(**args)
    second = generate_database(**args)

    assert set(first) == {
        "machines",
        "production_events",
        "sales_orders",
        "machine_telemetry",
        "parts_wear",
        "wear_events",
    }
    for name in first:
        assert not first[name].empty, name
        pd.testing.assert_frame_equal(first[name], second[name])

    machines = set(first["machines"]["machine_id"])
    production_batches = set(first["production_events"]["batch_id"])
    for name in ["production_events", "machine_telemetry", "parts_wear", "wear_events"]:
        assert set(first[name]["machine_id"]).issubset(machines), name
    assert set(first["sales_orders"]["batch_id"]).issubset(production_batches)

    assert first["machines"]["machine_id"].is_unique
    assert first["production_events"]["production_id"].is_unique
    assert first["production_events"]["batch_id"].is_unique
    assert first["sales_orders"]["order_id"].is_unique
    assert first["machine_telemetry"]["telemetry_id"].is_unique
    assert first["parts_wear"]["component_id"].is_unique
    assert first["wear_events"]["wear_event_id"].is_unique

    production = first["production_events"]
    assert (production["qty_rejected"] <= production["qty_produced"]).all()
    assert (first["parts_wear"]["wear_pct"].between(0, 100)).all()
    assert (first["wear_events"]["wear_pct"].between(0, 100)).all()
    print("OK: gerador reproduzível, seis tabelas e relacionamentos válidos.")


if __name__ == "__main__":
    main()
