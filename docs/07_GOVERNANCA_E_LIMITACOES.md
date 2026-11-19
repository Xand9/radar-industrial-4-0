# 7. Governança, segurança e limitações

## 7.1 Privacidade

A base não utiliza nomes, documentos, e-mails ou outros dados pessoais. Clientes são representados apenas por região e atributos comerciais agregados. Se o cenário for ampliado, deverão ser utilizados identificadores sintéticos sem relação com pessoas reais.

## 7.2 Segurança

- Senhas e URLs completas não ficam no código ou na documentação.
- `.env` e `.streamlit/secrets.toml` permanecem no `.gitignore`.
- O acesso ao painel deve utilizar, preferencialmente, usuário somente de leitura.
- Credenciais administrativas não devem ser compartilhadas nem publicadas.
- Capturas de tela não devem mostrar senhas, tokens ou URLs completas.
- Consultas do dashboard são somente leitura.

## 7.3 Qualidade e rastreabilidade

- A semente do gerador será registrada.
- Parâmetros de volume e período serão salvos em metadados.
- Cada execução de validação produzirá relatório datado.
- Fórmulas dos KPIs ficarão versionadas.
- Alterações relevantes deverão ser registradas em Git.

## 7.4 Uso responsável

- O índice de risco não será apresentado como probabilidade real de falha.
- Recomendações de manutenção exigem validação humana.
- O modelo não deve justificar punições ou avaliações individuais de trabalhadores.
- Resultados sintéticos demonstram método, não desempenho real da empresa.

## 7.5 Limitações do cenário

1. Não há módulo completo de estoque.
2. Produção menos vendas não equivale ao saldo físico.
3. Custos não incluem todas as despesas e tributos.
4. Margem estimada não é lucro líquido.
5. OEE é aproximado e não considera calendário industrial completo.
6. Sensores sintéticos simplificam fenômenos físicos complexos.
7. Ausência de ordens de manutenção impede confirmar falhas e intervenções reais.
8. Resultados dependem das regras usadas pelo gerador.
9. A previsão de desgaste pode falhar em tendências não lineares.

## 7.6 Riscos do projeto

| Risco | Impacto | Mitigação |
|---|---|---|
| Credencial publicada | acesso indevido | secrets, `.gitignore` e rotação de senha |
| Base incoerente | KPIs inválidos | testes de integridade antes da análise |
| Dupla contagem | valores inflados | respeitar granularidade e agregar antes dos joins |
| Modelo superestimado | decisão incorreta | métricas, limitações e validação humana |
| Dependência do Supabase | indisponibilidade na apresentação | base sintética local e instruções offline |
| Falta de domínio individual | perda na defesa | divisão de tópicos e perguntas simuladas |

