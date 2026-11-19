"""Consultas equivalentes às do Supabase usando os seis CSVs locais."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"
TABLES = ["machines", "production_events", "sales_orders", "machine_telemetry", "wear_events", "parts_wear"]
DATE_COLUMNS = {
    "machines": ["installed_at", "created_at"],
    "production_events": ["started_at", "ended_at", "recorded_at"],
    "sales_orders": ["created_at"],
    "machine_telemetry": ["recorded_at"],
    "wear_events": ["measured_at"],
    "parts_wear": ["last_inspection_at"],
}


def table(name: str) -> pd.DataFrame:
    if name not in TABLES:
        raise ValueError(f"Tabela local inválida: {name}")
    path = BASE_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Base local não encontrada: {path}")
    frame = pd.read_csv(path)
    for column in DATE_COLUMNS.get(name, []):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    return frame


def between(frame: pd.DataFrame, column: str, start, end) -> pd.DataFrame:
    values = pd.to_datetime(frame[column], errors="coerce", utc=True)
    return frame[(values >= pd.Timestamp(start)) & (values < pd.Timestamp(end))].copy()


def machines() -> pd.DataFrame:
    return table("machines").sort_values("machine_code")


def production(start, end) -> pd.DataFrame:
    return between(table("production_events"), "ended_at", start, end).sort_values("ended_at")


def sales(start, end) -> pd.DataFrame:
    return between(table("sales_orders"), "created_at", start, end).sort_values("created_at")


def telemetry_summary(start, end) -> pd.DataFrame:
    telemetry = between(table("machine_telemetry"), "recorded_at", start, end)
    telemetry = telemetry.merge(machines()[["machine_id", "machine_code"]], on="machine_id", how="left")
    if telemetry.empty:
        return pd.DataFrame()
    return telemetry.groupby("machine_code", as_index=False).agg(
        n_leituras=("telemetry_id", "count"), temp_media=("temperature_c", "mean"),
        temp_max=("temperature_c", "max"), vib_media=("vibration_mm_s", "mean"),
        vib_max=("vibration_mm_s", "max"), energia_media_kw=("energy_kw", "mean"),
        pressao_media=("pressure_bar", "mean"), rpm_medio=("rpm", "mean"),
        n_atencao=("machine_status", lambda s: s.astype(str).str.upper().eq("ATENCAO").sum()),
        n_critico=("machine_status", lambda s: s.astype(str).str.upper().eq("CRITICO").sum()),
    )


def _pandas_frequency(bucket: str) -> str:
    return {"1 minute": "1min", "5 minutes": "5min", "15 minutes": "15min",
            "1 hour": "1h", "6 hours": "6h"}.get(bucket, "1h")


def telemetry_series(start, end, bucket: str) -> pd.DataFrame:
    telemetry = between(table("machine_telemetry"), "recorded_at", start, end)
    telemetry = telemetry.merge(machines()[["machine_id", "machine_code"]], on="machine_id", how="left")
    if telemetry.empty:
        return pd.DataFrame()
    telemetry["bucket"] = telemetry["recorded_at"].dt.floor(_pandas_frequency(bucket))
    return telemetry.groupby(["machine_code", "bucket"], as_index=False).agg(
        temperature_c=("temperature_c", "mean"), vibration_mm_s=("vibration_mm_s", "mean"),
        energy_kw=("energy_kw", "mean"), pressure_bar=("pressure_bar", "mean"), rpm=("rpm", "mean"),
    )


def telemetry_latest() -> pd.DataFrame:
    telemetry = table("machine_telemetry").sort_values("recorded_at").drop_duplicates("machine_id", keep="last")
    return telemetry.merge(machines()[["machine_id", "machine_code", "machine_name"]], on="machine_id", how="left")


def current_wear() -> pd.DataFrame:
    return table("parts_wear")


def wear_history(start, end, bucket: str) -> pd.DataFrame:
    wear = between(table("wear_events"), "measured_at", start, end)
    if wear.empty:
        return wear
    wear["measured_at"] = wear["measured_at"].dt.floor(_pandas_frequency(bucket))
    return wear.groupby(["machine_id", "component_code", "component_name", "measured_at"], as_index=False).agg(
        wear_pct=("wear_pct", "max"), estimated_remaining_hours=("estimated_remaining_hours", "min")
    )


def pulse() -> pd.DataFrame:
    telemetry, production, sales_df, wear = table("machine_telemetry"), table("production_events"), table("sales_orders"), table("wear_events")
    latest = telemetry["recorded_at"].max()
    return pd.DataFrame([{
        "ultima_telemetria": latest,
        "telemetria_1min": int((telemetry["recorded_at"] > latest - pd.Timedelta(minutes=1)).sum()),
        "ultima_producao": production["ended_at"].max(),
        "producao_5min": int((production["recorded_at"] > production["recorded_at"].max() - pd.Timedelta(minutes=5)).sum()),
        "ultima_venda": sales_df["created_at"].max(), "ultimo_desgaste": wear["measured_at"].max(),
        "agora_banco": latest,
    }])


def counts() -> pd.DataFrame:
    return pd.DataFrame([{"tabela": name, "registros": len(table(name))} for name in TABLES])


def columns() -> pd.DataFrame:
    rows = []
    for name in TABLES:
        for column, dtype in table(name).dtypes.items():
            rows.append({"tabela": name, "coluna": column, "tipo": str(dtype), "aceita_nulo": "SIM"})
    return pd.DataFrame(rows)


def foreign_keys() -> pd.DataFrame:
    return pd.DataFrame([
        ["production_events", "machine_id", "machines", "machine_id"],
        ["sales_orders", "batch_id", "production_events", "batch_id"],
        ["machine_telemetry", "machine_id", "machines", "machine_id"],
        ["wear_events", "machine_id", "machines", "machine_id"],
        ["parts_wear", "machine_id", "machines", "machine_id"],
    ], columns=["tabela", "coluna", "referencia", "coluna_referencia"])


def filter_options() -> dict:
    production_df, sales_df = table("production_events"), table("sales_orders")
    return {
        "produtos": sorted(production_df["product_name"].dropna().astype(str).unique()),
        "turnos": sorted(production_df["shift_name"].dropna().astype(str).unique()),
        "canais": sorted(sales_df["sales_channel"].dropna().astype(str).unique()),
        "regioes": sorted(sales_df["customer_region"].dropna().astype(str).unique()),
    }


def sample(name: str, size: int = 10) -> pd.DataFrame:
    date_column = {"machines": "created_at", "production_events": "recorded_at", "sales_orders": "created_at",
                   "machine_telemetry": "recorded_at", "wear_events": "measured_at", "parts_wear": "last_inspection_at"}[name]
    return table(name).sort_values(date_column, ascending=False).head(size)
