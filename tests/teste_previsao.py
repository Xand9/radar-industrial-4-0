"""Teste funcional da técnica analítica de previsão de desgaste."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from prever_desgaste import run


def main() -> None:
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "prediction"
        metrics, tests = run(PROJECT / "data" / "generated", output, 0.8)

        assert len(metrics) == 12, "Devem existir três componentes para cada uma das quatro máquinas."
        assert not tests.empty
        assert {"mae", "rmse", "r2", "predicted_90_at", "hours_to_90_pct"}.issubset(metrics.columns)
        assert metrics["mae"].ge(0).all()
        assert metrics["rmse"].ge(metrics["mae"]).all()
        assert metrics["train_observations"].gt(0).all()
        assert metrics["test_observations"].gt(0).all()
        assert (output / "previsoes_componentes.csv").exists()
        assert (output / "previsoes_teste.csv").exists()
        assert (output / "relatorio_previsao.md").exists()
        assert (output / "charts" / "01_tempo_ate_90.png").exists()
        assert (output / "charts" / "02_observado_vs_previsto.png").exists()

        saved = pd.read_csv(output / "previsoes_componentes.csv")
        assert len(saved) == len(metrics)

    print("OK: previsão temporal, MAE, RMSE e R² gerados corretamente.")


if __name__ == "__main__":
    main()
