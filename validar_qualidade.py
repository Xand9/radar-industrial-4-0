"""Validação automatizada da base sintética Industrial 4.0.

Saídas:
    relatorio_qualidade.md  - relatório legível
    resumo_tabelas.csv      - volumes, duplicidades e ausências
    problemas.csv           - regras violadas
    estatisticas.csv        - estatísticas descritivas numéricas

Exemplo:
    python validar_qualidade.py --dados data/generated
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


TABLE_SPECS = {
    "machines": {
        "pk": ["machine_id"],
        "required": [
            "machine_id", "machine_code", "machine_name", "production_line",
            "machine_type", "nominal_capacity_per_hour", "installed_at",
            "machine_status", "created_at",
        ],
    },
    "production_events": {
        "pk": ["production_id"],
        "unique": [["batch_id"]],
        "required": [
            "production_id", "batch_id", "machine_id", "product_code",
            "product_name", "shift_name", "qty_produced", "qty_rejected",
            "downtime_minutes", "cycle_time_seconds", "energy_kwh", "unit_cost",
            "started_at", "ended_at", "recorded_at",
        ],
    },
    "sales_orders": {
        "pk": ["order_id"],
        "unique": [["order_number"]],
        "required": [
            "order_id", "order_number", "product_code", "product_name",
            "sales_channel", "qty_sold", "unit_price", "total_amount",
            "order_status", "customer_region", "created_at",
        ],
        "nullable": ["batch_id"],
    },
    "machine_telemetry": {
        "pk": ["telemetry_id"],
        "required": [
            "telemetry_id", "machine_id", "temperature_c", "vibration_mm_s",
            "energy_kw", "pressure_bar", "rpm", "machine_status", "recorded_at",
        ],
    },
    "parts_wear": {
        "pk": ["component_id"],
        "unique": [["machine_id", "component_code"]],
        "required": [
            "component_id", "machine_id", "component_code", "component_name",
            "wear_pct", "warning_threshold_pct", "critical_threshold_pct",
            "estimated_remaining_hours", "last_inspection_at",
        ],
    },
    "wear_events": {
        "pk": ["wear_event_id"],
        "required": [
            "wear_event_id", "machine_id", "component_code", "component_name",
            "wear_pct", "vibration_mm_s", "temperature_c",
            "estimated_remaining_hours", "measured_at",
        ],
    },
}

DATE_COLUMNS = {
    "machines": ["installed_at", "created_at"],
    "production_events": ["started_at", "ended_at", "recorded_at"],
    "sales_orders": ["created_at"],
    "machine_telemetry": ["recorded_at"],
    "parts_wear": ["last_inspection_at"],
    "wear_events": ["measured_at"],
}

DOMAINS = {
    ("machines", "machine_status"): {"OPERANDO", "ATENCAO", "CRITICO", "INATIVO", "MANUTENCAO"},
    ("production_events", "shift_name"): {"MANHA", "TARDE", "NOITE"},
    ("sales_orders", "order_status"): {"FATURADO", "PENDENTE", "ENVIADO", "CANCELADO"},
    ("sales_orders", "sales_channel"): {"E-COMMERCE", "DISTRIBUIDOR", "VENDA_DIRETA", "REPRESENTANTE"},
    ("sales_orders", "customer_region"): {"SUDESTE", "SUL", "CENTRO-OESTE", "NORDESTE", "NORTE"},
    ("machine_telemetry", "machine_status"): {"OPERANDO", "ATENCAO", "CRITICO"},
}


@dataclass(frozen=True)
class Issue:
    severity: str
    category: str
    table: str
    rule: str
    count: int
    example: str = ""


def add_issue(
    issues: list[Issue], severity: str, category: str, table: str,
    rule: str, mask_or_count, frame: pd.DataFrame | None = None,
) -> None:
    if isinstance(mask_or_count, pd.Series):
        count = int(mask_or_count.fillna(False).sum())
        example = ""
        if count and frame is not None:
            rows = frame.loc[mask_or_count.fillna(False)].head(3)
            example = rows.to_dict(orient="records").__str__()[:500]
    else:
        count = int(mask_or_count)
        example = ""
    if count:
        issues.append(Issue(severity, category, table, rule, count, example))


def load_tables(data_directory: Path) -> tuple[dict[str, pd.DataFrame], list[Issue]]:
    tables: dict[str, pd.DataFrame] = {}
    issues: list[Issue] = []
    for table, spec in TABLE_SPECS.items():
        path = data_directory / f"{table}.csv"
        if not path.exists():
            issues.append(Issue("ERRO", "arquivo", table, f"Arquivo ausente: {path.name}", 1))
            continue
        try:
            frame = pd.read_csv(path)
        except Exception as exc:
            issues.append(Issue("ERRO", "arquivo", table, f"Falha ao ler CSV: {exc}", 1))
            continue
        tables[table] = frame
        missing_columns = sorted(set(spec["required"] + spec.get("nullable", [])) - set(frame.columns))
        if missing_columns:
            issues.append(
                Issue("ERRO", "estrutura", table, f"Colunas ausentes: {', '.join(missing_columns)}", len(missing_columns))
            )
    return tables, issues


def convert_types(tables: dict[str, pd.DataFrame], issues: list[Issue]) -> None:
    for table, columns in DATE_COLUMNS.items():
        if table not in tables:
            continue
        for column in columns:
            if column not in tables[table]:
                continue
            original_not_null = tables[table][column].notna()
            converted = pd.to_datetime(tables[table][column], errors="coerce", utc=True)
            invalid = original_not_null & converted.isna()
            add_issue(
                issues, "ERRO", "tipo", table,
                f"{column} contém data/hora inválida", invalid, tables[table],
            )
            tables[table][column] = converted


def validate_structure(tables: dict[str, pd.DataFrame], issues: list[Issue]) -> pd.DataFrame:
    summary_rows = []
    for table, frame in tables.items():
        spec = TABLE_SPECS[table]
        duplicated_rows = int(frame.duplicated().sum())
        add_issue(issues, "ERRO", "duplicidade", table, "Linhas completamente duplicadas", duplicated_rows)

        pk = spec["pk"]
        if set(pk).issubset(frame.columns):
            duplicate_pk = frame.duplicated(pk, keep=False)
            add_issue(issues, "ERRO", "duplicidade", table, f"Chave primária duplicada: {pk}", duplicate_pk, frame)
            null_pk = frame[pk].isna().any(axis=1)
            add_issue(issues, "ERRO", "ausencia", table, f"Chave primária nula: {pk}", null_pk, frame)

        for columns in spec.get("unique", []):
            if set(columns).issubset(frame.columns):
                duplicate_unique = frame.duplicated(columns, keep=False) & frame[columns].notna().all(axis=1)
                add_issue(issues, "ERRO", "duplicidade", table, f"Chave única duplicada: {columns}", duplicate_unique, frame)

        required_missing = 0
        for column in spec["required"]:
            if column in frame:
                mask = frame[column].isna()
                required_missing += int(mask.sum())
                add_issue(issues, "ERRO", "ausencia", table, f"Campo obrigatório ausente: {column}", mask, frame)

        summary_rows.append(
            {
                "tabela": table,
                "registros": len(frame),
                "colunas": len(frame.columns),
                "linhas_duplicadas": duplicated_rows,
                "ausencias_obrigatorias": required_missing,
                "ausencias_totais": int(frame.isna().sum().sum()),
            }
        )
    return pd.DataFrame(summary_rows)


def validate_foreign_keys(tables: dict[str, pd.DataFrame], issues: list[Issue]) -> None:
    if "machines" in tables and "machine_id" in tables["machines"]:
        machine_ids = set(tables["machines"]["machine_id"].dropna().astype(str))
        for table in ["production_events", "machine_telemetry", "parts_wear", "wear_events"]:
            if table in tables and "machine_id" in tables[table]:
                values = tables[table]["machine_id"].astype(str)
                mask = tables[table]["machine_id"].notna() & ~values.isin(machine_ids)
                add_issue(issues, "ERRO", "integridade", table, "machine_id órfão", mask, tables[table])

    if "production_events" in tables and "sales_orders" in tables:
        production = tables["production_events"]
        sales = tables["sales_orders"]
        if "batch_id" in production and "batch_id" in sales:
            batches = set(production["batch_id"].dropna().astype(str))
            mask = sales["batch_id"].notna() & ~sales["batch_id"].astype(str).isin(batches)
            add_issue(issues, "ERRO", "integridade", "sales_orders", "batch_id órfão", mask, sales)

    if "parts_wear" in tables and "wear_events" in tables:
        parts = tables["parts_wear"]
        wear = tables["wear_events"]
        required = {"machine_id", "component_code"}
        if required.issubset(parts.columns) and required.issubset(wear.columns):
            current_components = set(zip(parts["machine_id"].astype(str), parts["component_code"].astype(str)))
            historical_components = set(zip(wear["machine_id"].astype(str), wear["component_code"].astype(str)))
            missing_current = historical_components - current_components
            if missing_current:
                issues.append(
                    Issue("ERRO", "integridade", "wear_events", "Componente histórico sem estado atual", len(missing_current), str(list(missing_current)[:3]))
                )


def validate_domains(tables: dict[str, pd.DataFrame], issues: list[Issue]) -> None:
    for (table, column), allowed in DOMAINS.items():
        if table not in tables or column not in tables[table]:
            continue
        frame = tables[table]
        values = frame[column].astype("string").str.strip().str.upper()
        mask = frame[column].notna() & ~values.isin(allowed)
        add_issue(
            issues, "ERRO", "dominio", table,
            f"{column} fora do domínio {sorted(allowed)}", mask, frame,
        )


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def validate_business_rules(tables: dict[str, pd.DataFrame], issues: list[Issue]) -> None:
    if "machines" in tables:
        df = tables["machines"]
        if "nominal_capacity_per_hour" in df:
            mask = numeric(df, "nominal_capacity_per_hour") <= 0
            add_issue(issues, "ERRO", "valor", "machines", "Capacidade nominal deve ser positiva", mask, df)

    if "production_events" in tables:
        df = tables["production_events"]
        numeric_columns = ["qty_produced", "qty_rejected", "downtime_minutes", "energy_kwh", "unit_cost"]
        for column in numeric_columns:
            if column in df:
                mask = numeric(df, column) < 0
                add_issue(issues, "ERRO", "valor", "production_events", f"{column} não pode ser negativo", mask, df)
        if {"qty_produced", "qty_rejected"}.issubset(df.columns):
            mask = numeric(df, "qty_rejected") > numeric(df, "qty_produced")
            add_issue(issues, "ERRO", "coerencia", "production_events", "Rejeição maior que produção", mask, df)
        if {"started_at", "ended_at"}.issubset(df.columns):
            mask = df["ended_at"] <= df["started_at"]
            add_issue(issues, "ERRO", "cronologia", "production_events", "Fim não é posterior ao início", mask, df)
        if {"started_at", "ended_at", "downtime_minutes"}.issubset(df.columns):
            duration = (df["ended_at"] - df["started_at"]).dt.total_seconds() / 60
            mask = numeric(df, "downtime_minutes") > duration
            add_issue(issues, "ERRO", "coerencia", "production_events", "Parada maior que duração do lote", mask, df)

    if "sales_orders" in tables:
        df = tables["sales_orders"]
        for column in ["qty_sold", "unit_price", "total_amount"]:
            if column in df:
                mask = numeric(df, column) < 0
                add_issue(issues, "ERRO", "valor", "sales_orders", f"{column} não pode ser negativo", mask, df)
        if {"qty_sold", "unit_price", "total_amount"}.issubset(df.columns):
            expected = numeric(df, "qty_sold") * numeric(df, "unit_price")
            mask = (numeric(df, "total_amount") - expected).abs() > 0.011
            add_issue(issues, "ERRO", "coerencia", "sales_orders", "Valor total diferente de quantidade x preço", mask, df)

    if "machine_telemetry" in tables:
        df = tables["machine_telemetry"]
        for column in ["vibration_mm_s", "energy_kw", "pressure_bar", "rpm"]:
            if column in df:
                mask = numeric(df, column) < 0
                add_issue(issues, "ERRO", "valor", "machine_telemetry", f"{column} não pode ser negativo", mask, df)
        if "temperature_c" in df:
            temp = numeric(df, "temperature_c")
            mask = ~temp.between(-20, 200)
            add_issue(issues, "AVISO", "plausibilidade", "machine_telemetry", "Temperatura fora da faixa plausível [-20, 200]", mask, df)

    for table in ["parts_wear", "wear_events"]:
        if table not in tables:
            continue
        df = tables[table]
        if "wear_pct" in df:
            mask = ~numeric(df, "wear_pct").between(0, 100)
            add_issue(issues, "ERRO", "valor", table, "Desgaste deve estar entre 0 e 100%", mask, df)
        if "estimated_remaining_hours" in df:
            mask = numeric(df, "estimated_remaining_hours") < 0
            add_issue(issues, "ERRO", "valor", table, "Horas restantes não podem ser negativas", mask, df)

    if "parts_wear" in tables:
        df = tables["parts_wear"]
        if {"warning_threshold_pct", "critical_threshold_pct"}.issubset(df.columns):
            mask = numeric(df, "warning_threshold_pct") >= numeric(df, "critical_threshold_pct")
            add_issue(issues, "ERRO", "coerencia", "parts_wear", "Limite de atenção deve ser menor que o crítico", mask, df)


def descriptive_statistics(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table, frame in tables.items():
        for column in frame.select_dtypes(include="number").columns:
            series = pd.to_numeric(frame[column], errors="coerce").dropna()
            if series.empty:
                continue
            rows.append(
                {
                    "tabela": table,
                    "campo": column,
                    "n": len(series),
                    "media": series.mean(),
                    "desvio_padrao": series.std(),
                    "minimo": series.min(),
                    "q1": series.quantile(0.25),
                    "mediana": series.median(),
                    "q3": series.quantile(0.75),
                    "maximo": series.max(),
                }
            )
    return pd.DataFrame(rows)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    """Tabela Markdown simples, sem depender do pacote opcional tabulate."""
    if frame.empty:
        return ""
    safe = frame.fillna("").astype(str).map(lambda value: value.replace("|", "\\|"))
    columns = [str(column).replace("|", "\\|") for column in safe.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in safe.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def validate(data_directory: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tables, issues = load_tables(data_directory)
    convert_types(tables, issues)
    summary = validate_structure(tables, issues)
    validate_foreign_keys(tables, issues)
    validate_domains(tables, issues)
    validate_business_rules(tables, issues)
    issues_df = pd.DataFrame([asdict(issue) for issue in issues], columns=[
        "severity", "category", "table", "rule", "count", "example"
    ])
    statistics = descriptive_statistics(tables)
    return tables, summary, issues_df, statistics


def markdown_report(
    data_directory: Path,
    summary: pd.DataFrame,
    issues: pd.DataFrame,
    statistics: pd.DataFrame,
) -> str:
    errors = int((issues["severity"] == "ERRO").sum()) if not issues.empty else 0
    warnings = int((issues["severity"] == "AVISO").sum()) if not issues.empty else 0
    status = "APROVADA" if errors == 0 else "REPROVADA"
    lines = [
        "# Relatório automático de qualidade dos dados",
        "",
        f"- Data da execução (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Diretório analisado: `{data_directory.resolve()}`",
        f"- Resultado: **{status}**",
        f"- Regras com erro: **{errors}**",
        f"- Regras com aviso: **{warnings}**",
        "",
        "## Resumo das tabelas",
        "",
        dataframe_to_markdown(summary) if not summary.empty else "Nenhuma tabela válida foi carregada.",
        "",
        "## Problemas encontrados",
        "",
    ]
    if issues.empty:
        lines.append("Nenhuma violação foi encontrada nas regras implementadas.")
    else:
        display = issues.drop(columns="example").copy()
        lines.append(dataframe_to_markdown(display))
        examples = issues[issues["example"].astype(str).str.len() > 0]
        if not examples.empty:
            lines.extend(["", "## Exemplos de registros problemáticos", ""])
            for _, row in examples.iterrows():
                lines.extend([
                    f"### {row['table']} - {row['rule']}",
                    "",
                    f"`{row['example']}`",
                    "",
                ])
    lines.extend([
        "",
        "## Estatísticas descritivas",
        "",
        f"Foram calculadas estatísticas para {len(statistics)} campos numéricos. Consulte `estatisticas.csv`.",
        "",
        "## Regras cobertas",
        "",
        "- existência dos seis arquivos e das colunas obrigatórias;",
        "- duplicidade de linhas, chaves primárias e chaves únicas;",
        "- valores ausentes em campos obrigatórios;",
        "- chaves estrangeiras órfãs;",
        "- domínios de status, turno, canal e região;",
        "- quantidades, valores e medições negativas;",
        "- rejeição maior que produção;",
        "- coerência de datas e tempo de parada;",
        "- valor do pedido versus quantidade multiplicada pelo preço;",
        "- desgaste, limiares e vida restante;",
        "- faixas de plausibilidade da telemetria.",
        "",
        "## Limitação",
        "",
        "A aprovação confirma as regras implementadas, não a veracidade de uma operação industrial real.",
    ])
    return "\n".join(lines) + "\n"


def write_reports(
    output_directory: Path,
    data_directory: Path,
    summary: pd.DataFrame,
    issues: pd.DataFrame,
    statistics: pd.DataFrame,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_directory / "resumo_tabelas.csv", index=False, encoding="utf-8")
    issues.to_csv(output_directory / "problemas.csv", index=False, encoding="utf-8")
    statistics.to_csv(output_directory / "estatisticas.csv", index=False, encoding="utf-8")
    (output_directory / "relatorio_qualidade.md").write_text(
        markdown_report(data_directory, summary, issues, statistics), encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valida a qualidade dos seis CSVs do projeto Industrial 4.0.")
    parser.add_argument("--dados", type=Path, default=Path("data/generated"), help="Diretório com os CSVs.")
    parser.add_argument("--saida", type=Path, default=Path("reports/quality"), help="Diretório dos relatórios.")
    parser.add_argument(
        "--falhar-com-aviso", action="store_true",
        help="Retorna código de erro também quando houver apenas avisos.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    _, summary, issues, statistics = validate(args.dados)
    write_reports(args.saida, args.dados, summary, issues, statistics)
    error_rules = int((issues["severity"] == "ERRO").sum()) if not issues.empty else 0
    warning_rules = int((issues["severity"] == "AVISO").sum()) if not issues.empty else 0
    print(f"Relatório: {(args.saida / 'relatorio_qualidade.md').resolve()}")
    print(f"Tabelas analisadas: {len(summary)}")
    print(f"Registros analisados: {int(summary['registros'].sum()) if not summary.empty else 0:,}")
    print(f"Regras com erro: {error_rules}")
    print(f"Regras com aviso: {warning_rules}")
    if error_rules or (args.falhar_com_aviso and warning_rules):
        sys.exit(1)


if __name__ == "__main__":
    main()
