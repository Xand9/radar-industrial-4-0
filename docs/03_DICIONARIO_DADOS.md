# 3. Dicionário de dados

## 3.1 `machines` - cadastro de máquinas

Granularidade: uma linha por máquina.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| machine_id | UUID | Identificador da máquina | PK |
| machine_code | texto | Código curto da máquina | Único, obrigatório |
| machine_name | texto | Nome descritivo | Obrigatório |
| production_line | texto | Linha produtiva | Categoria |
| machine_type | texto | Tipo do equipamento | Categoria |
| nominal_capacity_per_hour | inteiro | Capacidade nominal por hora | > 0 |
| installed_at | data | Data de instalação | <= data atual |
| machine_status | texto | Situação cadastral | Domínio controlado |
| created_at | data/hora | Criação do registro | UTC |

## 3.2 `production_events` - lotes/eventos de produção

Granularidade: uma linha por lote produzido em uma máquina.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| production_id | inteiro | Identificador do evento | PK |
| batch_id | UUID | Identificador do lote | Único por lote |
| machine_id | UUID | Máquina responsável | FK -> machines.machine_id |
| product_code | texto | Código do produto | Obrigatório |
| product_name | texto | Nome do produto | Obrigatório |
| shift_name | texto | Turno | MANHA, TARDE ou NOITE |
| qty_produced | inteiro | Quantidade total | >= 0 |
| qty_rejected | inteiro | Quantidade rejeitada | 0 <= rejeitada <= produzida |
| downtime_minutes | decimal | Tempo de parada | >= 0 |
| cycle_time_seconds | decimal | Tempo de ciclo | > 0 |
| energy_kwh | decimal | Energia consumida no lote | >= 0 |
| unit_cost | decimal | Custo unitário estimado | >= 0 |
| started_at | data/hora | Início da produção | UTC |
| ended_at | data/hora | Fim da produção | > started_at |
| recorded_at | data/hora | Registro no sistema | UTC |

## 3.3 `sales_orders` - pedidos de venda

Granularidade: uma linha por pedido.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| order_id | inteiro | Identificador do pedido | PK |
| order_number | texto | Número comercial | Único |
| batch_id | UUID | Lote associado | FK opcional -> production_events.batch_id |
| product_code | texto | Código do produto | Obrigatório |
| product_name | texto | Nome do produto | Obrigatório |
| sales_channel | texto | Canal de venda | Domínio controlado |
| qty_sold | inteiro | Quantidade vendida | > 0 |
| unit_price | decimal | Preço unitário | >= 0 |
| total_amount | decimal | Valor total | qty_sold x unit_price |
| order_status | texto | Situação do pedido | Domínio controlado |
| customer_region | texto | Região do cliente | Categoria |
| created_at | data/hora | Data do pedido | UTC |

## 3.4 `machine_telemetry` - telemetria

Granularidade: uma leitura por máquina e instante.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| telemetry_id | inteiro | Identificador da leitura | PK quando persistido |
| machine_id | UUID | Máquina medida | FK -> machines.machine_id |
| temperature_c | decimal | Temperatura | °C, faixa plausível |
| vibration_mm_s | decimal | Vibração | mm/s, >= 0 |
| energy_kw | decimal | Potência | kW, >= 0 |
| pressure_bar | decimal | Pressão | bar, >= 0 |
| rpm | inteiro | Rotação | RPM, >= 0 |
| machine_status | texto | Situação da leitura | OPERANDO, ATENCAO ou CRITICO |
| recorded_at | data/hora | Instante da leitura | UTC |

## 3.5 `parts_wear` - estado atual dos componentes

Granularidade: uma linha por máquina e componente, contendo a medição mais recente.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| component_id | inteiro | Identificador do componente monitorado | PK |
| machine_id | UUID | Máquina | FK -> machines.machine_id |
| component_code | texto | Código do componente | Único dentro da máquina |
| component_name | texto | Nome do componente | Obrigatório |
| wear_pct | decimal | Desgaste atual | 0 a 100% |
| warning_threshold_pct | decimal | Limite de atenção | padrão 75% |
| critical_threshold_pct | decimal | Limite crítico | padrão 90% |
| estimated_remaining_hours | decimal | Horas restantes estimadas | >= 0 |
| last_inspection_at | data/hora | Última medição | UTC |

## 3.6 `wear_events` - histórico de desgaste

Granularidade: uma medição por máquina, componente e instante.

| Campo | Tipo | Descrição | Chave/regra |
|---|---|---|---|
| wear_event_id | inteiro | Identificador da medição | PK quando persistido |
| machine_id | UUID | Máquina | FK -> machines.machine_id |
| component_code | texto | Código do componente | Relaciona ao estado atual |
| component_name | texto | Nome do componente | Obrigatório |
| wear_pct | decimal | Desgaste medido | 0 a 100% |
| vibration_mm_s | decimal | Vibração associada | mm/s |
| temperature_c | decimal | Temperatura associada | °C |
| estimated_remaining_hours | decimal | Vida estimada no instante | >= 0 |
| measured_at | data/hora | Instante da medição | UTC |

