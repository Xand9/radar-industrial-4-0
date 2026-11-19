from pathlib import Path

import plotly.express as px
import streamlit as st

from core import ui
from validar_qualidade import validate, write_reports


PROJECT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT / "data" / "generated"
REPORT_DIR = PROJECT / "reports" / "quality"


@st.cache_data(show_spinner=False)
def quality_results(data_signature: tuple):
    _, summary, issues, statistics = validate(DATA_DIR)
    write_reports(REPORT_DIR, DATA_DIR, summary, issues, statistics)
    return summary, issues, statistics


def _signature() -> tuple:
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(DATA_DIR.glob("*.csv")))


def render(ctx):
    ui.cabecalho("Qualidade dos dados", "Validação automática da base local usada na análise e na previsão")
    summary, issues, statistics = quality_results(_signature())
    errors = int((issues["severity"] == "ERRO").sum()) if not issues.empty else 0
    warnings = int((issues["severity"] == "AVISO").sum()) if not issues.empty else 0
    records = int(summary["registros"].sum()) if not summary.empty else 0

    c = st.columns(4)
    c[0].metric("Resultado", "APROVADA" if errors == 0 else "REPROVADA")
    c[1].metric("Registros verificados", ui.fint(records))
    c[2].metric("Regras com erro", ui.fint(errors))
    c[3].metric("Regras com aviso", ui.fint(warnings))

    if errors:
        st.error("A base possui violações críticas. Consulte os problemas abaixo.", icon=":material/error:")
    elif warnings:
        st.warning("A base não possui erros críticos, mas há avisos para revisão.", icon=":material/warning:")
    else:
        st.success("Nenhuma violação foi encontrada nas regras implementadas.", icon=":material/check_circle:")

    fig = px.bar(summary, x="tabela", y="registros", title="Registros por tabela",
                 color="registros", color_continuous_scale=["#203A62", "#19C6A3"])
    fig.update_layout(xaxis_title=None, yaxis_title="Registros", coloraxis_showscale=False)
    ui.grafico(fig, 370)

    st.markdown("#### Resumo estrutural")
    ui.tabela(summary.rename(columns={"tabela": "Tabela", "registros": "Registros", "colunas": "Colunas",
                                            "linhas_duplicadas": "Duplicadas", "ausencias_obrigatorias": "Ausências obrigatórias",
                                            "ausencias_totais": "Ausências totais"}))
    st.markdown("#### Problemas encontrados")
    if issues.empty:
        st.info("Nenhum problema encontrado.")
    else:
        ui.tabela(issues)
    with st.expander("Estatísticas descritivas"):
        ui.tabela(statistics)
    ui.nota("Verificações: duplicidades, ausências, chaves órfãs, domínios, valores inválidos, coerência temporal e plausibilidade da telemetria.")
