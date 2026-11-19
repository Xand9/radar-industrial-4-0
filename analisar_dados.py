"""Análise exploratória reproduzível da base Industrial 4.0.

Produz tabelas CSV, gráficos HTML interativos e relatório Markdown com
estatísticas, tendências, anomalias e oportunidades.

Exemplo:
    python analisar_dados.py --dados data/generated --saida reports/analysis
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


REQUIRED_TABLES = [
    "machines",
    "production_events",
    "sales_orders",
    "machine_telemetry",
    "parts_wear",
    "wear_events",
]

DATE_COLUMNS = {
    "machines": ["installed_at", "created_at"],
    "production_events": ["started_at", "ended_at", "recorded_at"],
    "sales_orders": ["created_at"],
    "machine_telemetry": ["recorded_at"],
    "parts_wear": ["last_inspection_at"],
    "wear_events": ["measured_at"],
}

COLORS = ["#19C6A3", "#4D8DFF", "#FFB84D", "#FF6078", "#9B7BFF", "#43D3FF"]


def load_data(data_directory: Path) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for table in REQUIRED_TABLES:
        path = data_directory / f"{table}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Arquivo obrigatório não encontrado: {path}")
        frame = pd.read_csv(path)
        for column in DATE_COLUMNS.get(table, []):
            if column in frame:
                frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
        tables[table] = frame
    return tables


def safe_divide(numerator, denominator):
    if isinstance(denominator, pd.Series):
        return numerator / denominator.replace(0, np.nan)
    return numerator / denominator if denominator else np.nan


def linear_trend(values: pd.Series) -> tuple[float, float]:
    """Retorna inclinação diária e variação percentual estimada do período."""
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) < 2:
        return 0.0, 0.0
    x = np.arange(len(clean), dtype=float)
    slope = float(np.polyfit(x, clean.to_numpy(dtype=float), 1)[0])
    mean = float(clean.mean())
    percent_period = slope * max(len(clean) - 1, 1) / mean if mean else 0.0
    return slope, percent_period


def prepare_analysis(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    machines = tables["machines"]
    production = tables["production_events"].merge(
        machines[["machine_id", "machine_code", "machine_name", "production_line", "nominal_capacity_per_hour"]],
        on="machine_id",
        how="left",
        validate="many_to_one",
    )
    production["approved"] = production["qty_produced"] - production["qty_rejected"]
    production["duration_hours"] = (
        production["ended_at"] - production["started_at"]
    ).dt.total_seconds() / 3600
    production["operating_hours"] = (
        production["duration_hours"] - production["downtime_minutes"] / 60
    ).clip(lower=0.001)
    production["production_cost"] = production["qty_produced"] * production["unit_cost"]
    production["rejection_cost"] = production["qty_rejected"] * production["unit_cost"]
    production["date"] = production["ended_at"].dt.floor("D")
    production["hour"] = production["ended_at"].dt.hour

    sales = tables["sales_orders"].copy()
    sales["valid_order"] = sales["order_status"].astype(str).str.upper() != "CANCELADO"
    sales["valid_revenue"] = np.where(sales["valid_order"], sales["total_amount"], 0.0)
    sales["valid_quantity"] = np.where(sales["valid_order"], sales["qty_sold"], 0)
    sales["date"] = sales["created_at"].dt.floor("D")

    telemetry = tables["machine_telemetry"].merge(
        machines[["machine_id", "machine_code", "machine_name"]],
        on="machine_id",
        how="left",
        validate="many_to_one",
    )
    telemetry["date"] = telemetry["recorded_at"].dt.floor("D")

    parts = tables["parts_wear"].merge(
        machines[["machine_id", "machine_code", "machine_name"]],
        on="machine_id",
        how="left",
        validate="many_to_one",
    )
    parts["risk_level"] = np.select(
        [
            parts["wear_pct"] >= parts["critical_threshold_pct"],
            parts["wear_pct"] >= parts["warning_threshold_pct"],
        ],
        ["CRITICO", "ATENCAO"],
        default="NORMAL",
    )

    wear = tables["wear_events"].merge(
        machines[["machine_id", "machine_code", "machine_name"]],
        on="machine_id",
        how="left",
        validate="many_to_one",
    )
    return {
        "machines": machines,
        "production": production,
        "sales": sales,
        "telemetry": telemetry,
        "parts": parts,
        "wear": wear,
    }


def build_summaries(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    production = data["production"]
    sales = data["sales"]
    telemetry = data["telemetry"]
    parts = data["parts"]
    wear = data["wear"]

    production_machine = production.groupby(
        ["machine_code", "machine_name", "production_line"], as_index=False
    ).agg(
        produced=("qty_produced", "sum"),
        approved=("approved", "sum"),
        rejected=("qty_rejected", "sum"),
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_minutes", lambda x: x.sum() / 60),
        production_cost=("production_cost", "sum"),
        rejection_cost=("rejection_cost", "sum"),
    )
    production_machine["rejection_rate"] = safe_divide(
        production_machine["rejected"], production_machine["produced"]
    )
    production_machine["approved_per_hour"] = safe_divide(
        production_machine["approved"], production_machine["operating_hours"]
    )

    production_shift = production.groupby("shift_name", as_index=False).agg(
        produced=("qty_produced", "sum"),
        approved=("approved", "sum"),
        rejected=("qty_rejected", "sum"),
        operating_hours=("operating_hours", "sum"),
        rejection_cost=("rejection_cost", "sum"),
    )
    production_shift["rejection_rate"] = safe_divide(
        production_shift["rejected"], production_shift["produced"]
    )
    production_shift["approved_per_hour"] = safe_divide(
        production_shift["approved"], production_shift["operating_hours"]
    )

    production_product = production.groupby(
        ["product_code", "product_name"], as_index=False
    ).agg(
        produced=("qty_produced", "sum"),
        approved=("approved", "sum"),
        rejected=("qty_rejected", "sum"),
        production_cost=("production_cost", "sum"),
        rejection_cost=("rejection_cost", "sum"),
    )
    production_product["rejection_rate"] = safe_divide(
        production_product["rejected"], production_product["produced"]
    )
    production_product["average_unit_cost"] = safe_divide(
        production_product["production_cost"], production_product["produced"]
    )

    production_daily = production.groupby("date", as_index=False).agg(
        production_records=("production_id", "count"),
        produced=("qty_produced", "sum"),
        approved=("approved", "sum"),
        rejected=("qty_rejected", "sum"),
        downtime_minutes=("downtime_minutes", "sum"),
        rejection_cost=("rejection_cost", "sum"),
    )
    production_daily["rejection_rate"] = safe_divide(
        production_daily["rejected"], production_daily["produced"]
    )
    typical_daily_records = production_daily["production_records"].median()
    production_daily["complete_day"] = (
        production_daily["production_records"] >= typical_daily_records * 0.8
    )

    valid_sales = sales[sales["valid_order"]]
    sales_product = valid_sales.groupby(
        ["product_code", "product_name"], as_index=False
    ).agg(
        orders=("order_id", "count"),
        quantity_sold=("valid_quantity", "sum"),
        revenue=("valid_revenue", "sum"),
    )
    sales_product["average_ticket"] = safe_divide(
        sales_product["revenue"], sales_product["orders"]
    )

    sales_channel = valid_sales.groupby("sales_channel", as_index=False).agg(
        orders=("order_id", "count"),
        quantity_sold=("valid_quantity", "sum"),
        revenue=("valid_revenue", "sum"),
    )
    sales_channel["average_ticket"] = safe_divide(
        sales_channel["revenue"], sales_channel["orders"]
    )

    sales_region = valid_sales.groupby("customer_region", as_index=False).agg(
        orders=("order_id", "count"),
        quantity_sold=("valid_quantity", "sum"),
        revenue=("valid_revenue", "sum"),
    )

    sales_daily = valid_sales.groupby("date", as_index=False).agg(
        orders=("order_id", "count"),
        quantity_sold=("valid_quantity", "sum"),
        revenue=("valid_revenue", "sum"),
    )

    production_sales = production_product.merge(
        sales_product[["product_code", "quantity_sold", "revenue"]],
        on="product_code",
        how="outer",
    ).fillna(0)
    production_sales["approved_minus_sold"] = (
        production_sales["approved"] - production_sales["quantity_sold"]
    )
    production_sales["sales_to_approved_ratio"] = safe_divide(
        production_sales["quantity_sold"], production_sales["approved"]
    )

    telemetry_machine = telemetry.groupby(
        ["machine_code", "machine_name"], as_index=False
    ).agg(
        readings=("telemetry_id", "count"),
        average_temperature=("temperature_c", "mean"),
        maximum_temperature=("temperature_c", "max"),
        average_vibration=("vibration_mm_s", "mean"),
        maximum_vibration=("vibration_mm_s", "max"),
        average_energy=("energy_kw", "mean"),
        average_pressure=("pressure_bar", "mean"),
        average_rpm=("rpm", "mean"),
        alert_readings=("machine_status", lambda x: x.astype(str).str.upper().ne("OPERANDO").sum()),
    )
    telemetry_machine["alert_rate"] = safe_divide(
        telemetry_machine["alert_readings"], telemetry_machine["readings"]
    )

    telemetry_daily = telemetry.groupby(["date", "machine_code"], as_index=False).agg(
        average_temperature=("temperature_c", "mean"),
        average_vibration=("vibration_mm_s", "mean"),
        average_energy=("energy_kw", "mean"),
    )

    telemetry_anomalies = detect_telemetry_anomalies(telemetry)

    maintenance_priority = parts.sort_values(
        ["wear_pct", "estimated_remaining_hours"], ascending=[False, True]
    )[[
        "machine_code", "machine_name", "component_code", "component_name",
        "wear_pct", "warning_threshold_pct", "critical_threshold_pct",
        "estimated_remaining_hours", "risk_level",
    ]]

    wear_trend = calculate_wear_trends(wear)
    complete_production_days = production_daily[production_daily["complete_day"]]
    trends = calculate_trends(complete_production_days, sales_daily, telemetry_daily, wear_trend)
    opportunities = identify_opportunities(
        production_machine,
        production_shift,
        production_sales,
        sales_channel,
        sales_region,
        telemetry_machine,
        maintenance_priority,
    )

    executive = pd.DataFrame(
        [
            {"indicator": "Produção total", "value": production["qty_produced"].sum(), "unit": "unidades"},
            {"indicator": "Produção aprovada", "value": production["approved"].sum(), "unit": "unidades"},
            {"indicator": "Taxa de rejeição", "value": safe_divide(production["qty_rejected"].sum(), production["qty_produced"].sum()), "unit": "proporção"},
            {"indicator": "Custo estimado do refugo", "value": production["rejection_cost"].sum(), "unit": "BRL"},
            {"indicator": "Pedidos válidos", "value": len(valid_sales), "unit": "pedidos"},
            {"indicator": "Faturamento", "value": valid_sales["valid_revenue"].sum(), "unit": "BRL"},
            {"indicator": "Ticket médio", "value": valid_sales["valid_revenue"].mean(), "unit": "BRL/pedido"},
            {"indicator": "Leituras de telemetria", "value": len(telemetry), "unit": "leituras"},
            {"indicator": "Leituras em alerta", "value": telemetry["machine_status"].astype(str).str.upper().ne("OPERANDO").sum(), "unit": "leituras"},
            {"indicator": "Componentes em atenção/críticos", "value": parts["risk_level"].ne("NORMAL").sum(), "unit": "componentes"},
        ]
    )

    return {
        "executive_summary": executive,
        "production_by_machine": production_machine,
        "production_by_shift": production_shift,
        "production_by_product": production_product,
        "production_daily": production_daily,
        "sales_by_product": sales_product,
        "sales_by_channel": sales_channel,
        "sales_by_region": sales_region,
        "sales_daily": sales_daily,
        "production_vs_sales": production_sales,
        "telemetry_by_machine": telemetry_machine,
        "telemetry_daily": telemetry_daily,
        "telemetry_anomalies": telemetry_anomalies,
        "maintenance_priority": maintenance_priority,
        "wear_trends": wear_trend,
        "trends": trends,
        "opportunities": opportunities,
    }


def detect_telemetry_anomalies(telemetry: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for machine_code, group in telemetry.groupby("machine_code"):
        current = group.copy()
        anomaly = pd.Series(False, index=current.index)
        reasons = pd.Series("", index=current.index, dtype="string")
        for column, label in [
            ("temperature_c", "temperatura fora do padrão"),
            ("vibration_mm_s", "vibração fora do padrão"),
            ("energy_kw", "energia fora do padrão"),
        ]:
            q1, q3 = current[column].quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            metric_anomaly = ~current[column].between(lower, upper)
            anomaly |= metric_anomaly
            reasons = reasons.mask(
                metric_anomaly,
                reasons.where(reasons.eq(""), reasons + "; ") + label,
            )
        status_anomaly = current["machine_status"].astype(str).str.upper().ne("OPERANDO")
        anomaly |= status_anomaly
        reasons = reasons.mask(
            status_anomaly,
            reasons.where(reasons.eq(""), reasons + "; ") + "status operacional em alerta",
        )
        current["anomaly_reason"] = reasons
        frames.append(current[anomaly])
    if not frames:
        return pd.DataFrame()
    columns = [
        "telemetry_id", "machine_code", "recorded_at", "temperature_c",
        "vibration_mm_s", "energy_kw", "pressure_bar", "rpm",
        "machine_status", "anomaly_reason",
    ]
    return pd.concat(frames, ignore_index=True)[columns].sort_values("recorded_at")


def calculate_wear_trends(wear: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (machine_code, component_code, component_name), group in wear.groupby(
        ["machine_code", "component_code", "component_name"]
    ):
        ordered = group.sort_values("measured_at")
        hours = (
            ordered["measured_at"] - ordered["measured_at"].iloc[0]
        ).dt.total_seconds() / 3600
        if len(ordered) < 2 or hours.iloc[-1] <= 0:
            slope = 0.0
        else:
            slope = float(np.polyfit(hours, ordered["wear_pct"], 1)[0])
        current_wear = float(ordered["wear_pct"].iloc[-1])
        hours_to_90 = (90 - current_wear) / slope if slope > 0 and current_wear < 90 else 0.0
        rows.append(
            {
                "machine_code": machine_code,
                "component_code": component_code,
                "component_name": component_name,
                "observations": len(ordered),
                "initial_wear_pct": ordered["wear_pct"].iloc[0],
                "current_wear_pct": current_wear,
                "wear_points_per_hour": slope,
                "estimated_hours_to_90": max(0.0, hours_to_90),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["estimated_hours_to_90", "current_wear_pct"], ascending=[True, False]
    )


def calculate_trends(
    production_daily: pd.DataFrame,
    sales_daily: pd.DataFrame,
    telemetry_daily: pd.DataFrame,
    wear_trend: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for name, frame, column, unit in [
        ("Produção diária", production_daily, "produced", "unidades/dia"),
        ("Taxa diária de rejeição", production_daily, "rejection_rate", "proporção/dia"),
        ("Faturamento diário", sales_daily, "revenue", "BRL/dia"),
    ]:
        slope, period_change = linear_trend(frame[column])
        rows.append(
            {
                "trend": name,
                "slope_per_day": slope,
                "estimated_period_change": period_change,
                "unit": unit,
                "direction": "crescimento" if slope > 0 else "queda" if slope < 0 else "estável",
            }
        )
    temp_daily = telemetry_daily.groupby("date", as_index=False)["average_temperature"].mean()
    slope, period_change = linear_trend(temp_daily["average_temperature"])
    rows.append(
        {
            "trend": "Temperatura média diária",
            "slope_per_day": slope,
            "estimated_period_change": period_change,
            "unit": "°C/dia",
            "direction": "crescimento" if slope > 0 else "queda" if slope < 0 else "estável",
        }
    )
    if not wear_trend.empty:
        rows.append(
            {
                "trend": "Maior velocidade de desgaste",
                "slope_per_day": wear_trend["wear_points_per_hour"].max() * 24,
                "estimated_period_change": np.nan,
                "unit": "p.p./dia",
                "direction": "crescimento",
            }
        )
    return pd.DataFrame(rows)


def identify_opportunities(
    production_machine: pd.DataFrame,
    production_shift: pd.DataFrame,
    production_sales: pd.DataFrame,
    sales_channel: pd.DataFrame,
    sales_region: pd.DataFrame,
    telemetry_machine: pd.DataFrame,
    maintenance_priority: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    best_machine = production_machine.sort_values("approved_per_hour", ascending=False).iloc[0]
    worst_machine = production_machine.sort_values("rejection_rate", ascending=False).iloc[0]
    best_shift = production_shift.sort_values("approved_per_hour", ascending=False).iloc[0]
    low_turnover = production_sales.sort_values("sales_to_approved_ratio").iloc[0]
    best_channel = sales_channel.sort_values("revenue", ascending=False).iloc[0]
    best_region = sales_region.sort_values("revenue", ascending=False).iloc[0]
    risky_telemetry = telemetry_machine.sort_values("alert_rate", ascending=False).iloc[0]
    risky_part = maintenance_priority.iloc[0]
    rows.extend(
        [
            {
                "type": "oportunidade",
                "subject": "Produtividade",
                "finding": f"{best_machine.machine_code} possui a maior produtividade: {best_machine.approved_per_hour:.1f} aprovadas/h.",
                "recommended_action": "Investigar setup, operação e práticas que possam ser replicadas nas outras máquinas.",
            },
            {
                "type": "anomalia operacional",
                "subject": "Qualidade",
                "finding": f"{worst_machine.machine_code} possui a maior rejeição: {worst_machine.rejection_rate:.2%}.",
                "recommended_action": "Revisar calibração, matéria-prima e parâmetros dos lotes dessa máquina.",
            },
            {
                "type": "oportunidade",
                "subject": "Turnos",
                "finding": f"O turno {best_shift.shift_name} alcançou {best_shift.approved_per_hour:.1f} aprovadas/h.",
                "recommended_action": "Comparar equipe, abastecimento e setup com os demais turnos.",
            },
            {
                "type": "oportunidade",
                "subject": "Oferta e demanda",
                "finding": f"{low_turnover.product_name} tem o menor giro produção-vendas: {low_turnover.sales_to_approved_ratio:.1%}.",
                "recommended_action": "Reavaliar lotes e priorizar produtos com demanda proporcionalmente maior.",
            },
            {
                "type": "oportunidade",
                "subject": "Canal comercial",
                "finding": f"{best_channel.sales_channel} lidera o faturamento com R$ {best_channel.revenue:,.2f}.",
                "recommended_action": "Preservar o canal líder e testar suas práticas nos demais canais.",
            },
            {
                "type": "oportunidade",
                "subject": "Região",
                "finding": f"{best_region.customer_region} é a região de maior receita: R$ {best_region.revenue:,.2f}.",
                "recommended_action": "Priorizar cobertura comercial e disponibilidade dos produtos mais vendidos na região.",
            },
            {
                "type": "anomalia operacional",
                "subject": "Telemetria",
                "finding": f"{risky_telemetry.machine_code} tem a maior proporção de leituras em alerta: {risky_telemetry.alert_rate:.2%}.",
                "recommended_action": "Inspecionar vibração e temperatura antes de ampliar a carga do equipamento.",
            },
            {
                "type": "risco",
                "subject": "Manutenção",
                "finding": f"{risky_part.machine_code}/{risky_part.component_name} possui {risky_part.wear_pct:.1f}% de desgaste.",
                "recommended_action": "Planejar inspeção e verificar disponibilidade da peça de reposição.",
            },
        ]
    )
    return pd.DataFrame(rows)


def chart_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        template="plotly_white",
        font=dict(family="Arial", color="#243248"),
        title_font=dict(size=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=30, t=85, b=55),
        hoverlabel=dict(bgcolor="#15243A", font_color="white"),
    )
    return fig


def create_charts(
    summaries: dict[str, pd.DataFrame],
    charts_directory: Path,
) -> list[Path]:
    charts_directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    daily = summaries["production_daily"]
    daily = daily[daily["complete_day"]]
    fig = px.line(
        daily, x="date", y=["produced", "approved", "rejected"],
        color_discrete_sequence=COLORS, labels={"value": "Unidades", "date": "Data", "variable": "Indicador"},
    )
    chart_layout(fig, "Produção diária e qualidade")
    outputs.append(write_chart(fig, charts_directory / "01_producao_diaria.html"))

    machine = summaries["production_by_machine"].sort_values("rejection_rate")
    fig = px.bar(
        machine, x="rejection_rate", y="machine_code", orientation="h",
        color="rejection_rate", color_continuous_scale=["#19C6A3", "#FFB84D", "#FF6078"],
        labels={"rejection_rate": "Taxa de rejeição", "machine_code": "Máquina"},
    )
    fig.update_xaxes(tickformat=".1%")
    chart_layout(fig, "Taxa de rejeição por máquina")
    outputs.append(write_chart(fig, charts_directory / "02_rejeicao_por_maquina.html"))

    sales = summaries["sales_by_product"].sort_values("revenue")
    fig = px.bar(
        sales, x="revenue", y="product_name", orientation="h",
        color="revenue", color_continuous_scale=["#203A62", "#19C6A3"],
        labels={"revenue": "Faturamento (R$)", "product_name": "Produto"},
    )
    chart_layout(fig, "Faturamento por produto")
    outputs.append(write_chart(fig, charts_directory / "03_faturamento_por_produto.html"))

    comparison = summaries["production_vs_sales"]
    long_comparison = comparison.melt(
        id_vars="product_name",
        value_vars=["approved", "quantity_sold"],
        var_name="indicator",
        value_name="quantity",
    )
    fig = px.bar(
        long_comparison, x="product_name", y="quantity", color="indicator", barmode="group",
        color_discrete_sequence=[COLORS[0], COLORS[1]],
        labels={"product_name": "Produto", "quantity": "Quantidade", "indicator": "Indicador"},
    )
    chart_layout(fig, "Produção aprovada e quantidade vendida")
    outputs.append(write_chart(fig, charts_directory / "04_producao_vs_vendas.html"))

    telemetry = summaries["telemetry_daily"]
    fig = px.line(
        telemetry, x="date", y="average_vibration", color="machine_code",
        color_discrete_sequence=COLORS,
        labels={"date": "Data", "average_vibration": "Vibração média (mm/s)", "machine_code": "Máquina"},
    )
    chart_layout(fig, "Evolução da vibração por máquina")
    outputs.append(write_chart(fig, charts_directory / "05_vibracao_por_maquina.html"))

    maintenance = summaries["maintenance_priority"].sort_values("wear_pct").copy()
    maintenance["machine_component"] = (
        maintenance["machine_code"] + " — " + maintenance["component_name"]
    )
    fig = px.bar(
        maintenance, x="wear_pct", y="machine_component", orientation="h",
        color="risk_level",
        color_discrete_map={"NORMAL": COLORS[0], "ATENCAO": COLORS[2], "CRITICO": COLORS[3]},
        hover_data=["machine_code", "estimated_remaining_hours"],
        labels={"wear_pct": "Desgaste (%)", "machine_component": "Máquina e componente", "risk_level": "Situação"},
    )
    fig.add_vline(x=75, line_dash="dash", line_color=COLORS[2])
    fig.add_vline(x=90, line_dash="dash", line_color=COLORS[3])
    chart_layout(fig, "Desgaste atual dos componentes")
    outputs.append(write_chart(fig, charts_directory / "06_desgaste_componentes.html"))
    return outputs


def write_chart(fig: go.Figure, path: Path) -> Path:
    fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    fig.write_image(path.with_suffix(".png"), width=1400, height=800, scale=1.5)
    return path


def build_report(
    summaries: dict[str, pd.DataFrame],
    data_directory: Path,
    chart_paths: list[Path],
) -> str:
    executive = summaries["executive_summary"].set_index("indicator")["value"]
    trends = summaries["trends"]
    opportunities = summaries["opportunities"]
    anomalies = summaries["telemetry_anomalies"]
    production_machine = summaries["production_by_machine"]
    sales_product = summaries["sales_by_product"]
    maintenance = summaries["maintenance_priority"]

    best_machine = production_machine.sort_values("approved_per_hour", ascending=False).iloc[0]
    worst_machine = production_machine.sort_values("rejection_rate", ascending=False).iloc[0]
    best_product = sales_product.sort_values("revenue", ascending=False).iloc[0]
    risky_part = maintenance.iloc[0]
    lines = [
        "# Relatório de análise exploratória",
        "",
        f"- Data da execução (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Fonte: `{data_directory.resolve()}`",
        f"- Período: {summaries['production_daily']['date'].min().date()} a {summaries['production_daily']['date'].max().date()}",
        "",
        "## Resumo executivo",
        "",
        f"- Produção total: **{executive['Produção total']:,.0f} unidades**.",
        f"- Produção aprovada: **{executive['Produção aprovada']:,.0f} unidades**.",
        f"- Taxa de rejeição: **{executive['Taxa de rejeição']:.2%}**.",
        f"- Custo estimado do refugo: **R$ {executive['Custo estimado do refugo']:,.2f}**.",
        f"- Faturamento: **R$ {executive['Faturamento']:,.2f}**.",
        f"- Leituras de telemetria analisadas: **{executive['Leituras de telemetria']:,.0f}**.",
        "",
        "## Principais resultados",
        "",
        f"- Maior produtividade: **{best_machine.machine_code}**, com {best_machine.approved_per_hour:.1f} unidades aprovadas por hora operada.",
        f"- Maior rejeição: **{worst_machine.machine_code}**, com {worst_machine.rejection_rate:.2%}.",
        f"- Produto de maior faturamento: **{best_product.product_name}**, com R$ {best_product.revenue:,.2f}.",
        f"- Componente mais desgastado: **{risky_part.machine_code}/{risky_part.component_name}**, com {risky_part.wear_pct:.1f}%.",
        f"- Registros de telemetria sinalizados como anomalia ou alerta: **{len(anomalies):,}**.",
        "",
        "## Tendências",
        "",
        "| Indicador | Direção | Inclinação | Variação estimada no período |",
        "|---|---|---:|---:|",
    ]
    for _, row in trends.iterrows():
        change = "—" if pd.isna(row["estimated_period_change"]) else f"{row['estimated_period_change']:.2%}"
        lines.append(
            f"| {row['trend']} | {row['direction']} | {row['slope_per_day']:.4f} {row['unit']} | {change} |"
        )

    lines.extend(["", "## Anomalias e oportunidades", ""])
    for _, row in opportunities.iterrows():
        lines.extend(
            [
                f"### {row['subject']}",
                "",
                f"**Evidência:** {row['finding']}",
                "",
                f"**Ação sugerida:** {row['recommended_action']}",
                "",
            ]
        )

    lines.extend(["## Gráficos exploratórios", ""])
    for path in chart_paths:
        lines.append(f"- [{path.stem}](charts/{path.name})")

    lines.extend(
        [
            "",
            "## Método de detecção de anomalias",
            "",
            "As anomalias de telemetria combinam o intervalo interquartil de temperatura, vibração e energia por máquina com o status operacional informado. O método sinaliza observações fora do padrão estatístico ou em estado de atenção/crítico. Ele não determina a causa nem confirma uma falha física.",
            "",
            "## Limitações",
            "",
            "- Os dados são sintéticos e demonstram o método, não o desempenho de uma empresa real.",
            "- Produção aprovada menos vendas não representa estoque físico.",
            "- Custos e margens são estimados com os campos disponíveis.",
            "- Dias parciais nas extremidades entram nos totais, mas são excluídos do gráfico e da tendência diária de produção.",
            "- A tendência linear resume o período e não constitui previsão futura.",
            "- Anomalia estatística não implica defeito; requer avaliação técnica.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    summaries: dict[str, pd.DataFrame],
    output_directory: Path,
    data_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    tables_directory = output_directory / "tables"
    charts_directory = output_directory / "charts"
    tables_directory.mkdir(parents=True, exist_ok=True)
    for name, frame in summaries.items():
        frame.to_csv(tables_directory / f"{name}.csv", index=False, encoding="utf-8")
    charts = create_charts(summaries, charts_directory)
    (output_directory / "relatorio_analise.md").write_text(
        build_report(summaries, data_directory, charts), encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa análise exploratória da base Industrial 4.0.")
    parser.add_argument("--dados", type=Path, default=Path("data/generated"), help="Diretório dos seis CSVs.")
    parser.add_argument("--saida", type=Path, default=Path("reports/analysis"), help="Diretório dos resultados.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raw = load_data(args.dados)
    prepared = prepare_analysis(raw)
    summaries = build_summaries(prepared)
    write_outputs(summaries, args.saida, args.dados)
    print(f"Relatório: {(args.saida / 'relatorio_analise.md').resolve()}")
    print(f"Tabelas analíticas: {len(summaries)}")
    print(f"Gráficos interativos: {len(list((args.saida / 'charts').glob('*.html')))}")
    print(f"Anomalias/alertas de telemetria: {len(summaries['telemetry_anomalies']):,}")
    print(f"Oportunidades e riscos: {len(summaries['opportunities'])}")


if __name__ == "__main__":
    main()
