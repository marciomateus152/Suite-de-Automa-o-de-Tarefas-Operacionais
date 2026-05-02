#!/usr/bin/env python3
"""
bulk_data_formatter.py - Formatador de Dados em Massa
Pipeline de padronização: datas, telefones, emails e nomes.
Detecta e reporta linhas corrompidas ou inconsistentes.
"""

import logging
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import pandas as pd

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "bulk_data_formatter.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Expressões regulares de validação
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_BR_RE = re.compile(r"[\d]")  # usado para extrair apenas dígitos
DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
    "%d.%m.%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y",
]

# ---------------------------------------------------------------------------
# Funções de normalização individuais
# ---------------------------------------------------------------------------


def normalize_name(value: str) -> str:
    """Title case, remove espaços extras e caracteres não alfabéticos extras."""
    if not isinstance(value, str) or not value.strip():
        return ""
    cleaned = re.sub(r"[^a-zA-ZÀ-ÿ\s\-\']", "", value)
    return " ".join(w.capitalize() for w in cleaned.split())


def normalize_email(value: str) -> str:
    """Lowercase e strip; retorna vazio se inválido."""
    if not isinstance(value, str):
        return ""
    v = value.strip().lower()
    return v if EMAIL_RE.match(v) else ""


def normalize_phone(value: str) -> str:
    """
    Extrai dígitos e formata como telefone brasileiro.
    Celular: (XX) 9XXXX-XXXX  |  Fixo: (XX) XXXX-XXXX
    """
    if not isinstance(value, str):
        return ""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"
    return value.strip()


def normalize_date(value: str, output_format: str = "%d/%m/%Y") -> str:
    """
    Tenta parsear a data em múltiplos formatos e normaliza para output_format.
    Retorna string vazia se nenhum formato encaixar.
    """
    if not isinstance(value, str) or not value.strip():
        return ""
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(value.strip(), format=fmt).strftime(output_format)
        except (ValueError, TypeError):
            continue
    # Tentativa liberal com pandas
    try:
        return pd.to_datetime(value.strip(), dayfirst=True).strftime(output_format)
    except (ValueError, TypeError):
        return ""


