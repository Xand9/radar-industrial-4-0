"""Gerador reproduzível da base sintética Industrial 4.0.

Gera seis arquivos CSV relacionados e um metadata.json com os parâmetros e
volumes da execução. O gerador não depende do Supabase.

Exemplo:
    python gerar_base.py --dias 30 --maquinas 4 --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


PRODUCTS = [
    ("PRD-100", "Componente Automotivo A", 85.0, 32.0),
    ("PRD-200", "Conjunto Mecânico B", 145.0, 61.0),
    ("PRD-300", "Peça Industrial C", 210.0, 94.0),
    ("PRD-400", "Módulo Eletrônico D", 320.0, 155.0),
    ("PRD-500", "Kit de Montagem E", 58.0, 21.0),
]

COMPONENTS = [
    ("ROLAMENTO", "Rolamento principal"),
    ("MOTOR", "Motor elétrico"),
    ("CORREIA", "Correia de transmissão"),
]

MACHINE_TEMPLATES = [
    ("CNC", "Centro de Usinagem CNC", "USINAGEM", "CNC", 120),
    ("PRE", "Prensa Hidráulica", "ESTAMPARIA", "PRENSA", 180),
    ("MON", "Linha de Montagem", "MONTAGEM", "MONTAGEM", 95),
    ("PIN", "Cabine de Pintura", "ACABAMENTO", "PINTURA", 80),
    ("SOL", "Célula de Soldagem", "SOLDAGEM", "SOLDA", 110),
    ("EMB", "Linha de Embalagem", "EMBALAGEM", "EMBALAGEM", 150),
]

TABLE_ORDER = [
    "machines",
    "production_events",
    "sales_orders",
    "machine_telemetry",
    "parts_wear",
    "wear_events",
]


@dataclass(frozen=True)
class GeneratorConfig:
    start: str
    end: str
    days: int
    machines: int
    seed: int
    telemetry_interval_minutes: int
    wear_interval_hours: int
    production_interval_hours: int
    sale_probability: float
    output_directory: str


def deterministic_uuid(seed: int, category: str, value: str | int) -> str:
    """UUID estável: os mesmos parâmetros geram as mesmas chaves."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"industria40:{seed}:{category}:{value}"))


def shift_name(hour: int) -> str:
    if 6 <= hour < 14:
        return "MANHA"
    if 14 <= hour < 22:
        return "TARDE"
    return "NOITE"


def hourly_factor(hour: int) -> float:
    if 7 <= hour < 11:
        return 1.08
    if 11 <= hour < 14:
        return 0.98
    if 14 <= hour < 18:
        return 1.03
    if hour >= 22 or hour < 6:
        return 0.78
    return 0.92


