# 📡 Radar Industrial 4.0 — Painel de BI

> Evolução para a prova prática de 4.000 pontos: consulte a [documentação da Parte 2](docs/README.md).

Painel gerencial interativo do **Desafio Industrial 4.0** (Desenvolvimento de Business Intelligence).
Consulta diretamente o PostgreSQL do Supabase alimentado pelo simulador do professor, trata os dados
com **Python + Pandas** e apresenta indicadores com **Streamlit + Plotly**, atualizando sozinho por
**polling**.

## Arquitetura

```
Simulador do professor (Python) ──INSERT──▶ Supabase PostgreSQL (6 tabelas)
                                                 │  SQL somente leitura (readonly_user, SSL)
                                                 ▼
                         core/db.py      SQLAlchemy + psycopg 3, consultas SQL, cache curto (ttl)
                                                 ▼
                         core/transform.py   Pandas: tipos, limpeza, fuso de Brasília, JOINs, colunas derivadas
                                                 ▼
                         core/kpis.py        Indicadores, 12 respostas, índice de risco, recomendações
                                                 ▼
                         paginas/*.py        9 páginas Streamlit + Plotly (filtros na barra lateral)
                                                 ▲
                         app.py              st.fragment(run_every=N s) → polling automático
```

| Pasta/arquivo | Função |
|---|---|
| `app.py` | Configuração, barra lateral (filtros + atualização), navegação, tratamento de erros |
| `core/db.py` | Conexão, todas as consultas SQL (texto exibido na página *Dados e conexão*) |
| `core/transform.py` | Tratamento com Pandas e relacionamentos entre tabelas |
| `core/kpis.py` | Cálculo dos indicadores e respostas (funções puras, testáveis) |
| `core/formatos.py`, `core/ui.py` | Formatação pt‑BR, identidade visual, componentes |
| `paginas/` | Executivo, Produção, Vendas, Produção×Vendas, Máquinas, Manutenção, Financeiro, Respostas, Dados |
| `tests/` | Teste offline com dados sintéticos no formato do banco |

## Como executar

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
#   → cole em DATABASE_URL a string somente leitura do PDF do professor
streamlit run app.py
```

Na barra lateral, escolha a fonte:

- **Base local (CSV):** lê os seis arquivos de `data/generated/` e funciona sem banco de dados;
- **Supabase:** usa `DATABASE_URL` e mantém as consultas PostgreSQL com polling.

O menu também possui as páginas **Qualidade dos dados**, com validação automática, e **Previsão de desgaste**, com MAE, RMSE, R² e estimativa do limite de 90%.

## Gerar a base sintética da Parte 2

O gerador oficial cria seis arquivos CSV relacionados sem depender do Supabase:

```bash
python gerar_base.py --dias 30 --maquinas 4 --seed 42
```

Os arquivos são salvos em `data/generated/`. Para controlar volume e período:

```bash
python gerar_base.py --dias 60 --maquinas 6 --seed 2026 \
  --intervalo-telemetria-min 10 --intervalo-desgaste-h 2 \
  --saida data/generated --sobrescrever
