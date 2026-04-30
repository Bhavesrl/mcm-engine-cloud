import os
import pandas as pd
from src.loader.detect_columns import detect_columns

from src.loader.load_db import load_data_from_db

# Percorso del file corrente: ...\MCM ENGINE\src\loader\load_raw.py
# Serve salire a:             ...\MCM ENGINE
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Cartella data_raw nella root del progetto
RAW_FOLDER = os.path.join(PROJECT_ROOT, "data_raw")


def load_data():
    """Ritorna df_beh, df_perf e columns.

    Usa il database PostgreSQL se RAW_DATA_SOURCE=db, altrimenti legge gli Excel.
    """
    raw_data_source = os.environ.get("RAW_DATA_SOURCE", "excel").lower()
    if raw_data_source == "db":
        return load_data_from_db()

    if not os.path.exists(RAW_FOLDER):
        raise FileNotFoundError(f"La cartella data_raw non esiste: {RAW_FOLDER}")

    files = os.listdir(RAW_FOLDER)

    file_beh = next((f for f in files if "Comportamento" in f), None)
    file_perf = next((f for f in files if "Performance" in f), None)

    if not file_beh or not file_perf:
        raise FileNotFoundError(
            f"Non trovo i file richiesti nella cartella: {RAW_FOLDER}"
        )

    df_beh = pd.read_excel(os.path.join(RAW_FOLDER, file_beh))
    df_perf = pd.read_excel(os.path.join(RAW_FOLDER, file_perf))

    columns = detect_columns(df_beh, df_perf)

    return {
        "df_beh": df_beh,
        "df_perf": df_perf,
        "columns": columns,
    }
