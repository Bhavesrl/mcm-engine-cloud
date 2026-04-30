import os
import argparse

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.sql.sqltypes import TIMESTAMP

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_FOLDER = os.path.join(PROJECT_ROOT, "data_raw")

# Carica variabili d'ambiente da .env se presente
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _find_file(keyword: str) -> str:
    for name in os.listdir(RAW_FOLDER):
        if keyword.lower() in name.lower():
            return os.path.join(RAW_FOLDER, name)
    raise FileNotFoundError(f"Non trovato il file Excel per '{keyword}' in {RAW_FOLDER}")


def _sqlalchemy_type_for_series(series: pd.Series):
    dtype = series.dtype

    if pd.api.types.is_bool_dtype(dtype):
        return Boolean()
    if pd.api.types.is_integer_dtype(dtype):
        return Integer()
    if pd.api.types.is_float_dtype(dtype):
        return Float(precision=53)
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return TIMESTAMP(timezone=False)
    if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
        # Per colonne testuali molto lunghe usiamo TEXT in Postgres
        return Text()

    return Text()


def _infer_table_dtypes(df: pd.DataFrame) -> dict[str, object]:
    dtypes = {}
    for col in df.columns:
        dtypes[col] = _sqlalchemy_type_for_series(df[col])
    return dtypes


def _write_table(engine, df: pd.DataFrame, table_name: str) -> None:
    print(f"Creazione della tabella: {table_name}")
    dtypes = _infer_table_dtypes(df)
    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False,
        dtype=dtypes,
        method="multi",
        chunksize=1000,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa i file Excel raw in un database PostgreSQL/Supabase con schema corretto."
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="Stringa di connessione Postgres/Supabase. Può anche essere impostata in DATABASE_URL.",
    )
    parser.add_argument(
        "--beh-table",
        default=os.environ.get("RAW_BEH_TABLE", "raw_comportamento"),
        help="Nome tabella per i dati Comportamento.",
    )
    parser.add_argument(
        "--perf-table",
        default=os.environ.get("RAW_PERF_TABLE", "raw_performance"),
        help="Nome tabella per i dati Performance.",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise RuntimeError("DATABASE_URL non impostato. Passalo con --database-url o tramite env.")

    if not os.path.isdir(RAW_FOLDER):
        raise FileNotFoundError(f"Cartella data_raw non trovata: {RAW_FOLDER}")

    beh_path = _find_file("comportamento")
    perf_path = _find_file("performance")

    print(f"Carico Excel: {beh_path}")
    print(f"Carico Excel: {perf_path}")

    df_beh = pd.read_excel(beh_path)
    df_perf = pd.read_excel(perf_path)

    engine = create_engine(args.database_url, future=True)

    _write_table(engine, df_beh, args.beh_table)
    _write_table(engine, df_perf, args.perf_table)

    print("Import e migrazione completati")
    print(f"- {len(df_beh)} righe scritte in {args.beh_table}")
    print(f"- {len(df_perf)} righe scritte in {args.perf_table}")


if __name__ == "__main__":
    main()
