"""
Genera CSV puliti con nomi colonna allineati allo schema PostgreSQL.
I file vengono salvati in data_clean/ pronti per l'import via pgAdmin o psql COPY.

Uso:
    python sql/03_export_clean_csv.py
"""

import re
import pathlib
import pandas as pd
import importlib.util

# ------------------------------------------------------------------ helpers

def sanitize(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_").lower()
    if name and name[0].isdigit():
        name = "col_" + name
    return name


def deduplicate_cols(raw_cols):
    seen: dict[str, int] = {}
    result = []
    for c in raw_cols:
        s = sanitize(c)
        if s in seen:
            seen[s] += 1
            s = f"{s}_{seen[s]}"
        else:
            seen[s] = 0
        result.append(s)
    return result


# Carica le rename map dal file di import
spec = importlib.util.spec_from_file_location("imp", "sql/02_import.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RENAME_HCP = mod.RENAME_HCP
RENAME_PC  = mod.RENAME_PC

# ------------------------------------------------------------------ main

def export(src_path: str, rename_map: dict, out_path: str):
    print(f"Lettura {src_path} ...", flush=True)
    df = pd.read_csv(src_path, sep=";", low_memory=False, encoding="utf-8-sig")

    # Rinomina colonne con sanitize + rename map
    df.columns = deduplicate_cols(list(df.columns))
    df.rename(columns={k: v for k, v in rename_map.items() if v is not None}, inplace=True)

    # Rimuovi colonne mappate a None (unnamed trailing)
    drop_cols = [k for k, v in rename_map.items() if v is None and k in df.columns]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")

    # Scrivi CSV pulito (virgola come separatore, encoding UTF-8 con BOM per compatibilità)
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  -> {out_path}  ({len(df):,} righe, {len(df.columns)} colonne)")


export(
    "data_raw/Comportamento HCP.csv",
    RENAME_HCP,
    "data_clean/comportamento_hcp.csv",
)

export(
    "data_raw/Performance Channel.csv",
    RENAME_PC,
    "data_clean/performance_channel.csv",
)

print("\nDone. Ora importa i file da data_clean/ tramite pgAdmin:")
print("  Tasto destro sulla tabella > Import/Export Data")
print("  Format: csv | Delimiter: , | Header: ON | Encoding: UTF8")
