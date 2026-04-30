"""
Import data_raw CSV files into PostgreSQL.

Requirements:
    pip install psycopg2-binary pandas

Usage:
    python sql/02_import.py --host localhost --port 5432 --db mydb --user myuser --password mypass

The script:
  1. Reads each CSV with the correct encoding and separator
  2. Renames columns to match the schema in 01_schema.sql
  3. Streams rows to PostgreSQL via COPY (fast bulk load)
"""

import argparse
import io
import re
import sys

import pandas as pd
import psycopg2


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


# Explicit mapping: sanitized auto-name  →  final schema column name
# (only the columns whose auto-name differs from what 01_schema.sql defines)
RENAME_HCP = {
    "q3_1_l_hcp_in_accordo_con_internet_la_fonte_di_aggiornamento_professionale_che_preferisco":
        "q3_1_internet_fonte_aggiornamento_preferita",
    "q3_2_l_hcp_in_accordo_con_su_internet_riesco_a_trovare_sempre_e_facilmente_tutte_le_informazioni_di_cui_ho_bisogno_per_la_mia_professione":
        "q3_2_internet_facile_trovare_informazioni",
    "q3_3_l_hcp_in_accordo_con_mi_piace_navigare_su_internet_ed_esplorarne_i_contenuti":
        "q3_3_piace_navigare_internet",
    "q3_4_l_hcp_in_accordo_con_i_siti_delle_aziende_sono_utili_in_quanto_organizzano_le_informazioni_in_maniera_chiara":
        "q3_4_siti_aziende_utili",
    "q3_5_l_hcp_in_accordo_con_non_mi_fido_dei_siti_delle_aziende":
        "q3_5_non_mi_fido_siti_aziende",
    "q3_6_l_hcp_in_accordo_con_preferisco_il_contatto_diretto_con_l_informatore_farmaceutico":
        "q3_6_preferisco_contatto_diretto_isf",
    "q3_7_l_hcp_in_accordo_con_non_ritengo_i_social_media_lo_strumento_adatto_al_mio_aggiornamento_professionale":
        "q3_7_social_media_non_adatti_aggiornamento",
    "q3_8_l_hcp_in_accordo_con_sono_favorevole_ai_colloqui_telefonici_con_l_isf":
        "q3_8_favorevole_colloqui_telefonici_isf",
    "q3_9_l_hcp_in_accordo_con_i_social_media_sono_utili_solo_per_lo_scambio_di_poche_informazioni_veloci":
        "q3_9_social_media_utili_solo_info_veloci",
    "q3_10_l_hcp_in_accordo_con_sono_favorevole_al_collegamento_via_web_on_line_con_l_isf":
        "q3_10_favorevole_collegamento_web_isf",
    "q3_11_l_hcp_in_accordo_con_ritengo_che_i_canali_digitali_siano_efficaci_solo_se_affiancati_dall_informazione_diretta_da_parte_dell_isf":
        "q3_11_canali_digitali_efficaci_se_affiancati_isf",
    "q3_12_l_hcp_in_accordo_con_navigare_su_internet_solo_una_perdita_di_tempo":
        "q3_12_internet_perdita_di_tempo",
    "q3_13_l_hcp_in_accordo_con_l_introduzione_dei_nuovi_canali_digitali_di_informazione_medico_scientifica_ha_contribuito_a_migliorare_la_mia_modalit_di_aggiornamento":
        "q3_13_canali_digitali_migliorano_aggiornamento",
    "q4_1_hcp_possiede_un_profilo_su_social_network":
        "q4_1_hcp_possiede_profilo_social_network",
    "q4a_1_rivevuto_info_su_sn":
        "q4a_1_ricevuto_info_su_sn",
    "q5_1_quanto_tempo_decica_al_canale_ricevuto_via_posta":
        "q5_1_tempo_canale_posta",
    "q5_2_quanto_tempo_decica_al_canale_ftof":
        "q5_2_tempo_canale_ftof",
    "q5_3_quanto_t_al_gg":    "q5_3_tempo_canale",
    "q5_4quanto_t_al_gg":     "q5_4_tempo_canale",
    "q5_5_quanto_t_al_gg":    "q5_5_tempo_canale",
    "q5_6_quanto_t_al_gg":    "q5_6_tempo_canale",
    "q5_7_quanto_t_al_gg":    "q5_7_tempo_canale",
    "q5_8_quanto_t_al_gg":    "q5_8_tempo_canale",
    "q5_9_quanto_t_al_gg":    "q5_9_tempo_canale",
    "q5_10_quanto_t_al_gg":   "q5_10_tempo_canale",
    "q5_11_quanto_t_al_gg":   "q5_11_tempo_canale",
    "q5_12_quanto_t_al_gg":   "q5_12_tempo_canale",
    "q5_13_quanto_t_al_gg":   "q5_13_tempo_canale",
    "q5_14_quanto_t_al_gg":   "q5_14_tempo_canale",
    "q5_15_quanto_t_al_gg":   "q5_15_tempo_canale",
    "q5_16_quanto_t_al_gg":   "q5_16_tempo_canale",
    "q5_17_quanto_t_al_gg":   "q5_17_tempo_canale",
    "q5_18_quanto_t_al_gg":   "q5_18_tempo_canale",
    "q5_19_quanto_t_al_gg":   "q5_19_tempo_canale",
    "q5_20_quanto_t_al_gg":   "q5_20_tempo_canale",
    "q6_1_utilia_opuscoli":   "q6_1_utilita_opuscoli",
    "q6_2_utilita_ftof":      "q6_2_utilita_ftof",
    "q6_5_utilita_email_da_isf":           "q6_5_utilita_email_da_isf",
    "q6_6_utilita_siti_portali_di_aziende_con_login": "q6_6_utilita_siti_portali_aziende_con_login",
    "q6_7_utilita_pubblicit_cartacee":     "q6_7_utilita_pubblicita_cartacee",
    "q6_9_utilita_sms_mobile":             "q6_9_utilita_sms_mobile",
    "q6_10_utilita_e_mail_aziendali":      "q6_10_utilita_email_aziendali",
    "q6_11_utilita_newsletter_e_mail":     "q6_11_utilita_newsletter_email",
    "q7a_area_terapeutica_di_cui_occupa_pi_frequentemente_hcp": "q7a_area_terapeutica_principale",
    "q7b_1_patologia_di_cui_si_occupa_pi_frequentemente_l_hcp": "q7b_1_patologia_principale",
    "q11a_1_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_opuscoli_ricevuti_via_posta": "q11a_1_ricevuto_opuscoli_posta",
    "q11a_2_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_isf_faccia_a_faccia": "q11a_2_ricevuto_isf_ftof",
    "q11a_3_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_isf_telefonica": "q11a_3_ricevuto_isf_telefonica",
    "q11a_4_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_isf_via_webcall": "q11a_4_ricevuto_isf_webcall",
    "q11a_5_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_email_da_isf": "q11a_5_ricevuto_email_isf",
    "q11a_6_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_portali_aziendali_con_login": "q11a_6_ricevuto_portali_aziendali",
    "q11a_7_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_adv_riviste_cartacee": "q11a_7_ricevuto_adv_riviste_cartacee",
    "q11a_8_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_articoli_su_riviste_cartacee": "q11a_8_ricevuto_articoli_riviste_cartacee",
    "q11a_9_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_sms_mobile": "q11a_9_ricevuto_sms_mobile",
    "q11a_10_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_e_mail_aziendali": "q11a_10_ricevuto_email_aziendali",
    "q11a_11_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_newsletter_inviate_e_mail": "q11a_11_ricevuto_newsletter_email",
    "q11a_12_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_product_website": "q11a_12_ricevuto_product_website",
    "q11a_13_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_articoli_su_riviste_digitali": "q11a_13_ricevuto_articoli_riviste_digitali",
    "q11a_14_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_social_network": "q11a_14_ricevuto_social_network",
    "q11a_15_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_mess_da_app_tematiche": "q11a_15_ricevuto_app_tematiche",
    "q11a_16_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_app_messaggistica_mobile": "q11a_16_ricevuto_app_messaggistica",
    "q11a_17_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_webinar": "q11a_17_ricevuto_webinar",
    "q11a_18_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_fad_online": "q11a_18_ricevuto_fad_online",
    "q11a_19_hcp_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_congressi_naz_con_ecm": "q11a_19_ricevuto_congressi_naz_ecm",
    "q11a_20_ha_ricevuto_negli_ultimi_7_gg_info_attraverso_congressi_int_con_ecm": "q11a_20_ricevuto_congressi_int_ecm",
    "q11a_1_numerosita_di_opuscoli_ricevuti_via_posta": "q11a_1_num_opuscoli_posta",
    "q11a_2_numerosita_di_isf_faccia_a_faccia": "q11a_2_num_isf_ftof",
    "q11a_3_isf_telefonica":    "q11a_3_num_isf_telefonica",
    "q11a_4_isf_via_webcall":   "q11a_4_num_isf_webcall",
    "q11a_5_email_da_isf":      "q11a_5_num_email_isf",
    "q11a_6_portali_aziendali_con_login": "q11a_6_num_portali_aziendali",
    "q11a_7_adv_riviste_cartacee": "q11a_7_num_adv_riviste_cartacee",
    "q11a_8_articoli_su_riviste_cartacee": "q11a_8_num_articoli_riviste_cartacee",
    "q11a_9_sms_mobile":        "q11a_9_num_sms_mobile",
    "q11a_10_e_mail_aziendali": "q11a_10_num_email_aziendali",
    "q11a_11_newsletter_inviate_e_mail": "q11a_11_num_newsletter_email",
    "q11a_12_product_website":  "q11a_12_num_product_website",
    "q11a_13_articoli_su_riviste_digitali": "q11a_13_num_articoli_riviste_digitali",
    "q11a_14_social_network":   "q11a_14_num_social_network",
    "q11a_15_mess_da_app_tematiche": "q11a_15_num_app_tematiche",
    "q11a_16_app_messaggistica_mobile": "q11a_16_num_app_messaggistica",
    "q11a_17_webinar":          "q11a_17_num_webinar",
    "q11a_18_fad_online":       "q11a_18_num_fad_online",
    "q11a_19_congressi_naz_con_ecm": "q11a_19_num_congressi_naz_ecm",
    "q11a_20_congressi_int_con_ecm": "q11a_20_num_congressi_int_ecm",
    "q17_1_questa_azienda_ha_una_comunicazione_aperta_e_trasparente": "q17_1_azienda_comunicazione_aperta",
    "q17_2_questa_azienda_un_valido_partner_per_me": "q17_2_azienda_valido_partner",
    "q17_3_questa_azienda_comprende_le_mie_necessit_professionali": "q17_3_azienda_comprende_necessita",
    "q17_4_i_prodotti_di_questa_azienda_impattano_positivamente_sulla_salute_dei_miei_pazienti": "q17_4_prodotti_impattano_positivamente",
    "q17_5_questa_azienda_fornisce_informazioni_sui_loro_prodotti_e_servizi_utili_e_aggiornate": "q17_5_azienda_fornisce_info_utili",
    "q17_6_questa_azienda_fornisce_tutte_le_informazioni_di_cui_ho_bisogno": "q17_6_azienda_fornisce_tutte_info",
    "q17_7_questa_azienda_fornisce_buoni_clinical_data_per_supportare_l_uso_dei_loro_prodotti": "q17_7_azienda_fornisce_clinical_data",
    "q17_8_questa_azienda_usa_una_combinazione_di_canali_di_comunicazione_che_incontra_i_miei_bisogni_es_visita_isf_congressi_canali_online": "q17_8_azienda_usa_combinazione_canali",
    "q18_1_annodilaurea":       "q18_1_anno_laurea",
    "q21a_1_datadinascita":     "q21a_1_anno_nascita",
    "tipologia_di_attivit_prevalente": "tipologia_attivita_prevalente",
    "tipo_di_specializzazione_primary_or_secondary_care": "tipo_specializzazione_primary_secondary_care",
}

