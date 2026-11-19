# Documentação - Prova Prática de Business Intelligence

Esta pasta documenta a evolução do projeto **Radar Industrial 4.0** para a prova prática de 4.000 pontos.

## Identificação

- Disciplina: Desenvolvimento de Business Intelligence
- Cenário: Indústria 4.0 - produção, vendas, telemetria e manutenção preditiva
- Integrantes:
  - Beatriz Andrade Barbosa de Sousa
  - Pedro Henrique de Souza Pereira
  - **Alexandre de Marcus Paiva Barcelos**

## Documentos

1. [Planejamento do negócio](01_PLANEJAMENTO_NEGOCIO.md)
2. [Perguntas gerenciais e KPIs](02_PERGUNTAS_E_KPIS.md)
3. [Dicionário de dados](03_DICIONARIO_DADOS.md)
4. [Modelagem, relacionamentos e granularidade](04_MODELAGEM_E_GRANULARIDADE.md)
5. [ETL e qualidade dos dados](05_ETL_E_QUALIDADE.md)
6. [Análise exploratória e técnica analítica](06_ANALISE_E_TECNICA_ANALITICA.md)
7. [Governança, segurança e limitações](07_GOVERNANCA_E_LIMITACOES.md)
8. [Reprodução e roteiro de defesa](08_REPRODUCAO_E_DEFESA.md)
9. [Matriz de atendimento ao barema](09_MATRIZ_DO_BAREMA.md)
10. [Relatório final](10_RELATORIO_FINAL.md)
11. [Perguntas e respostas para a defesa](11_PERGUNTAS_DEFESA.md)

## Situação atual

O dashboard, os tratamentos com Pandas, os KPIs, as perguntas gerenciais e as recomendações já existem. Para a etapa de 4.000 pontos falta concluir o ensaio e consolidar a entrega final.

Concluído: `gerar_base.py` reproduz seis CSVs relacionados a partir de período, quantidade de máquinas, intervalos e semente. `validar_qualidade.py` verifica estrutura, duplicidades, ausências, chaves órfãs, domínios, valores e coerência. `analisar_dados.py` produz estatísticas, 17 tabelas, seis gráficos, tendências, anomalias e oportunidades. `prever_desgaste.py` prevê o limite de 90% por componente e calcula MAE, RMSE e R² com teste temporal. O dashboard alterna entre CSV local e Supabase e exibe qualidade e previsão em páginas próprias.

Os documentos registram requisitos e decisões. Itens futuros estão marcados como **planejado**, evitando apresentar funcionalidades não implementadas como concluídas.

