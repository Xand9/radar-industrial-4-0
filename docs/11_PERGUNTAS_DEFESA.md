# Perguntas e respostas para a defesa

## Base e modelagem

### Por que usar seis tabelas?

Cada tabela representa uma granularidade diferente: cadastro de máquinas, lotes de produção, pedidos, leituras de sensores, estado atual das peças e histórico de desgaste. Separar essas entidades evita duplicação e permite relacionamentos claros.

### Como a base é reproduzível?

O gerador recebe uma semente. Com os mesmos parâmetros e a mesma semente, ele produz as mesmas chaves e os mesmos valores. O `metadata.json` registra os parâmetros utilizados.

### Qual é a diferença entre `parts_wear` e `wear_events`?

`parts_wear` guarda o estado atual de cada componente. `wear_events` guarda cada medição histórica e permite calcular tendência e previsão.

### Como as chaves órfãs são detectadas?

O validador compara cada chave estrangeira com a chave da tabela de referência. Um `machine_id` inexistente em `machines` ou um `batch_id` inexistente em produção gera erro.

## Indicadores e ETL

### Como a taxa de rejeição é calculada?

Quantidade rejeitada dividida pela quantidade produzida. O cálculo usa a soma do período, não a média simples das taxas dos lotes.

### Por que produção menos vendas não representa estoque?

O conjunto não registra estoque inicial, transferências, perdas, devoluções ou momento exato de disponibilidade. A diferença indica desequilíbrio entre oferta e demanda, mas não é saldo contábil de estoque.

### Por que a margem estimada não é lucro líquido?

Ela desconta apenas o custo de produção estimado. Despesas administrativas, impostos, frete, comissões e outros custos não estão presentes.

### Como o OEE foi estimado?

Disponibilidade multiplicada por desempenho e qualidade. A disponibilidade usa tempo operando sobre duração do lote, o desempenho compara a produção com a capacidade nominal e a qualidade usa aprovadas sobre produzidas.

## Qualidade

### O que significa base aprovada?

Significa que nenhuma regra implementada encontrou violação. Isso não prova que os dados representam uma fábrica real.

### Quais regras foram verificadas?

Arquivos e colunas obrigatórias, duplicidades, ausências, chaves órfãs, domínios, valores negativos, datas, rejeição maior que produção, coerência dos pedidos, desgaste e faixas de telemetria.

## Técnica analítica

### Por que regressão linear?

O desgaste sintético cresce aproximadamente de forma linear e a regressão permite explicar a taxa em pontos percentuais por hora e calcular o instante de 90%. O modelo é simples, interpretável e adequado ao histórico disponível.

### Por que separar treino e teste no tempo?

Uma divisão aleatória misturaria medições futuras no treino. A divisão temporal avalia se o modelo treinado no passado consegue prever o trecho posterior.

### O que significam MAE, RMSE e R²?

MAE é o erro absoluto médio em pontos percentuais. RMSE dá mais peso a erros grandes. R² mede quanto da variação do teste o modelo explica. Um R² negativo indica desempenho pior que usar a média do teste.

### Por que o R² médio é alto, mas existe um caso com confiança insuficiente?

Onze componentes mantiveram comportamento aproximadamente linear. O rolamento da PRE-01 atingiu o teto de 99,5%, enquanto a reta continuou crescendo. Nesse caso o modelo errou no teste e o sistema expôs a limitação.

### O que acontece após uma manutenção?

A série anterior perde validade para a nova peça. O modelo deve reiniciar o histórico ou incluir uma identificação do ciclo do componente.

## Dashboard e segurança

### Como o painel funciona sem Supabase?

O módulo local lê os seis CSVs e executa com Pandas operações equivalentes às consultas do banco. O seletor da barra lateral troca a fonte.

### Como as credenciais são protegidas?

`DATABASE_URL` fica em `.streamlit/secrets.toml` ou variável de ambiente. O arquivo de segredos está no `.gitignore` e não entra no pacote final.

### O painel usa tempo real?

No Supabase ele usa polling, isto é, consultas periódicas. Não usa assinatura nativa do Supabase Realtime. No modo local, os CSVs são estáticos até uma nova geração ou recarga.

### Qual é a principal recomendação?

Inspecionar o rolamento principal da PRE-01, que atingiu 99,5%, e revisar a qualidade dessa máquina, pois ela também apresentou a maior rejeição.

### Qual é a principal limitação do trabalho?

Os dados são sintéticos. O projeto demonstra método e integração, mas uma aplicação real exige validação com histórico industrial, eventos de manutenção e critérios definidos por engenheiros.