RENAME_PC = {
    "s1_sprcializzazione_del_medico": "s1_specializzazione_medico",
    "q9_1_opuscoli_ricevuti_via_posta": "q9_1_opuscoli_posta",
    "q9_2_isf_faccia_a_faccia":         "q9_2_isf_ftof",
    "q9_5_email_da_isf":                "q9_5_email_isf",
    "q9_6_portali_aziendali_con_login": "q9_6_portali_aziendali",
    "q9_7_adv_riviste_cartacee":        "q9_7_adv_riviste_cartacee",
    "q9_8_articoli_su_riviste_cartacee":"q9_8_articoli_riviste_cartacee",
    "q9_9_sms_mobile":                  "q9_9_sms_mobile",
    "q9_10_e_mail_aziendali":           "q9_10_email_aziendali",
    "q9_11_newsletter_e_mail":          "q9_11_newsletter_email",
    "q9_13_articoli_su_riviste_digitali":"q9_13_articoli_riviste_digitali",
    "q9_15_da_app_tematiche":           "q9_15_app_tematiche",
    "q9_16_app_mess_mobile":            "q9_16_app_mess_mobile",
    "q9_19_congressi_naz_con_ecm":      "q9_19_congressi_naz_ecm",
    "q9_20_congressi_int_con_ecm":      "q9_20_congressi_int_ecm",
    "q13_1_le_informazioni_erano_rilevanti": "q13_1_informazioni_rilevanti",
    "q16_probabilita_di_consiglio":     "q16_probabilita_consiglio",
    "q18_1_anno_laurea":                "q18_1_anno_laurea",
    "q21a_1_anno_nascita":              "q21a_1_anno_nascita",
    "unnamed_79":                       None,  # drop this column
}


