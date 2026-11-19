# 2. Perguntas gerenciais e KPIs

## 2.1 Perguntas gerenciais

1. Qual máquina possui maior produtividade por hora efetivamente operada?
2. Qual máquina e qual turno apresentam maior taxa de rejeição?
3. Qual horário combina maior produção e melhor qualidade?
4. Qual linha utiliza melhor sua capacidade nominal?
5. Quais produtos apresentam maior demanda e faturamento?
6. Qual região e canal comercial geram melhor resultado?
7. Existe desalinhamento relevante entre produção aprovada e vendas?
8. Qual produto possui maior custo estimado de fabricação?
9. Qual é o custo do refugo e onde ele se concentra?
10. Quais máquinas apresentam sinais combinados de possível problema?
11. Quais componentes estão acima dos limites de atenção e criticidade?
12. Quando os componentes prioritários poderão atingir 90% de desgaste?

## 2.2 Catálogo de KPIs

| KPI | Objetivo | Fórmula | Unidade | Interpretação |
|---|---|---|---|---|
| Produção total | Medir volume bruto | `SUM(qty_produced)` | unidades | Quanto foi produzido no período |
| Produção aprovada | Medir saída com qualidade | `SUM(qty_produced - qty_rejected)` | unidades | Volume potencialmente aproveitável |
| Quantidade rejeitada | Medir refugo | `SUM(qty_rejected)` | unidades | Perda de qualidade |
| Taxa de rejeição | Comparar qualidade | `rejeitados / produzidos` | % | Menor é melhor |
| Tempo de operação | Medir tempo útil | duração do lote - parada | minutos | Base da produtividade real |
| Produtividade operacional | Comparar máquinas | aprovadas / horas operadas | un./h | Maior é melhor, respeitando qualidade |
| Disponibilidade estimada | Medir perda por parada | tempo operando / duração | % | Parcela do tempo disponível em operação |
| Desempenho estimado | Comparar capacidade | produção / capacidade possível | % | Utilização da capacidade durante operação |
| Qualidade | Medir peças conformes | aprovadas / produzidas | % | Parcela sem rejeição |
| OEE estimado | Integrar eficiência | disponibilidade x desempenho x qualidade | % | Indicador estimado, não OEE auditado |
| Pedidos | Medir atividade comercial | `COUNT(order_id)` | pedidos | Inclui todos os status quando indicado |
| Quantidade vendida | Medir demanda atendida | soma vendida não cancelada | unidades | Volume comercial válido |
| Faturamento | Medir receita bruta | soma de `total_amount` não cancelado | R$ | Não é lucro |
| Ticket médio | Medir valor por pedido | faturamento / pedidos válidos | R$/pedido | Valor médio comercial |
| Giro produção-vendas | Comparar oferta e demanda | vendido / aprovado | % | Não equivale a giro de estoque contábil |
| Custo de produção | Estimar gasto industrial | produzido x custo unitário | R$ | Premissa baseada no campo disponível |
| Custo do refugo | Quantificar perda | rejeitado x custo unitário | R$ | Custo industrial estimado da rejeição |
| CPV estimado | Estimar custo vendido | vendido x custo do lote/produto | R$ | Usa lote; custo médio como fallback |
| Margem bruta estimada | Comparar resultado | faturamento - CPV estimado | R$ e % | Não representa lucro líquido |
| Componentes em atenção | Priorizar manutenção | desgaste >= 75% e < 90% | componentes | Requer avaliação planejada |
| Componentes críticos | Sinalizar risco | desgaste >= 90% | componentes | Intervenção prioritária |
| Índice de risco | Combinar sinais | 40% desgaste + 30% alertas + 15% vibração + 15% rejeição | 0-100 | Ranking gerencial, não probabilidade de falha |
| Vida restante prevista | Antecipar manutenção | projeção até 90% de desgaste | horas | Estimativa sujeita às limitações do modelo |

## 2.3 Regras de cálculo

- Pedidos cancelados não entram em faturamento, quantidade vendida, CPV e margem.
- Divisões por zero produzem valor ausente, nunca infinito.
- Horários são convertidos para o fuso de Brasília.
- Produção menos vendas não é estoque físico.
- Margem estimada não é lucro líquido.
- OEE é estimado porque a base não possui calendário completo de disponibilidade planejada.
- O índice de risco é uma regra da equipe e deve ser apresentado com seus pesos.

