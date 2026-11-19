# 5. ETL e qualidade dos dados

## 5.1 Fluxo de ETL

### Extração

- Base sintética: leitura dos CSVs ou banco gerados pelo código oficial.
- Ambiente online: consultas SQL ao PostgreSQL/Supabase.
- Credenciais fornecidas por variável de ambiente ou segredo do Streamlit.

### Transformação

1. Converter UUIDs para representação consistente.
2. Remover espaços extras e padronizar categorias em maiúsculas.
3. Converter campos numéricos com erros para valor ausente controlado.
4. Converter datas para UTC e apresentar no fuso de Brasília.
5. Relacionar produção com máquinas.
6. Relacionar vendas com lotes de produção.
7. Criar produção aprovada, duração, tempo operado e custos.
8. Calcular disponibilidade, desempenho, qualidade e OEE estimado.
9. Classificar desgaste em normal, atenção e crítico.
10. Agregar telemetria antes de integrá-la aos demais fatos.

### Carga

- DataFrames tratados para análise e dashboard.
- Arquivos de saída da base sintética em `data/generated/`.
- Relatório de qualidade em `outputs/relatorio_qualidade.csv` e Markdown.

## 5.2 Validações obrigatórias planejadas

| Validação | Regra | Tratamento esperado |
|---|---|---|
| Duplicidade de PK | zero duplicidades | interromper geração/ETL |
| Chave nula | PK nunca nula | interromper |
| Chave órfã | FK deve encontrar dimensão | registrar erro e interromper |
| Quantidade inválida | valores não negativos | rejeitar linha |
| Rejeição inválida | rejeitada <= produzida | rejeitar linha |
| Total do pedido | total ≈ quantidade x preço | recalcular ou sinalizar |
| Cronologia | fim > início | rejeitar linha |
| Desgaste | 0 <= wear_pct <= 100 | limitar apenas se regra documentada; preferir rejeitar |
| Limiares | atenção < crítico | interromper |
| Domínios | status e turno conhecidos | padronizar ou marcar desconhecido |
| Datas futuras | dentro do período gerado | sinalizar |

## 5.3 Relatório de qualidade

Para cada tabela serão apresentados:

- número de registros e colunas;
- duplicidades totais e nas chaves;
- quantidade e percentual de ausentes por campo;
- chaves órfãs;
- mínimo, máximo, média e quartis dos campos numéricos;
- categorias inesperadas;
- regras de negócio violadas;
- decisão tomada para cada problema.

## 5.4 Qualidade proposital dos dados sintéticos

A base principal será gerada consistente. Para demonstrar ETL, um parâmetro opcional poderá introduzir uma pequena quantidade controlada de problemas, como espaços extras, ausências em campos não críticos e categorias com grafia inconsistente. A semente, a proporção e as correções serão documentadas. Não serão introduzidas violações silenciosas de chave primária ou estrangeira.

## 5.5 Evidências existentes

O módulo `core/transform.py` já implementa conversão de tipos, padronização de textos, fuso horário, relacionamentos e colunas derivadas. A etapa seguinte será transformar as validações acima em testes automatizados e relatório executável.