def is_corrupted_row(row: pd.Series, required_cols: list[str]) -> bool:
    """Retorna True se todas as colunas obrigatórias estiverem nulas/vazias."""
    return all(
        pd.isna(row.get(col)) or str(row.get(col, "")).strip() == ""
        for col in required_cols
    )


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def format_dataframe(
    df: pd.DataFrame,
    col_map: dict[str, str],
    required_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Executa o pipeline de formatação sobre o DataFrame.

    Args:
        df: DataFrame bruto.
        col_map: Mapeamento {nome_coluna: tipo} onde tipo é
                 'name' | 'email' | 'phone' | 'date'.
        required_cols: Colunas cuja ausência total indica linha corrompida.

    Returns:
        Tupla (df_clean, df_corrupted, metrics).
    """
    required_cols = required_cols or list(col_map.keys())
    metrics: dict[str, int] = {
        "total_rows": len(df),
        "corrupted_rows": 0,
        "fixed_names": 0,
        "fixed_emails": 0,
        "fixed_phones": 0,
        "fixed_dates": 0,
        "invalid_emails": 0,
    }

    corrupted_mask = df.apply(is_corrupted_row, axis=1, required_cols=required_cols)
    df_corrupted = df[corrupted_mask].copy()
    df_clean = df[~corrupted_mask].copy()
    metrics["corrupted_rows"] = int(corrupted_mask.sum())
    logger.info("Linhas corrompidas identificadas: %d", metrics["corrupted_rows"])

    formatters = {
        "name": normalize_name,
        "email": normalize_email,
        "phone": normalize_phone,
        "date": normalize_date,
    }
    counter_keys = {
        "name": "fixed_names",
        "email": "fixed_emails",
        "phone": "fixed_phones",
        "date": "fixed_dates",
    }

    for col, col_type in col_map.items():
        if col not in df_clean.columns:
            logger.warning("Coluna '%s' não encontrada no DataFrame.", col)
            continue
        fn = formatters.get(col_type)
        if fn is None:
            logger.warning("Tipo desconhecido '%s' para coluna '%s'.", col_type, col)
            continue

        original = df_clean[col].copy()
        df_clean[col] = df_clean[col].fillna("").astype(str).apply(fn)
        changed = (df_clean[col] != original.fillna("").astype(str)).sum()
        metrics[counter_keys[col_type]] += int(changed)
        logger.info("Coluna '%s' (%s): %d registros padronizados.", col, col_type, changed)

    # Marca emails que ficaram vazios após normalização (eram inválidos)
    if "email" in col_map:
        invalid_count = int((df_clean.get("email", pd.Series(dtype=str)) == "").sum())
        metrics["invalid_emails"] = invalid_count
        if invalid_count:
            logger.warning("Emails inválidos (campo zerado): %d", invalid_count)

    metrics["clean_rows"] = len(df_clean)
    return df_clean, df_corrupted, metrics


# ---------------------------------------------------------------------------
# Geração de relatório de inconsistências
# ---------------------------------------------------------------------------


def save_inconsistency_report(df_corrupted: pd.DataFrame, output_dir: Path) -> None:
    """Salva as linhas corrompidas em CSV para análise posterior."""
    if df_corrupted.empty:
        logger.info("Nenhuma inconsistência para reportar.")
        return
    report_path = output_dir / "inconsistency_report.csv"
    df_corrupted.to_csv(report_path, index=True, sep=";", encoding="utf-8-sig")
    logger.info("Relatório de inconsistências salvo: %s (%d linhas)", report_path, len(df_corrupted))


def print_metrics(metrics: dict, elapsed: float, output_path: Path) -> None:
    sep = "=" * 55
    print(f"\n{sep}")
    print("  RELATÓRIO DE FORMATAÇÃO EM MASSA")
    print(sep)
    print(f"  Total de registros        : {metrics['total_rows']}")
    print(f"  Linhas corrompidas        : {metrics['corrupted_rows']}")
    print(f"  Linhas processadas        : {metrics['clean_rows']}")
    print(f"  Nomes padronizados        : {metrics['fixed_names']}")
    print(f"  Emails padronizados       : {metrics['fixed_emails']}")
    print(f"  Emails inválidos (zerados): {metrics['invalid_emails']}")
    print(f"  Telefones padronizados    : {metrics['fixed_phones']}")
    print(f"  Datas padronizadas        : {metrics['fixed_dates']}")
    print(f"  Tempo de processamento    : {elapsed:.3f}s")
    print(f"\n  Arquivo limpo exportado   : {output_path}")
    print(sep)


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse
    import json

    base = Path(__file__).parent.parent

    parser = argparse.ArgumentParser(
        description="Pipeline de formatação e padronização de dados em massa."
    )
    parser.add_argument(
        "--input",
        default=str(base / "input" / "raw_data.csv"),
        help="Arquivo CSV de entrada",
    )
    parser.add_argument(
        "--output-dir",
        default=str(base / "output"),
        help="Diretório de saída",
    )
    parser.add_argument(
        "--col-map",
        default='{"nome":"name","email":"email","telefone":"phone","data_nascimento":"date"}',
        help='JSON mapeando colunas para tipos: name|email|phone|date',
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Codificação do arquivo de entrada",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.critical("Arquivo de entrada não encontrado: %s", input_path)
        sys.exit(1)

    try:
        col_map = json.loads(args.col_map)
    except json.JSONDecodeError as exc:
        logger.critical("--col-map inválido: %s", exc)
        sys.exit(1)

    start = time.perf_counter()
    logger.info("Carregando: %s", input_path)

    try:
        df = pd.read_csv(input_path, encoding=args.encoding, dtype=str)
        logger.info("Registros carregados: %d", len(df))

        df_clean, df_corrupted, metrics = format_dataframe(df, col_map)

        output_path = output_dir / f"formatted_{input_path.stem}.csv"
        df_clean.to_csv(output_path, index=False, sep=";", encoding="utf-8-sig")
        save_inconsistency_report(df_corrupted, output_dir)

        elapsed = time.perf_counter() - start
        print_metrics(metrics, elapsed, output_path)
        logger.info("Pipeline concluído em %.3fs.", elapsed)

    except (pd.errors.ParserError, OSError) as exc:
        logger.critical("Falha ao processar arquivo: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