```

O mesmo conjunto de parâmetros e a mesma semente produzem as mesmas tabelas e chaves. O `metadata.json` registra os parâmetros e volumes. Teste estrutural:

```bash
python tests/teste_gerador.py
```

## Validar a qualidade da base

Após gerar os CSVs:

```bash
python validar_qualidade.py --dados data/generated --saida reports/quality
```

O comando verifica arquivos, colunas, duplicidades, ausências, chaves órfãs, domínios, valores inválidos e coerência temporal. São produzidos:

- `reports/quality/relatorio_qualidade.md`;
- `reports/quality/resumo_tabelas.csv`;
- `reports/quality/problemas.csv`;
- `reports/quality/estatisticas.csv`.

O processo retorna código diferente de zero quando encontra uma violação crítica, permitindo uso em testes automatizados.

## Executar a análise exploratória

```bash
python analisar_dados.py --dados data/generated --saida reports/analysis
```

A etapa gera tabelas analíticas em CSV, seis gráficos HTML interativos e um relatório com estatísticas, tendências, anomalias, oportunidades e limitações.

## Executar a previsão de desgaste

```bash
python prever_desgaste.py --dados data/generated --saida reports/prediction
```

O modelo ajusta uma regressão linear separada para cada máquina e componente. A divisão é cronológica, com 80% das observações para treino e 20% para teste. A execução calcula MAE, RMSE e R² e estima a data em que cada componente alcançará 90% de desgaste. Os resultados ficam em `reports/prediction/`.

Teste funcional:

```bash
python tests/teste_previsao.py
```

### Publicar no Streamlit Community Cloud
1. Suba a pasta para um repositório no GitHub (o `.gitignore` já impede o envio do `secrets.toml`).
2. Em share.streamlit.io → *New app* → escolha o repositório e `app.py`.
3. Em *Advanced settings → Secrets* cole: `DATABASE_URL = "postgresql://..."`.
4. Coloque o link gerado no relatório de entrega.

## Atualização automática — mecanismo: **polling**
Cada página roda dentro de `st.fragment(run_every=N)`. A cada N segundos (5, 10, 15, 30 ou 60,
escolhido na barra lateral) o bloco é reexecutado, o período relativo ("últimas 24 h") avança e as
consultas vão ao banco. As funções de consulta têm cache de 4–15 s, para não sobrecarregar o
Supabase. **Não é** assinatura nativa Supabase Realtime: é consulta periódica (polling).
A faixa no topo mostra a última telemetria gravada no banco e quantas leituras chegaram no último minuto.

## Indicadores e fórmulas
| Indicador | Fórmula / origem |
|---|---|
| Quantidade produzida / rejeitada | `SUM(qty_produced)` / `SUM(qty_rejected)` em `production_events` |
| Taxa de rejeição | rejeitados ÷ produzidos |
| Pedidos | `COUNT(*)` em `sales_orders` (todos os status) |
| Faturamento | `SUM(total_amount)` com `order_status ≠ 'CANCELADO'` |
| Ticket médio | faturamento ÷ pedidos não cancelados |
| Máquinas em atenção/crítica | status da leitura de telemetria mais recente de cada máquina (`DISTINCT ON`) |
| Componentes com desgaste elevado | `parts_wear.wear_pct ≥ warning_threshold_pct (75%)`; crítico ≥ 90% |
| Aprovadas por hora | (produzido − rejeitado) ÷ horas operando, sendo horas operando = (`ended_at − started_at`) − `downtime_minutes` |
| Uso da capacidade | produção por hora operando ÷ `nominal_capacity_per_hour` |
| OEE estimado | disponibilidade × desempenho × qualidade (por lote) |
| Giro de venda | vendido (não cancelado) ÷ aprovado |
| Custo estimado de produção | `qty_produced × unit_cost` |
| Custo dos rejeitados | `qty_rejected × unit_cost` |
| CPV estimado | `qty_sold × unit_cost` do lote ligado por `batch_id` (fallback: custo médio do produto) |
| Margem bruta estimada | receita − CPV estimado (**não é lucro líquido**) |
| Índice de risco (0–100) | 40% desgaste máx. + 30% % leituras em alerta + 15% vibração média/7 + 15% rejeição/10% |

## Tratamento de erros e ausência de dados
- Sem `DATABASE_URL` ou falha de conexão → mensagem clara e botão *Tentar novamente*.
- Falha momentânea durante o polling → nova tentativa automática (2 tentativas por consulta) e aviso; o próximo ciclo tenta de novo.
- Período/filtros sem registros → aviso "Nenhum registro encontrado…" em cada gráfico/tabela.
- Divisões por zero retornam "—" em vez de erro.

## Teste offline
```bash
python tests/teste_offline.py
```
Executa todas as páginas com dados sintéticos gerados pela mesma lógica do simulador e também com
o banco vazio. Serve para validar o código e as respostas sem depender da rede. No uso normal, o
seletor da barra lateral permite alternar entre **Base local (CSV)** e **Supabase**.

## Arquivos finais de entrega

- `entrega/Apresentacao_Radar_Industrial_4_0_Final.pptx` — apresentação com notas do orador;
- `entrega/Relatorio_Final_Radar_Industrial_4_0.pdf` — relatório técnico final;
- `entrega/Guia_Apresentacao_e_Defesa_Radar_Industrial_4_0.pdf` — roteiro, perguntas e checklist;
- `entrega/Radar_Industrial_4_0_Entrega_Final.zip` — pacote do projeto sem credenciais e arquivos temporários.

Integrantes: Beatriz Andrade Barbosa de Sousa, Pedro Henrique de Souza Pereira e Alexandre de Marcus Paiva Barcelos.
