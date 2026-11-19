# Relatório da técnica analítica

- Execução (UTC): 2026-11-17T14:03:03.656812+00:00
- Fonte: `C:\Users\Xand\Documents\Codex\2026-11-12\preciso-da-sua-ajuda-para-fazer\outputs\painel_industria40_parte2\data\generated`
- Componentes modelados: **12**
- Divisão temporal: **80% treino / 20% teste**
- Limite previsto: **90% de desgaste**

## Resultado geral

- MAE médio: **1.112 ponto percentual**.
- RMSE médio: **1.160 ponto percentual**.
- R² médio: **0.9820**.
- Prioridade: **PRE-01/Rolamento principal**, desgaste atual de 99.5% e status `LIMITE_ATINGIDO`.

## Previsão por componente

| Máquina | Componente | Atual | Taxa por hora | Horas até 90% | Data prevista | MAE | RMSE | R² | Confiança |
|---|---|---:|---:|---:|---|---:|---:|---:|---|
| PRE-01 | Rolamento principal | 99.5% | 0.05384 | 0.0 | 12/11/2026 18:00 UTC | 11.166 | 11.537 | — | INSUFICIENTE |
| CNC-01 | Correia de transmissão | 73.8% | 0.04719 | 333.3 | 26/11/2026 15:20 UTC | 0.558 | 0.571 | 0.9096 | ALTA |
| PRE-01 | Correia de transmissão | 72.7% | 0.04969 | 340.3 | 26/11/2026 22:16 UTC | 0.351 | 0.366 | 0.9678 | ALTA |
| MON-01 | Rolamento principal | 72.0% | 0.04802 | 372.5 | 28/11/2026 06:30 UTC | 0.115 | 0.139 | 0.9953 | ALTA |
| PIN-01 | Rolamento principal | 70.1% | 0.04934 | 407.7 | 29/11/2026 17:39 UTC | 0.087 | 0.104 | 0.9976 | ALTA |
| PIN-01 | Correia de transmissão | 66.4% | 0.04950 | 477.9 | 02/12/2026 15:55 UTC | 0.054 | 0.066 | 0.9990 | ALTA |
| MON-01 | Motor elétrico | 65.2% | 0.04730 | 522.6 | 04/12/2026 12:37 UTC | 0.045 | 0.053 | 0.9993 | ALTA |
| CNC-01 | Rolamento principal | 62.4% | 0.04599 | 599.3 | 07/12/2026 17:16 UTC | 0.245 | 0.267 | 0.9824 | ALTA |
| PIN-01 | Motor elétrico | 59.5% | 0.04953 | 606.5 | 08/12/2026 00:32 UTC | 0.141 | 0.171 | 0.9921 | ALTA |
| MON-01 | Correia de transmissão | 55.1% | 0.04843 | 716.6 | 12/12/2026 14:38 UTC | 0.304 | 0.315 | 0.9745 | ALTA |
| CNC-01 | Motor elétrico | 53.2% | 0.04835 | 761.4 | 14/12/2026 11:23 UTC | 0.069 | 0.094 | 0.9979 | ALTA |
| PRE-01 | Motor elétrico | 48.3% | 0.04788 | 872.8 | 19/12/2026 02:46 UTC | 0.213 | 0.238 | 0.9866 | ALTA |

## Método

Cada série foi ordenada no tempo. O início foi usado para treino e o trecho final para teste, evitando usar o futuro para explicar o passado. MAE e RMSE medem o erro em pontos percentuais. R² mede quanto da variação do teste é explicada pelo modelo. Depois da avaliação, a reta foi reajustada com todo o histórico para estimar quando alcançará 90%.

## Gráficos

- [Tempo previsto até 90%](charts/01_tempo_ate_90.html)
- [Observado versus previsto](charts/02_observado_vs_previsto.html)

## Limitações

- A regressão pressupõe crescimento aproximadamente linear do desgaste.
- Troca de peça, manutenção ou mudança de carga invalida a extrapolação anterior.
- R² negativo indica que, no teste, a reta foi pior que usar a média observada.
- A previsão apoia o planejamento, mas não substitui inspeção técnica.
