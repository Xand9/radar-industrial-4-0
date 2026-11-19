# Relatório final - Radar Industrial 4.0

## Identificação

- Disciplina: Desenvolvimento de Business Intelligence
- Projeto: Desafio Industrial 4.0
- Integrantes: Beatriz Andrade Barbosa de Sousa; Pedro Henrique de Souza Pereira; **Alexandre de Marcus Paiva Barcelos**

## Resumo

O projeto implementa um fluxo de Business Intelligence para uma indústria simulada. A solução gera seis tabelas relacionadas, valida a qualidade, calcula indicadores, identifica tendências e anomalias, prevê quando componentes atingirão 90% de desgaste e apresenta os resultados em um dashboard Streamlit. O painel funciona com os CSVs locais ou com o PostgreSQL do Supabase.

## Problema e objetivo

Produção, vendas, telemetria e manutenção precisam ser analisadas em conjunto. O objetivo é permitir que gestores acompanhem produtividade, qualidade, receita, risco operacional e necessidade de manutenção com evidências reproduzíveis.

## Arquitetura

```text
Gerador -> CSVs -> Validação -> ETL/Pandas -> Análise -> Previsão -> Dashboard
                                                            |-> CSV local
                                                            |-> Supabase
```

As seis tabelas são `machines`, `production_events`, `sales_orders`, `machine_telemetry`, `parts_wear` e `wear_events`. A modelagem utiliza `machine_id` para relacionar máquinas aos eventos e `batch_id` para relacionar pedidos aos lotes de produção.

## Geração e qualidade

O gerador aceita período, quantidade de máquinas, intervalos e semente. A execução final produziu 48.515 registros. O validador verificou estrutura, duplicidades, ausências, chaves órfãs, domínios, valores negativos, coerência temporal e plausibilidade. A base foi aprovada com zero regras em erro e zero avisos.

## Análise exploratória

- Produção total: 315.374 unidades.
- Produção aprovada: 300.331 unidades.
- Taxa de rejeição: 4,77%.
- Faturamento: R$ 19.064.388,44.
- Custo estimado do refugo: R$ 1.115.783,11.
- Telemetria analisada: 34.564 leituras.
- Anomalias ou alertas de telemetria: 349 registros.

A PRE-01 apresentou a maior produtividade e também a maior taxa de rejeição, 5,53%. O Módulo Eletrônico D liderou o faturamento. O rolamento principal da PRE-01 atingiu 99,5% de desgaste.

## Técnica analítica

Foi ajustada uma regressão linear separada para cada máquina e componente. As observações foram ordenadas no tempo. Os primeiros 80% formaram o treino e os 20% finais formaram o teste. Após a avaliação, o modelo foi reajustado com todo o histórico para estimar a data em que o desgaste alcançará 90%.

Resultados médios dos 12 componentes:

- MAE: 1,112 ponto percentual;
- RMSE: 1,160 ponto percentual;
- R²: 0,9820.

O rolamento da PRE-01 já havia ultrapassado 90%. O modelo classificou esse caso com confiança insuficiente porque a série atingiu o limite de 99,5% e deixou de seguir a tendência linear observada no treino.

## Dashboard

O painel possui visão executiva, produção, vendas, produção versus vendas, máquinas, manutenção, financeiro, respostas gerenciais, dados, qualidade e previsão. A barra lateral permite alternar entre Base local (CSV) e Supabase. O modo local garante a demonstração mesmo sem internet ou banco disponível.

## Recomendações

1. Inspecionar imediatamente o rolamento principal da PRE-01 e confirmar a disponibilidade da peça.
2. Revisar calibração, matéria-prima e parâmetros dos lotes da PRE-01 devido à rejeição de 5,53%.
3. Comparar o setup da PRE-01 com as demais máquinas para separar as causas de produtividade das causas de refugo.
4. Ajustar o plano de produção dos produtos com menor giro entre volume aprovado e vendido.
5. Acompanhar o crescimento da temperatura média e os 349 alertas antes de ampliar a carga dos equipamentos.

## Limitações

- os dados são sintéticos;
- produção aprovada menos vendas não representa estoque físico;
- margem bruta estimada não representa lucro líquido;
- anomalia estatística não confirma defeito;
- desgaste real pode não ser linear;
- manutenção ou troca de peça exige novo treinamento;
- a previsão não substitui inspeção técnica.

## Reprodução

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python gerar_base.py --dias 30 --maquinas 4 --seed 42 --sobrescrever
python validar_qualidade.py
python analisar_dados.py
python prever_desgaste.py
python -m streamlit run app.py
```

## Conclusão

O projeto demonstra o fluxo completo de BI: geração reproduzível, modelagem, qualidade, análise, técnica preditiva, visualização e recomendação. A principal decisão operacional é priorizar a manutenção da PRE-01 sem perder de vista sua produtividade e sua taxa de rejeição.
