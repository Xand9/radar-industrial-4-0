# Relatório de análise exploratória

- Data da execução (UTC): 2026-11-17T13:32:57.671552+00:00
- Fonte: `C:\Users\Xand\Documents\Codex\2026-11-12\preciso-da-sua-ajuda-para-fazer\outputs\painel_industria40_parte2\data\generated`
- Período: 2026-10-13 a 2026-11-12

## Resumo executivo

- Produção total: **315,374 unidades**.
- Produção aprovada: **300,331 unidades**.
- Taxa de rejeição: **4.77%**.
- Custo estimado do refugo: **R$ 1,115,783.11**.
- Faturamento: **R$ 19,064,388.44**.
- Leituras de telemetria analisadas: **34,564**.

## Principais resultados

- Maior produtividade: **PRE-01**, com 168.3 unidades aprovadas por hora operada.
- Maior rejeição: **PRE-01**, com 5.53%.
- Produto de maior faturamento: **Módulo Eletrônico D**, com R$ 7,573,844.77.
- Componente mais desgastado: **PRE-01/Rolamento principal**, com 99.5%.
- Registros de telemetria sinalizados como anomalia ou alerta: **349**.

## Tendências

| Indicador | Direção | Inclinação | Variação estimada no período |
|---|---|---:|---:|
| Produção diária | queda | -3.1754 unidades/dia | -0.85% |
| Taxa diária de rejeição | queda | -0.0001 proporção/dia | -3.13% |
| Faturamento diário | crescimento | 3668.6090 BRL/dia | 17.90% |
| Temperatura média diária | crescimento | 0.0266 °C/dia | 1.17% |
| Maior velocidade de desgaste | crescimento | 1.2921 p.p./dia | — |

## Anomalias e oportunidades

### Produtividade

**Evidência:** PRE-01 possui a maior produtividade: 168.3 aprovadas/h.

**Ação sugerida:** Investigar setup, operação e práticas que possam ser replicadas nas outras máquinas.

### Qualidade

**Evidência:** PRE-01 possui a maior rejeição: 5.53%.

**Ação sugerida:** Revisar calibração, matéria-prima e parâmetros dos lotes dessa máquina.

### Turnos

**Evidência:** O turno MANHA alcançou 123.9 aprovadas/h.

**Ação sugerida:** Comparar equipe, abastecimento e setup com os demais turnos.

### Oferta e demanda

**Evidência:** Componente Automotivo A tem o menor giro produção-vendas: 36.6%.

**Ação sugerida:** Reavaliar lotes e priorizar produtos com demanda proporcionalmente maior.

### Canal comercial

**Evidência:** DISTRIBUIDOR lidera o faturamento com R$ 5,052,552.40.

**Ação sugerida:** Preservar o canal líder e testar suas práticas nos demais canais.

### Região

**Evidência:** CENTRO-OESTE é a região de maior receita: R$ 4,056,377.52.

**Ação sugerida:** Priorizar cobertura comercial e disponibilidade dos produtos mais vendidos na região.

### Telemetria

**Evidência:** PRE-01 tem a maior proporção de leituras em alerta: 4.04%.

**Ação sugerida:** Inspecionar vibração e temperatura antes de ampliar a carga do equipamento.

### Manutenção

**Evidência:** PRE-01/Rolamento principal possui 99.5% de desgaste.

**Ação sugerida:** Planejar inspeção e verificar disponibilidade da peça de reposição.

## Gráficos exploratórios

- [01_producao_diaria](charts/01_producao_diaria.html)
- [02_rejeicao_por_maquina](charts/02_rejeicao_por_maquina.html)
- [03_faturamento_por_produto](charts/03_faturamento_por_produto.html)
- [04_producao_vs_vendas](charts/04_producao_vs_vendas.html)
- [05_vibracao_por_maquina](charts/05_vibracao_por_maquina.html)
- [06_desgaste_componentes](charts/06_desgaste_componentes.html)

## Método de detecção de anomalias

As anomalias de telemetria combinam o intervalo interquartil de temperatura, vibração e energia por máquina com o status operacional informado. O método sinaliza observações fora do padrão estatístico ou em estado de atenção/crítico. Ele não determina a causa nem confirma uma falha física.

## Limitações

- Os dados são sintéticos e demonstram o método, não o desempenho de uma empresa real.
- Produção aprovada menos vendas não representa estoque físico.
- Custos e margens são estimados com os campos disponíveis.
- Dias parciais nas extremidades entram nos totais, mas são excluídos do gráfico e da tendência diária de produção.
- A tendência linear resume o período e não constitui previsão futura.
- Anomalia estatística não implica defeito; requer avaliação técnica.
