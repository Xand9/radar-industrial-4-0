# Relatório automático de qualidade dos dados

- Data da execução (UTC): 2026-11-17T14:03:03.894651+00:00
- Diretório analisado: `C:\Users\Xand\Documents\Codex\2026-11-12\preciso-da-sua-ajuda-para-fazer\outputs\painel_industria40_parte2\data\generated`
- Resultado: **APROVADA**
- Regras com erro: **0**
- Regras com aviso: **0**

## Resumo das tabelas

| tabela | registros | colunas | linhas_duplicadas | ausencias_obrigatorias | ausencias_totais |
| --- | --- | --- | --- | --- | --- |
| machines | 4 | 9 | 0 | 0 | 0 |
| production_events | 2884 | 15 | 0 | 0 | 0 |
| sales_orders | 2399 | 12 | 0 | 0 | 0 |
| machine_telemetry | 34564 | 9 | 0 | 0 | 0 |
| parts_wear | 12 | 9 | 0 | 0 | 0 |
| wear_events | 8652 | 9 | 0 | 0 | 0 |

## Problemas encontrados

Nenhuma violação foi encontrada nas regras implementadas.

## Estatísticas descritivas

Foram calculadas estatísticas para 28 campos numéricos. Consulte `estatisticas.csv`.

## Regras cobertas

- existência dos seis arquivos e das colunas obrigatórias;
- duplicidade de linhas, chaves primárias e chaves únicas;
- valores ausentes em campos obrigatórios;
- chaves estrangeiras órfãs;
- domínios de status, turno, canal e região;
- quantidades, valores e medições negativas;
- rejeição maior que produção;
- coerência de datas e tempo de parada;
- valor do pedido versus quantidade multiplicada pelo preço;
- desgaste, limiares e vida restante;
- faixas de plausibilidade da telemetria.

## Limitação

A aprovação confirma as regras implementadas, não a veracidade de uma operação industrial real.
