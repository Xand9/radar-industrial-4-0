# 8. Reprodução e roteiro de defesa

## 8.1 Fluxo implementado

```text
gerar_base.py -> seis CSVs -> validar_qualidade.py -> analisar_dados.py
              -> prever_desgaste.py -> dashboard Streamlit
              -> Base local ou Supabase -> Qualidade e Previsão
```

## 8.2 Execução no Windows

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python gerar_base.py --dias 30 --maquinas 4 --seed 42 --sobrescrever
python validar_qualidade.py
python analisar_dados.py
python prever_desgaste.py
python -m streamlit run app.py
```

No dashboard, selecionar **Base local (CSV)**. Para demonstrar o Supabase, selecionar **Supabase** e manter `DATABASE_URL` em `.streamlit/secrets.toml`.

## 8.3 Evidências da execução final

- 6 arquivos CSV relacionados e 48.515 registros;
- validação aprovada com zero regras em erro e zero avisos;
- 17 tabelas analíticas e 6 gráficos exploratórios;
- 349 registros de telemetria sinalizados como anomalia ou alerta;
- 12 componentes modelados;
- MAE médio de 1,112 ponto percentual;
- RMSE médio de 1,160 ponto percentual;
- R² médio de 0,9820;
- 11 páginas do dashboard executadas sem erro no teste offline;
- testes do gerador, validador, análise e previsão aprovados.

## 8.4 Roteiro da apresentação - 10 minutos

### Abertura e problema - 1 minuto

Apresentador 1 explica que a solução reúne produção, vendas, telemetria e desgaste para apoiar qualidade, planejamento comercial e manutenção.

### Base e modelagem - 1 minuto e 30 segundos

Apresentador 1 mostra os seis CSVs, a semente reproduzível, as chaves e as granularidades. Destacar que `machine_id` conecta os fatos operacionais às máquinas e `batch_id` conecta vendas à produção.

### ETL e qualidade - 1 minuto e 30 segundos

Apresentador 2 abre a página Qualidade dos dados. Mostrar 48.515 registros, zero erros, zero avisos e explicar as verificações de duplicidade, ausência, chave órfã, domínio e coerência.

### Análise exploratória - 1 minuto e 30 segundos

Apresentador 2 apresenta os KPIs: produção de 315.374 unidades, rejeição de 4,77%, faturamento de R$ 19,06 milhões e PRE-01 como máquina de maior rejeição, com 5,53%.

### Técnica analítica - 2 minutos

Apresentador 3 abre a página Previsão de desgaste. Explicar a divisão temporal 80/20, a regressão por componente e as métricas. Mostrar o rolamento da PRE-01 em 99,5% e explicar por que a confiança desse caso ficou insuficiente.

### Dashboard e decisões - 1 minuto e 30 segundos

Apresentador 3 demonstra o seletor Base local/Supabase, os filtros e as recomendações. Destacar inspeção imediata da PRE-01, revisão dos parâmetros de qualidade e ajuste do plano de produção à demanda.

### Encerramento - 1 minuto

Apresentador 1 resume o fluxo completo e reforça que os dados são sintéticos e que a previsão apoia, mas não substitui, inspeção técnica.

## 8.5 Plano de demonstração

1. Abrir o dashboard em Visão executiva.
2. Confirmar a fonte Base local (CSV).
3. Abrir Qualidade dos dados e mostrar o resultado APROVADA.
4. Abrir Manutenção e localizar PRE-01/Rolamento principal.
5. Abrir Previsão de desgaste e mostrar MAE, RMSE e R².
6. Voltar à Visão executiva e concluir com as recomendações.

Se o Supabase estiver indisponível, manter a fonte local. O modo local demonstra todas as etapas avaliadas sem depender da internet.

## 8.6 Checklist antes da apresentação

- testar `python -m streamlit run app.py`;
- manter o terminal aberto durante a apresentação;
- usar Base local como plano principal;
- ensaiar a troca de apresentadores;
- não expor `DATABASE_URL` nem senhas;
- levar o arquivo ZIP, o PDF e o PPTX em dois locais diferentes.
