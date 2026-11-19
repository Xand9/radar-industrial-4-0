# 6. Análise exploratória e técnica analítica

## 6.1 Análise exploratória implementada

A execução reproduzível é feita por `analisar_dados.py`. O programa lê os seis CSVs validados e grava 17 tabelas analíticas, seis gráficos em HTML/PNG e o relatório `reports/analysis/relatorio_analise.md`. Dias incompletos nas extremidades do período permanecem nas estatísticas totais, mas são retirados da tendência diária para não distorcer a interpretação.

### Produção

- distribuição de volume, ciclo, parada e energia;
- produção e rejeição por máquina, linha, produto, turno e hora;
- produtividade e OEE estimado;
- identificação de horários e máquinas fora do padrão.

### Vendas

- faturamento, quantidade e ticket;
- distribuição por produto, canal e região;
- tendência temporal e sazonalidade;
- comparação entre produção aprovada e demanda.

### Telemetria e desgaste

- estatísticas de temperatura, vibração, energia, pressão e RPM;
- correlação entre telemetria, rejeição e desgaste;
- evolução do desgaste por componente;
- identificação de máquinas e componentes prioritários.

## 6.2 Técnica analítica escolhida

**Previsão do tempo até o componente atingir 90% de desgaste.**

Justificativa: o problema é diretamente relacionado à manutenção preditiva e possui variável temporal contínua. A previsão transforma o histórico de desgaste em uma estimativa acionável para planejamento de paradas e peças.

## 6.3 Metodologia implementada

1. Ordenar as medições por máquina e componente.
2. Criar variável de tempo em horas desde a primeira medição.
3. Separar observações de treino e teste respeitando a ordem temporal.
4. Ajustar regressão linear por componente quando houver ao menos 10 observações.
5. Prever o instante em que a curva alcançará 90%.
6. Comparar a previsão com o campo de horas restantes do simulador.
7. Classificar resultados inválidos quando a tendência for nula, negativa ou instável.

## 6.4 Métricas

- MAE: erro absoluto médio do desgaste previsto.
- RMSE: penaliza erros maiores.
- R²: capacidade explicativa da tendência linear.
- Número de observações por componente.
- Largura do histórico analisado.

Uma previsão não será apresentada como confiável somente por possuir R² elevado. Também serão avaliados volume de dados, estabilidade da taxa e plausibilidade operacional.

## 6.5 Saídas produzidas

| Máquina | Componente | Desgaste atual | Taxa estimada | Horas até 90% | MAE | R² | Confiança |
|---|---|---:|---:|---:|---:|---:|---|

O script `prever_desgaste.py` produz `previsoes_componentes.csv`, previsões do conjunto de teste, dois gráficos e `relatorio_previsao.md`. A execução atual modelou 12 componentes. O resultado médio foi MAE de 1,112 ponto percentual, RMSE de 1,160 ponto percentual e R² de 0,9820.

## 6.6 Limitações da técnica

- desgaste real pode não ser linear;
- manutenção e substituição alteram a série;
- mudanças de carga e ambiente podem modificar a taxa;
- dados sintéticos não comprovam desempenho em uma fábrica real;
- correlação entre sensores e desgaste não implica causalidade;
- a previsão apoia decisão, mas não substitui inspeção técnica.

## 6.7 Situação

A análise exploratória e a técnica analítica estão concluídas e testadas. A previsão respeita a ordem temporal, calcula MAE, RMSE e R², estima a data de 90% e classifica a confiança. O componente PRE-01/Rolamento principal já atingiu o limite e apresentou comportamento não linear no teste, por isso foi classificado com confiança insuficiente em vez de ocultar a limitação do modelo.

