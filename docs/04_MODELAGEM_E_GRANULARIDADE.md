# 4. Modelagem, relacionamentos e granularidade

## 4.1 Diagrama lógico

```text
machines (machine_id PK)
 |
 +-- 1:N --> production_events (production_id PK, machine_id FK, batch_id UQ)
 |              |
 |              +-- 1:0..N --> sales_orders (order_id PK, batch_id FK opcional)
 |
 +-- 1:N --> machine_telemetry (telemetry_id PK, machine_id FK)
 |
 +-- 1:N --> parts_wear (component_id PK, machine_id FK)
 |
 +-- 1:N --> wear_events (wear_event_id PK, machine_id FK)

parts_wear (machine_id + component_code)
 +-- 1:N lógico --> wear_events (machine_id + component_code)
```

## 4.2 Granularidade

| Tabela | Grão |
|---|---|
| machines | máquina |
| production_events | lote produzido por máquina |
| sales_orders | pedido de venda |
| machine_telemetry | leitura por máquina e instante |
| parts_wear | estado atual por máquina e componente |
| wear_events | medição histórica por máquina, componente e instante |

Misturar granularidades sem agregação pode duplicar valores. Por exemplo, relacionar diretamente todos os registros de telemetria com todos os lotes da mesma máquina multiplica linhas. Por isso, telemetria e desgaste são agregados por máquina e período antes da integração com indicadores produtivos.

## 4.3 Relacionamentos analíticos

- Produção recebe atributos da máquina por `machine_id`.
- Vendas podem receber máquina, turno e custo do lote por `batch_id`.
- Pedidos sem lote usam custo médio ponderado do produto como fallback.
- Telemetria é agregada por máquina e janela de tempo.
- Histórico de desgaste é relacionado ao estado atual por máquina e código do componente.

## 4.4 Integridade esperada

- Todo `machine_id` operacional deve existir em `machines`.
- `batch_id` de venda pode ser nulo, mas, quando preenchido, deve existir em produção.
- Uma chave primária não pode ser nula ou duplicada.
- Rejeição não pode superar produção.
- Fim do lote deve ser posterior ao início.
- Limite de atenção deve ser menor que o crítico.
- Desgaste deve permanecer entre 0 e 100%.

## 4.5 Volume planejado

O gerador oficial deverá aceitar período, quantidade de máquinas e semente. Configuração inicial proposta:

| Tabela | Volume aproximado para 30 dias | Justificativa |
|---|---:|---|
| machines | 4 | Cadastro mestre |
| production_events | 2.880 | 1 lote/hora por máquina |
| sales_orders | 2.000 a 2.500 | Parte dos lotes gera pedidos |
| machine_telemetry | 34.560 | Leitura a cada 5 minutos por máquina |
| parts_wear | 12 | 3 componentes por máquina |
| wear_events | 8.640 | Medição horária por componente |

Esse volume permite séries temporais, agrupamentos e detecção de tendências sem tornar a execução local excessivamente pesada.

