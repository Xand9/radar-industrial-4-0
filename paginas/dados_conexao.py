import re

import pandas as pd

import streamlit as st

from core import db, ui
from core.transform import BR_TZ


def _host_mascarado() -> str:
    url = db._database_url() or ""
    m = re.search(r"@([^:/]+)", url)
    return m.group(1) if m else "—"


def render(ctx):
    local = db.fonte_atual() == "local"
    ui.cabecalho("Dados e fonte ativa",
                 "Estrutura das seis tabelas, relacionamentos e origem utilizada pelo dashboard")

    with st.container(border=True):
        c = st.columns(3)
        c[0].markdown(f"**Status:** {ui.badge('OPERANDO')} disponível", unsafe_allow_html=True)
        if local:
            c[1].markdown("**Fonte:** `data/generated/*.csv`")
            c[2].markdown("**Modo:** leitura local dos seis arquivos gerados")
        else:
            c[1].markdown(f"**Servidor:** `{_host_mascarado()}`")
            usuario = re.search(r"//([^:.@]+)", db._database_url() or "")
            c[2].markdown(f"**Usuário:** `{usuario.group(1) if usuario else '—'}` · somente consultas SELECT")
        p = db.pulso().iloc[0]
        ui.nota(("Último instante disponível nos CSVs" if local else "Hora do servidor PostgreSQL") +
                f": {p['agora_banco']} · lotes no intervalo mais recente: {int(p['producao_5min'])}")

    st.markdown("#### As seis tabelas")
    cont = db.contagens()
    cols = st.columns(6)
    for col, (_, r) in zip(cols, cont.iterrows()):
        col.metric(r["tabela"], ui.fint(r["registros"]))

    st.markdown("#### Relacionamentos")
    st.code("""machines (machine_id PK)
 ├──< production_events.machine_id      (1 máquina → N lotes de produção)
 │        └──< sales_orders.batch_id     (1 lote → 0..N pedidos de venda)
 ├──< machine_telemetry.machine_id      (1 máquina → milhares de leituras)
 ├──< wear_events.machine_id            (histórico de medições de desgaste)
 └──< parts_wear.machine_id             (estado ATUAL: 1 linha por máquina+componente)""", language="text")
    fks = db.chaves_estrangeiras()
    if not fks.empty:
        ui.tabela(fks.drop_duplicates())

    st.markdown("#### Campos e tipos de dados")
    colunas = db.colunas()
    tab = st.tabs(db.TABELAS)
    for t, nome in zip(tab, db.TABELAS):
        with t:
            ui.tabela(colunas[colunas["tabela"] == nome].drop(columns="tabela"))
            st.caption("Registros mais recentes:")
            st.dataframe(db.amostra(nome, 8), width="stretch", hide_index=True)

    st.markdown("#### Registros mais recentes")
    ultimas = db.amostra("machine_telemetry", 12).copy()
    if not ultimas.empty:
        ultimas["recorded_at"] = (pd.to_datetime(ultimas["recorded_at"], utc=True)
                                  .dt.tz_convert(BR_TZ).dt.strftime("%d/%m %H:%M:%S"))
    st.dataframe(ultimas, width="stretch", hide_index=True)
    ui.nota("Os dados são relidos dos CSVs ao limpar o cache." if local else
            "Com o simulador ligado, novas linhas aparecem por polling e cache de poucos segundos.")

    if not local:
        st.markdown("#### Consultas SQL utilizadas")
        for nome, sql in db.SQL.items():
            with st.expander(nome):
                st.code(sql.strip(), language="sql")
