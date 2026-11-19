# 9. Matriz de atendimento ao barema

Legenda: **pronto**, **parcial**, **planejado**.

| Critério | Pontos | Situação | Evidência/próxima ação |
|---|---:|---|---|
| Cenário, problema e objetivos | 150 | pronto | `01_PLANEJAMENTO_NEGOCIO.md` |
| Usuários e perguntas gerenciais | 150 | pronto | documentos 01 e 02 |
| KPIs: fórmula, unidade e interpretação | 200 | pronto | `02_PERGUNTAS_E_KPIS.md` |
| Coerência entre problema, dados e indicadores | 100 | pronto | documentos 01 a 04 |
| Gerador funcional e reproduzível | 250 | pronto | `gerar_base.py`, CLI parametrizável e teste de reprodução |
| Quatro ou mais tabelas e chaves | 200 | pronto | seis CSVs, PKs determinísticas e FKs validadas |
| Relacionamentos e granularidade | 200 | pronto na documentação | `04_MODELAGEM_E_GRANULARIDADE.md` |
| Variedade, plausibilidade e volume | 150 | pronto | execução padrão gera 48.515 registros em seis tabelas; parâmetros no `metadata.json` |
| ETL | 250 | pronto | `core/transform.py`, `core/dados.py`, integração local/Supabase e teste offline |
| Dicionário e qualidade | 150 | pronto | dicionário, `validar_qualidade.py` e relatórios automáticos em `reports/quality/` |
| Análise exploratória | 150 | pronto | `analisar_dados.py`, 17 tabelas, seis gráficos e relatório automático |
| Cálculos e comparações | 200 | pronto | `core/kpis.py`, teste offline e relatórios com resultados reproduzíveis |
| Técnica analítica | 250 | pronto | `prever_desgaste.py`, regressão por componente e divisão temporal 80/20 |
| Métricas, resultados e limitações | 150 | pronto | MAE, RMSE, R², confiança e limitações em `reports/prediction/` |
| Padrões, tendências e oportunidades | 150 | pronto | `reports/analysis/relatorio_analise.md` e tabelas de tendências, anomalias e oportunidades |
| Gráficos e organização visual | 150 | pronto | páginas Streamlit/Plotly |
| Dashboard, filtros e navegação | 200 | pronto | `app.py` e `paginas/` |
| Insights sustentados | 150 | pronto | relatório automático consolida tendências, anomalias e evidências numéricas |
| Recomendações fundamentadas | 150 | pronto | tabela de oportunidades relaciona evidência, impacto e ação sugerida |
| Qualidade, privacidade e segurança | 50 | pronto na documentação | documento 07 e secrets fora do código |
| Integração do fluxo | 150 | pronto | seletor Base local/Supabase e páginas de qualidade e previsão no dashboard |
| Organização e reprodução | 100 | pronto | README contém geração, validação, análise, previsão e execução do painel |
| Demonstração prática | 150 | pronto | dashboard demonstra dados locais, qualidade, métricas e previsão de 90% |
| Domínio técnico e respostas | 200 | pronto para ensaio | documentos 08 e 11 com roteiro, perguntas e respostas |

## Prioridade de implementação

1. Ensaiar a apresentação e a troca de apresentadores.
2. Entregar o pacote final, o relatório e os slides.

