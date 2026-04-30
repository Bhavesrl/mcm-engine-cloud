import os

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from src.loader.detect_columns import detect_columns

RAW_BEH_TABLE = os.environ.get("RAW_BEH_TABLE", "raw_comportamento")
RAW_PERF_TABLE = os.environ.get("RAW_PERF_TABLE", "raw_performance")


def _create_engine() -> Engine:
    """Restituisce l'engine SQLAlchemy collegato al DB configurato."""
    try:
        from app.models import db

        if getattr(db, "engine", None) is not None:
            return db.engine
    except Exception:
        pass

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL non impostato. Imposta la stringa di connessione Supabase/Postgres."
        )

    return create_engine(database_url, future=True)


def _table_exists(engine: Engine, table_name: str) -> bool:
    """Verifica che la tabella esista nel database corrente."""
    inspector = inspect(engine)
    return inspector.has_table(table_name)


def load_data_from_db():
    """Carica i dataset raw da tabelle PostgreSQL invece che da Excel."""
    engine = _create_engine()

    if not _table_exists(engine, RAW_BEH_TABLE):
        raise FileNotFoundError(
            f"Tabella raw non trovata: {RAW_BEH_TABLE}. Controlla RAW_BEH_TABLE e il database."
        )
    if not _table_exists(engine, RAW_PERF_TABLE):
        raise FileNotFoundError(
            f"Tabella raw non trovata: {RAW_PERF_TABLE}. Controlla RAW_PERF_TABLE e il database."
        )

    df_beh = pd.read_sql_table(RAW_BEH_TABLE, con=engine)
    df_perf = pd.read_sql_table(RAW_PERF_TABLE, con=engine)
    columns = detect_columns(df_beh, df_perf)

    return {
        "df_beh": df_beh,
        "df_perf": df_perf,
        "columns": columns,
    }