# ------------------------------------------------------------------ core

def load_and_rename(path: str, rename_map: dict, drop_unnamed: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", low_memory=False, encoding="utf-8-sig")
    df.columns = deduplicate_cols(list(df.columns))
    df.rename(columns={k: v for k, v in rename_map.items() if v is not None}, inplace=True)
    # Drop columns mapped to None
    drop_cols = [k for k, v in rename_map.items() if v is None and k in df.columns]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")
    return df


def copy_df_to_pg(conn, df: pd.DataFrame, table: str) -> int:
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {table} FROM STDIN WITH (FORMAT csv, NULL '\\N')",
            buf,
        )
    return len(df)


def main():
    parser = argparse.ArgumentParser(description="Import MCM Engine CSVs into PostgreSQL")
    parser.add_argument("--host",     default="localhost")
    parser.add_argument("--port",     default=5432, type=int)
    parser.add_argument("--db",       required=True, help="Database name")
    parser.add_argument("--user",     required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--schema-only", action="store_true",
                        help="Create tables then exit (no data load)")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=args.host, port=args.port,
        dbname=args.db, user=args.user, password=args.password,
    )
    conn.autocommit = False

    schema_sql = open("sql/01_schema.sql", encoding="utf-8").read()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    print("Tables created (or already exist).")

    if args.schema_only:
        conn.close()
        return

    jobs = [
        ("data_raw/Comportamento HCP.csv",   RENAME_HCP, "comportamento_hcp"),
        ("data_raw/Performance Channel.csv",  RENAME_PC,  "performance_channel"),
    ]

    for path, rename, table in jobs:
        print(f"Loading {path} → {table} ...", flush=True)
        df = load_and_rename(path, rename)
        n = copy_df_to_pg(conn, df, table)
        conn.commit()
        print(f"  {n:,} rows inserted into {table}.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
