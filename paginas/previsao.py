from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core import ui
from prever_desgaste import run


PROJECT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT / "data" / "generated"
OUTPUT_DIR = PROJECT / "reports" / "prediction"


@st.cache_data(show_spinner=False)
def prediction_results(data_signature: tuple):
    return run(DATA_DIR, OUTPUT_DIR, 0.8, export_charts=False)


def _signature() -> tuple:
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                 for p in [DATA_DIR / "machines.csv", DATA_DIR / "wear_events.csv"] if p.exists())


def render(ctx):
    ui.cabecalho("Previsão de desgaste", "Regressão linear por componente com validação temporal 80% treino e 20% teste")
    metrics, tests = prediction_results(_signature())
    metrics = metrics.copy()
    if ctx.maquinas:
        metrics = metrics[metrics["machine_code"].isin(ctx.maquinas)]
        tests = tests[tests["machine_code"].isin(ctx.maquinas)]
    if metrics.empty:
        ui.sem_dados("Nenhuma previsão disponível para os filtros selecionados.")
        return

    valid_r2 = metrics["r2"].dropna()
    priority = metrics.sort_values(["hours_to_90_pct", "current_wear_pct"], ascending=[True, False]).iloc[0]
    c = st.columns(4)
    c[0].metric("Componentes modelados", ui.fint(len(metrics)))
    c[1].metric("MAE médio", f"{metrics['mae'].mean():.3f} p.p.")
    c[2].metric("RMSE médio", f"{metrics['rmse'].mean():.3f} p.p.")
    c[3].metric("R² médio", f"{valid_r2.mean():.4f}" if not valid_r2.empty else "—")

    if priority["status"] == "LIMITE_ATINGIDO":
        st.error(f"{priority['machine_code']} · {priority['component_name']} já atingiu {priority['current_wear_pct']:.1f}% de desgaste.",
                 icon=":material/emergency_home:")

    chart = metrics.copy()
    chart["componente"] = chart["machine_code"] + " · " + chart["component_name"]
    chart["dias_ate_90"] = chart["hours_to_90_pct"] / 24
    fig = px.bar(chart.sort_values("dias_ate_90", ascending=False), x="dias_ate_90", y="componente", orientation="h",
                 color="confidence", title="Dias previstos até 90% de desgaste",
                 color_discrete_map={"ALTA": "#19C6A3", "MEDIA": "#4D8DFF", "BAIXA": "#FFB84D", "INSUFICIENTE": "#FF6078"},
                 labels={"dias_ate_90": "Dias até 90%", "componente": "Componente", "confidence": "Confiança"})
    fig.update_layout(yaxis_title=None, legend_title=None)
    ui.grafico(fig, 480)

    fig = px.scatter(tests, x="wear_pct", y="predicted_wear_pct", color="machine_code",
                     title="Desgaste observado versus previsto no teste",
                     labels={"wear_pct": "Observado (%)", "predicted_wear_pct": "Previsto (%)", "machine_code": "Máquina"})
    ui.grafico(fig, 420)

    display = metrics[["machine_code", "component_name", "current_wear_pct", "wear_rate_pct_per_hour",
                       "hours_to_90_pct", "predicted_90_at", "mae", "rmse", "r2", "confidence", "status"]].copy()
    display["predicted_90_at"] = pd.to_datetime(display["predicted_90_at"], utc=True, errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    ui.tabela(display.rename(columns={"machine_code": "Máquina", "component_name": "Componente",
                                      "current_wear_pct": "Desgaste atual (%)", "wear_rate_pct_per_hour": "Taxa (p.p./h)",
                                      "hours_to_90_pct": "Horas até 90%", "predicted_90_at": "Data prevista (UTC)",
                                      "mae": "MAE", "rmse": "RMSE", "r2": "R²", "confidence": "Confiança", "status": "Status"}))
    ui.nota("A previsão é calculada sobre wear_events.csv. R² negativo ou ausente e mudanças bruscas de desgaste reduzem a confiança. O resultado apoia a manutenção, mas não substitui inspeção.")
