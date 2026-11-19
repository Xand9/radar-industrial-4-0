"""Testa aprovação da base válida e detecção de problemas controlados."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gerar_base import generate_database  # noqa: E402
from validar_qualidade import validate  # noqa: E402


def write_tables(tables, directory: Path) -> None:
    for name, frame in tables.items():
        frame.to_csv(directory / f"{name}.csv", index=False)


def main() -> None:
    options = dict(
        days=2,
        machines_count=3,
        seed=321,
        end=datetime(2026, 11, 12, 18, tzinfo=timezone.utc),
        telemetry_interval_minutes=30,
        wear_interval_hours=4,
        production_interval_hours=2,
        sale_probability=0.8,
    )
    with tempfile.TemporaryDirectory() as temp:
        valid_dir = Path(temp) / "valid"
        valid_dir.mkdir()
        valid = generate_database(**options)
        write_tables(valid, valid_dir)
        _, _, valid_issues, _ = validate(valid_dir)
        assert valid_issues.empty, valid_issues.to_dict(orient="records")

        invalid_dir = Path(temp) / "invalid"
        invalid_dir.mkdir()
        invalid = generate_database(**options)
        invalid["production_events"].loc[0, "qty_rejected"] = invalid["production_events"].loc[0, "qty_produced"] + 10
        invalid["production_events"].loc[1, "machine_id"] = "machine-does-not-exist"
        invalid["sales_orders"] = invalid["sales_orders"].copy()
        invalid["sales_orders"].loc[0, "total_amount"] = -1
        invalid["parts_wear"] = invalid["parts_wear"].copy()
        invalid["parts_wear"].loc[0, "wear_pct"] = 120
        write_tables(invalid, invalid_dir)
        _, _, invalid_issues, _ = validate(invalid_dir)
        rules = " | ".join(invalid_issues["rule"].tolist())
        assert "Rejeição maior que produção" in rules
        assert "machine_id órfão" in rules
        assert "total_amount não pode ser negativo" in rules
        assert "Desgaste deve estar entre 0 e 100%" in rules
        print("OK: base válida aprovada e problemas controlados detectados.")


if __name__ == "__main__":
    main()
