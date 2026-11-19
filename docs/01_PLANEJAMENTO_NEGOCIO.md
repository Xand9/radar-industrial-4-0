# 1. Planejamento do negócio

## 1.1 Cenário

Uma indústria de médio porte opera quatro linhas produtivas com máquinas que geram registros de produção e telemetria continuamente. A empresa vende diferentes produtos em múltiplos canais e regiões. Componentes das máquinas sofrem desgaste progressivo, criando risco de paradas, perdas de qualidade e custos inesperados.

A direção necessita integrar dados operacionais, comerciais, financeiros e de manutenção para entender o desempenho da fábrica e tomar decisões baseadas em evidências.

## 1.2 Problema de negócio

Os dados existem em fontes relacionadas, mas não são suficientes por si só para responder rapidamente:

- onde estão as maiores perdas de produtividade e qualidade;
- quais máquinas apresentam risco de falha;
- quais produtos e canais geram melhores resultados;
- se a produção está coerente com a demanda;
- quando uma intervenção de manutenção deve ser priorizada.

Sem integração e análise, a empresa corre risco de produzir itens com baixo giro, manter máquinas críticas em operação, aumentar refugo e tomar decisões comerciais sem considerar custos industriais.

## 1.3 Objetivo geral

Desenvolver uma solução integrada de Business Intelligence que gere uma base industrial sintética reproduzível, trate e valide os dados, calcule indicadores, identifique padrões e apresente informações gerenciais em um dashboard interativo.

## 1.4 Objetivos específicos

1. Modelar tabelas relacionadas de máquinas, produção, vendas, telemetria e desgaste.
2. Gerar dados plausíveis por código, com volume suficiente para análises temporais.
3. Executar ETL e validar integridade, duplicidade, ausência e domínio dos valores.
4. Medir produção, qualidade, disponibilidade, vendas, custos e risco de manutenção.
5. Comparar desempenho por máquina, produto, turno, canal, região e período.
6. Aplicar uma técnica de previsão de desgaste para apoiar manutenção preventiva.
7. Comunicar insights, limitações e recomendações gerenciais em painel interativo.

## 1.5 Usuários da informação

| Usuário | Decisões apoiadas | Informações necessárias |
|---|---|---|
| Direção industrial | Prioridades, investimentos e metas | KPIs executivos, custos, riscos e oportunidades |
| Gerência de produção | Distribuição de carga e melhoria de produtividade | Produção, capacidade, ciclo, paradas e rejeição |
| Qualidade | Redução de refugo e investigação de causas | Rejeição por máquina, turno, produto e horário |
| Manutenção | Planejamento de intervenções e peças | Telemetria, desgaste, vida restante e risco |
| Comercial | Mix, canais e regiões prioritárias | Demanda, faturamento, ticket e margem estimada |
| Controladoria | Acompanhamento de custos e resultado estimado | Custo de produção, refugo, CPV e margem |

## 1.6 Escopo

Incluído:

- geração e análise de dados industriais sintéticos;
- produção, vendas, telemetria, desgaste e cadastro de máquinas;
- ETL em Python/Pandas;
- dashboard em Streamlit/Plotly;
- atualização periódica por polling quando conectado ao banco;
- análise de manutenção preditiva.

Não incluído:

- estoque físico completo;
- impostos, despesas administrativas e lucro líquido;
- ordens reais de manutenção;
- dados pessoais identificáveis de clientes ou funcionários;
- controle direto das máquinas.

## 1.7 Critérios de sucesso

- base reproduzida com um único comando e semente documentada;
- ausência de chaves órfãs e duplicidades nas chaves primárias;
- indicadores calculados de forma consistente e documentada;
- dashboard navegável com filtros e tratamento de períodos sem dados;
- técnica analítica acompanhada de métricas e limitações;
- pelo menos três insights e três recomendações fundamentadas;
- todos os integrantes aptos a explicar o fluxo completo.