def parse_end(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def generate_machines(count: int, start: datetime, seed: int) -> pd.DataFrame:
    rows = []
    for index in range(count):
        prefix, name, line, machine_type, capacity = MACHINE_TEMPLATES[index % len(MACHINE_TEMPLATES)]
        sequence = index + 1
        cycle = index // len(MACHINE_TEMPLATES) + 1
        rows.append(
            {
                "machine_id": deterministic_uuid(seed, "machine", sequence),
                "machine_code": f"{prefix}-{cycle:02d}",
                "machine_name": f"{name} {cycle:02d}",
                "production_line": line,
                "machine_type": machine_type,
                "nominal_capacity_per_hour": capacity + (cycle - 1) * 5,
                "installed_at": date(2019 + index % 5, 1 + index % 12, 1 + (index * 3) % 27),
                "machine_status": "OPERANDO",
                "created_at": start,
            }
        )
    return pd.DataFrame(rows)


def generate_production_and_sales(
    machines: pd.DataFrame,
    start: datetime,
    end: datetime,
    seed: int,
    production_interval_hours: int,
    sale_probability: float,
    rng: random.Random,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    production_rows: list[dict] = []
    sales_rows: list[dict] = []
    current = start.replace(minute=0, second=0, microsecond=0)
    production_id = 1
    order_id = 1

    while current <= end:
        for _, machine in machines.iterrows():
            product_code, product_name, price, base_cost = rng.choice(PRODUCTS)
            capacity_interval = machine["nominal_capacity_per_hour"] * production_interval_hours
            expected = capacity_interval * hourly_factor(current.hour)
            produced = max(1, int(rng.gauss(expected, max(1, capacity_interval * 0.08))))
            rejection_probability = 0.065 if current.hour >= 22 or current.hour < 6 else 0.035
            if machine["machine_type"] == "PRENSA":
                rejection_probability += 0.012
            rejected = sum(rng.random() < rejection_probability for _ in range(produced))
            batch_id = deterministic_uuid(seed, "batch", production_id)
            ended_at = current
            started_at = ended_at - timedelta(hours=production_interval_hours)
            downtime = round(rng.uniform(0, 8 * production_interval_hours), 2)
            unit_cost = round(base_cost * rng.uniform(0.92, 1.13), 2)

            production_rows.append(
                {
                    "production_id": production_id,
                    "batch_id": batch_id,
                    "machine_id": machine["machine_id"],
                    "product_code": product_code,
                    "product_name": product_name,
                    "shift_name": shift_name(current.hour),
                    "qty_produced": produced,
                    "qty_rejected": rejected,
                    "downtime_minutes": downtime,
                    "cycle_time_seconds": round(rng.uniform(12, 95), 2),
                    "energy_kwh": round(rng.uniform(3, 24) * production_interval_hours, 3),
                    "unit_cost": unit_cost,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "recorded_at": ended_at,
                }
            )

            if rng.random() < sale_probability:
                sold = rng.randint(max(1, int(produced * 0.15)), max(2, int(produced * 0.75)))
                unit_price = round(price * rng.uniform(0.94, 1.12), 2)
                sales_rows.append(
                    {
                        "order_id": order_id,
                        "order_number": f"PED-{order_id:08d}",
                        "batch_id": batch_id,
                        "product_code": product_code,
                        "product_name": product_name,
                        "sales_channel": rng.choice(
                            ["E-COMMERCE", "DISTRIBUIDOR", "VENDA_DIRETA", "REPRESENTANTE"]
                        ),
                        "qty_sold": sold,
                        "unit_price": unit_price,
                        "total_amount": round(sold * unit_price, 2),
                        "order_status": rng.choices(
                            ["FATURADO", "PENDENTE", "ENVIADO", "CANCELADO"],
                            weights=[65, 15, 17, 3],
                            k=1,
                        )[0],
                        "customer_region": rng.choice(
                            ["SUDESTE", "SUL", "CENTRO-OESTE", "NORDESTE", "NORTE"]
                        ),
                        "created_at": ended_at,
                    }
                )
                order_id += 1
            production_id += 1
        current += timedelta(hours=production_interval_hours)

    return pd.DataFrame(production_rows), pd.DataFrame(sales_rows)


def generate_telemetry(
    machines: pd.DataFrame,
    start: datetime,
    end: datetime,
    interval_minutes: int,
    rng: random.Random,
) -> pd.DataFrame:
    rows = []
    current = start
    telemetry_id = 1
    while current <= end:
        elapsed_days = (current - start).total_seconds() / 86400
        for machine_index, (_, machine) in enumerate(machines.iterrows()):
            progressive_stress = elapsed_days * (0.015 + machine_index * 0.002)
            temperature = rng.uniform(58, 78) + progressive_stress
            vibration = rng.uniform(0.35, 3.8) + progressive_stress * 0.12
            if machine["machine_type"] == "PRENSA":
                vibration += 0.8
            status = (
                "CRITICO"
                if temperature >= 90 or vibration >= 7
                else "ATENCAO"
                if temperature >= 80 or vibration >= 4.5
                else "OPERANDO"
            )
            rows.append(
                {
                    "telemetry_id": telemetry_id,
                    "machine_id": machine["machine_id"],
                    "temperature_c": round(temperature, 2),
                    "vibration_mm_s": round(vibration, 3),
                    "energy_kw": round(rng.uniform(2, 15), 3),
                    "pressure_bar": round(rng.uniform(4, 10), 2),
                    "rpm": rng.randint(800, 3500),
                    "machine_status": status,
                    "recorded_at": current,
                }
            )
            telemetry_id += 1
        current += timedelta(minutes=interval_minutes)
    return pd.DataFrame(rows)


def generate_wear(
    machines: pd.DataFrame,
    start: datetime,
    end: datetime,
    interval_hours: int,
    rng: random.Random,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    snapshots: dict[tuple[str, str], dict] = {}
    wear_rows: list[dict] = []
    current = start.replace(minute=0, second=0, microsecond=0)
    wear_event_id = 1

    for machine_index, (_, machine) in enumerate(machines.iterrows()):
        for component_index, (component_code, component_name) in enumerate(COMPONENTS):
            initial = rng.uniform(8, 42) + machine_index * 1.3 + component_index * 0.8
            if machine["machine_type"] == "PRENSA" and component_code == "ROLAMENTO":
                initial = 64.0
            snapshots[(machine["machine_id"], component_code)] = {
                "wear": min(initial, 78),
                "component_name": component_name,
            }

    while current <= end:
        for machine_index, (_, machine) in enumerate(machines.iterrows()):
            for component_code, component_name in COMPONENTS:
                key = (machine["machine_id"], component_code)
                wear = snapshots[key]["wear"]
                growth = rng.uniform(0.012, 0.085) * interval_hours
                if machine["machine_type"] == "PRENSA" and component_code == "ROLAMENTO":
                    growth *= 1.65
                wear = min(99.5, wear + growth)
                snapshots[key]["wear"] = wear
                remaining = max(5, (100 - wear) * rng.uniform(18, 30))
                wear_rows.append(
                    {
                        "wear_event_id": wear_event_id,
                        "machine_id": machine["machine_id"],
                        "component_code": component_code,
                        "component_name": component_name,
                        "wear_pct": round(wear, 2),
                        "vibration_mm_s": round(0.8 + wear * 0.065 + rng.uniform(-0.25, 0.25), 3),
                        "temperature_c": round(52 + wear * 0.35 + rng.uniform(-1.5, 1.5), 2),
                        "estimated_remaining_hours": round(remaining, 2),
                        "measured_at": current,
                    }
                )
                wear_event_id += 1
        current += timedelta(hours=interval_hours)

    parts_rows = []
    component_id = 1
    last_measurements = pd.DataFrame(wear_rows).sort_values("measured_at").groupby(
        ["machine_id", "component_code"], as_index=False
    ).tail(1)
    for _, row in last_measurements.iterrows():
        parts_rows.append(
            {
                "component_id": component_id,
                "machine_id": row["machine_id"],
                "component_code": row["component_code"],
                "component_name": row["component_name"],
                "wear_pct": row["wear_pct"],
                "warning_threshold_pct": 75.0,
                "critical_threshold_pct": 90.0,
                "estimated_remaining_hours": row["estimated_remaining_hours"],
                "last_inspection_at": row["measured_at"],
            }
        )
        component_id += 1

    return pd.DataFrame(parts_rows), pd.DataFrame(wear_rows)


def generate_database(
    *,
    days: int,
    machines_count: int,
    seed: int,
    end: datetime,
    telemetry_interval_minutes: int,
    wear_interval_hours: int,
    production_interval_hours: int,
    sale_probability: float,
) -> dict[str, pd.DataFrame]:
    if days < 1:
        raise ValueError("--dias deve ser maior ou igual a 1.")
    if machines_count < 1 or machines_count > 24:
        raise ValueError("--maquinas deve estar entre 1 e 24.")
    if telemetry_interval_minutes < 1:
        raise ValueError("--intervalo-telemetria-min deve ser positivo.")
    if wear_interval_hours < 1 or production_interval_hours < 1:
        raise ValueError("Intervalos de desgaste e produção devem ser positivos.")
    if not 0 <= sale_probability <= 1:
        raise ValueError("--probabilidade-venda deve estar entre 0 e 1.")

    start = end - timedelta(days=days)
    rng = random.Random(seed)
    machines = generate_machines(machines_count, start, seed)
    production, sales = generate_production_and_sales(
        machines,
        start,
        end,
        seed,
        production_interval_hours,
        sale_probability,
        rng,
    )
    telemetry = generate_telemetry(
        machines, start, end, telemetry_interval_minutes, rng
    )
    parts, wear = generate_wear(
        machines, start, end, wear_interval_hours, rng
    )
    return {
        "machines": machines,
        "production_events": production,
        "sales_orders": sales,
        "machine_telemetry": telemetry,
        "parts_wear": parts,
        "wear_events": wear,
    }


def write_database(
    tables: dict[str, pd.DataFrame],
    output_directory: Path,
    config: GeneratorConfig,
    overwrite: bool,
) -> None:
    resolved = output_directory.resolve()
    if resolved == Path(resolved.anchor):
        raise ValueError("Diretório de saída não pode ser a raiz do disco.")
    if output_directory.exists() and any(output_directory.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"{output_directory} não está vazio. Use --sobrescrever para substituir."
            )
        shutil.rmtree(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    volumes: dict[str, int] = {}
    for table_name in TABLE_ORDER:
        frame = tables[table_name]
        frame.to_csv(output_directory / f"{table_name}.csv", index=False, encoding="utf-8")
        volumes[table_name] = len(frame)

    metadata = {
        "generator": "gerar_base.py",
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parameters": asdict(config),
        "volumes": volumes,
        "files": [f"{name}.csv" for name in TABLE_ORDER],
    }
    (output_directory / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera a base sintética reproduzível do projeto Industrial 4.0."
    )
    parser.add_argument("--dias", type=int, default=30, help="Período gerado em dias.")
    parser.add_argument("--maquinas", type=int, default=4, help="Quantidade de máquinas (1 a 24).")
    parser.add_argument("--seed", type=int, default=42, help="Semente de aleatoriedade.")
    parser.add_argument(
        "--fim",
        default="2026-11-12T18:00:00+00:00",
        help="Fim do período em ISO 8601. O padrão fixo garante reprodução.",
    )
    parser.add_argument(
        "--intervalo-telemetria-min", type=int, default=5, help="Minutos entre leituras de telemetria."
    )
    parser.add_argument(
        "--intervalo-desgaste-h", type=int, default=1, help="Horas entre medições de desgaste."
    )
    parser.add_argument(
        "--intervalo-producao-h", type=int, default=1, help="Horas entre lotes por máquina."
    )
    parser.add_argument(
        "--probabilidade-venda", type=float, default=0.82, help="Probabilidade de um lote gerar pedido."
    )
    parser.add_argument(
        "--saida", type=Path, default=Path("data/generated"), help="Diretório dos CSVs."
    )
    parser.add_argument(
        "--sobrescrever", action="store_true", help="Substitui o diretório de saída quando não estiver vazio."
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    end = parse_end(args.fim)
    start = end - timedelta(days=args.dias)
    config = GeneratorConfig(
        start=start.isoformat(),
        end=end.isoformat(),
        days=args.dias,
        machines=args.maquinas,
        seed=args.seed,
        telemetry_interval_minutes=args.intervalo_telemetria_min,
        wear_interval_hours=args.intervalo_desgaste_h,
        production_interval_hours=args.intervalo_producao_h,
        sale_probability=args.probabilidade_venda,
        output_directory=str(args.saida),
    )
    tables = generate_database(
        days=args.dias,
        machines_count=args.maquinas,
        seed=args.seed,
        end=end,
        telemetry_interval_minutes=args.intervalo_telemetria_min,
        wear_interval_hours=args.intervalo_desgaste_h,
        production_interval_hours=args.intervalo_producao_h,
        sale_probability=args.probabilidade_venda,
    )
    write_database(tables, args.saida, config, args.sobrescrever)
    print(f"Base gerada em: {args.saida.resolve()}")
    for name in TABLE_ORDER:
        print(f"- {name}.csv: {len(tables[name]):,} registros")
    print("- metadata.json: parâmetros e volumes da execução")


if __name__ == "__main__":
    main()
