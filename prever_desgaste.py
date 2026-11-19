"""Previsão temporal do desgaste de componentes até o limite de 90%.

Usa regressão linear por máquina e componente, com divisão cronológica entre
treino e teste. Produz métricas, previsões, gráficos e relatório reproduzível.

Exemplo:
    python prever_desgaste.py --dados data/generated --saida reports/prediction
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px


TARGET_WEAR = 90.0
COLORS = ["#19C6A3", "#4D8DFF", "#FFB84D", "#FF6078"]


def load_wear_data(data_directory: Path) -> pd.DataFrame:
    wear_path = data_directory / "wear_events.csv"
    machines_path = data_directory / "machines.csv"
    if not wear_path.exists() or not machines_path.exists():
        raise FileNotFoundError("São necessários wear_events.csv e machines.csv.")

    wear = pd.read_csv(wear_path)
    machines = pd.read_csv(machines_path)
    wear["measured_at"] = pd.to_datetime(wear["measured_at"], errors="coerce", utc=True)
    wear["wear_pct"] = pd.to_numeric(wear["wear_pct"], errors="coerce")
    wear = wear.dropna(subset=["machine_id", "component_code", "measured_at", "wear_pct"])
    wear = wear.merge(
        machines[["machine_id", "machine_code", "machine_name"]],
        on="machine_id",
        how="left",
        validate="many_to_one",
    )
    return wear.sort_values(["machine_id", "component_code", "measured_at"])


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float, float]:
    residuals = actual - predicted
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    denominator = float(np.sum((actual - actual.mean()) ** 2))
    r2 = float(1 - np.sum(residuals**2) / denominator) if denominator > 0 else np.nan
    return mae, rmse, r2


def confidence_label(observations: int, mae: float, r2: float, slope: float) -> str:
    if slope <= 0 or np.isnan(r2):
        return "INSUFICIENTE"
    if observations >= 100 and r2 >= 0.90 and mae <= 2.0:
        return "ALTA"
    if observations >= 30 and r2 >= 0.70 and mae <= 4.0:
        return "MEDIA"
    return "BAIXA"


def fit_component(group: pd.DataFrame, train_fraction: float) -> tuple[dict, pd.DataFrame]:
    group = group.sort_values("measured_at").drop_duplicates("measured_at", keep="last").copy()
    first_time = group["measured_at"].iloc[0]
    group["elapsed_hours"] = (group["measured_at"] - first_time).dt.total_seconds() / 3600
    n = len(group)
    train_size = min(max(int(np.floor(n * train_fraction)), 2), n - 2)
    train = group.iloc[:train_size]
    test = group.iloc[train_size:].copy()

    train_slope, train_intercept = np.polyfit(
        train["elapsed_hours"].to_numpy(float), train["wear_pct"].to_numpy(float), 1
    )
    test["predicted_wear_pct"] = train_intercept + train_slope * test["elapsed_hours"]
    mae, rmse, r2 = regression_metrics(
        test["wear_pct"].to_numpy(float), test["predicted_wear_pct"].to_numpy(float)
    )

    full_slope, full_intercept = np.polyfit(
        group["elapsed_hours"].to_numpy(float), group["wear_pct"].to_numpy(float), 1
    )
    last = group.iloc[-1]
    if last["wear_pct"] >= TARGET_WEAR:
        status = "LIMITE_ATINGIDO"
        hours_to_target = 0.0
        predicted_date = last["measured_at"]
    elif full_slope <= 0:
        status = "SEM_TENDENCIA_POSITIVA"
        hours_to_target = np.nan
        predicted_date = pd.NaT
    else:
        target_elapsed = (TARGET_WEAR - full_intercept) / full_slope
        hours_to_target = max(float(target_elapsed - last["elapsed_hours"]), 0.0)
        predicted_date = last["measured_at"] + pd.to_timedelta(hours_to_target, unit="h")
        status = "PREVISTO"

    result = {
        "machine_id": last["machine_id"],
        "machine_code": last["machine_code"],
        "machine_name": last["machine_name"],
        "component_code": last["component_code"],
        "component_name": last["component_name"],
        "observations": n,
        "train_observations": len(train),
        "test_observations": len(test),
        "history_hours": float(group["elapsed_hours"].iloc[-1]),
        "current_wear_pct": float(last["wear_pct"]),
        "target_wear_pct": TARGET_WEAR,
        "wear_rate_pct_per_hour": float(full_slope),
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "hours_to_90_pct": hours_to_target,
        "predicted_90_at": predicted_date,
        "status": status,
        "confidence": confidence_label(n, mae, r2, full_slope),
        "last_measurement_at": last["measured_at"],
    }
    test.insert(0, "dataset", "TESTE")
    test["residual"] = test["wear_pct"] - test["predicted_wear_pct"]
    return result, test


def train_models(
    wear: pd.DataFrame, train_fraction: float = 0.8, minimum_observations: int = 10
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0.5 <= train_fraction <= 0.9:
        raise ValueError("A proporção de treino deve estar entre 0,5 e 0,9.")
    results: list[dict] = []
    predictions: list[pd.DataFrame] = []
    for _, group in wear.groupby(["machine_id", "component_code"], sort=True):
        if len(group) < minimum_observations:
            continue
        result, test = fit_component(group, train_fraction)
        results.append(result)
        predictions.append(test)
    if not results:
        raise ValueError("Nenhum componente possui observações suficientes para modelagem.")
    metrics = pd.DataFrame(results).sort_values(
        ["hours_to_90_pct", "current_wear_pct"], ascending=[True, False], na_position="last"
    )
    tests = pd.concat(predictions, ignore_index=True)
    return metrics, tests


def create_charts(metrics: pd.DataFrame, tests: pd.DataFrame, charts_dir: Path) -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)
    forecast = metrics.copy()
    forecast["machine_component"] = forecast["machine_code"] + " — " + forecast["component_name"]
    forecast["days_to_90_pct"] = forecast["hours_to_90_pct"] / 24
    fig = px.bar(
        forecast.sort_values("days_to_90_pct", ascending=False),
        x="days_to_90_pct", y="machine_component", orientation="h", color="confidence",
        color_discrete_map={"ALTA": COLORS[0], "MEDIA": COLORS[1], "BAIXA": COLORS[2], "INSUFICIENTE": COLORS[3]},
        labels={"days_to_90_pct": "Dias previstos até 90%", "machine_component": "Máquina e componente", "confidence": "Confiança"},
        title="Previsão do tempo até 90% de desgaste",
    )
    fig.update_layout(template="plotly_white", height=700, margin=dict(l=80, r=30, t=80, b=55))
    fig.write_html(charts_dir / "01_tempo_ate_90.html", include_plotlyjs="cdn")
    fig.write_image(charts_dir / "01_tempo_ate_90.png", width=1400, height=800, scale=1.5)

    fig = px.scatter(
        tests, x="wear_pct", y="predicted_wear_pct", color="machine_code",
        labels={"wear_pct": "Desgaste observado (%)", "predicted_wear_pct": "Desgaste previsto (%)", "machine_code": "Máquina"},
        title="Valores observados e previstos no conjunto de teste",
    )
    limits = [float(min(tests["wear_pct"].min(), tests["predicted_wear_pct"].min())),
              float(max(tests["wear_pct"].max(), tests["predicted_wear_pct"].max()))]
    fig.add_shape(type="line", x0=limits[0], y0=limits[0], x1=limits[1], y1=limits[1], line=dict(dash="dash", color="#64748B"))
    fig.update_layout(template="plotly_white", height=700, margin=dict(l=70, r=30, t=80, b=55))
    fig.write_html(charts_dir / "02_observado_vs_previsto.html", include_plotlyjs="cdn")
    fig.write_image(charts_dir / "02_observado_vs_previsto.png", width=1400, height=800, scale=1.5)


def build_report(metrics: pd.DataFrame, data_directory: Path, train_fraction: float) -> str:
    valid_r2 = metrics["r2"].dropna()
    priority = metrics.iloc[0]
    lines = [
        "# Relatório da técnica analítica",
        "",
        f"- Execução (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Fonte: `{data_directory.resolve()}`",
        f"- Componentes modelados: **{len(metrics)}**",
        f"- Divisão temporal: **{train_fraction:.0%} treino / {1-train_fraction:.0%} teste**",
        f"- Limite previsto: **{TARGET_WEAR:.0f}% de desgaste**",
        "",
        "## Resultado geral",
        "",
        f"- MAE médio: **{metrics['mae'].mean():.3f} ponto percentual**.",
        f"- RMSE médio: **{metrics['rmse'].mean():.3f} ponto percentual**.",
        f"- R² médio: **{valid_r2.mean():.4f}**.",
        f"- Prioridade: **{priority.machine_code}/{priority.component_name}**, desgaste atual de {priority.current_wear_pct:.1f}% e status `{priority.status}`.",
        "",
        "## Previsão por componente",
        "",
        "| Máquina | Componente | Atual | Taxa por hora | Horas até 90% | Data prevista | MAE | RMSE | R² | Confiança |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in metrics.itertuples():
        hours = "—" if pd.isna(row.hours_to_90_pct) else f"{row.hours_to_90_pct:.1f}"
        date = "—" if pd.isna(row.predicted_90_at) else pd.Timestamp(row.predicted_90_at).strftime("%d/%m/%Y %H:%M UTC")
        r2 = "—" if pd.isna(row.r2) else f"{row.r2:.4f}"
        lines.append(
            f"| {row.machine_code} | {row.component_name} | {row.current_wear_pct:.1f}% | "
            f"{row.wear_rate_pct_per_hour:.5f} | {hours} | {date} | {row.mae:.3f} | {row.rmse:.3f} | {r2} | {row.confidence} |"
        )
    lines.extend([
        "",
        "## Método",
        "",
        "Cada série foi ordenada no tempo. O início foi usado para treino e o trecho final para teste, evitando usar o futuro para explicar o passado. MAE e RMSE medem o erro em pontos percentuais. R² mede quanto da variação do teste é explicada pelo modelo. Depois da avaliação, a reta foi reajustada com todo o histórico para estimar quando alcançará 90%.",
        "",
        "## Gráficos",
        "",
        "- [Tempo previsto até 90%](charts/01_tempo_ate_90.html)",
        "- [Observado versus previsto](charts/02_observado_vs_previsto.html)",
        "",
        "## Limitações",
        "",
        "- A regressão pressupõe crescimento aproximadamente linear do desgaste.",
        "- Troca de peça, manutenção ou mudança de carga invalida a extrapolação anterior.",
        "- R² negativo indica que, no teste, a reta foi pior que usar a média observada.",
        "- A previsão apoia o planejamento, mas não substitui inspeção técnica.",
    ])
    return "\n".join(lines) + "\n"


def run(
    data_directory: Path,
    output_directory: Path,
    train_fraction: float,
    export_charts: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    wear = load_wear_data(data_directory)
    metrics, tests = train_models(wear, train_fraction=train_fraction)
    output_directory.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_directory / "previsoes_componentes.csv", index=False, encoding="utf-8")
    tests.to_csv(output_directory / "previsoes_teste.csv", index=False, encoding="utf-8")
    if export_charts:
        create_charts(metrics, tests, output_directory / "charts")
    (output_directory / "relatorio_previsao.md").write_text(
        build_report(metrics, data_directory, train_fraction), encoding="utf-8"
    )
    return metrics, tests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prevê quando componentes alcançarão 90% de desgaste.")
    parser.add_argument("--dados", type=Path, default=Path("data/generated"))
    parser.add_argument("--saida", type=Path, default=Path("reports/prediction"))
    parser.add_argument("--proporcao-treino", type=float, default=0.8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics, tests = run(args.dados, args.saida, args.proporcao_treino)
    print(f"Componentes modelados: {len(metrics)}")
    print(f"Observações de teste: {len(tests)}")
    print(f"MAE médio: {metrics['mae'].mean():.3f}")
    print(f"RMSE médio: {metrics['rmse'].mean():.3f}")
    print(f"R² médio: {metrics['r2'].mean():.4f}")
    print(f"Relatório: {(args.saida / 'relatorio_previsao.md').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
