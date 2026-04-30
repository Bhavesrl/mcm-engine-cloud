# MCM Engine — Flask

Applicazione web per l'analisi di dati comportamentali e di performance HCP (Healthcare Professionals), con integrazione AI locale tramite Ollama.

## Stack Tecnologico

- **Backend**: Flask 3 + SQLAlchemy + Flask-Login
- **Frontend**: Tailwind CSS + Plotly.js + Lucide Icons
- **AI**: Ollama (modelli locali, ReAct agent con tool calling + SSE streaming)
- **Report**: PDF generati lato server con fpdf2
- **Database**: SQLite (locale, non versionato)

## Prerequisiti

- Python 3.10+
- [Ollama](https://ollama.com/) installato e avviato in locale
- Un modello Ollama compatibile (es. `qwen2.5:14b`, `llama3.1`, ecc.)

## Setup

```bash
# 1. Clona il repository
git clone https://github.com/TUO_USERNAME/MCM_ENGINE_FLASK.git
cd MCM_ENGINE_FLASK

# 2. Crea e attiva il virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con le tue impostazioni

# 5. Metti i tuoi file Excel in data_raw/
#    - Comportamento HCP.xlsx
#    - Performance Channel.xlsx

# 6. Avvia l'applicazione
python run.py
```

L'app sarà disponibile su `http://localhost:5001`

## Variabili d'Ambiente (.env)

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `FLASK_ENV` | `development` | Ambiente Flask |
| `FLASK_DEBUG` | `True` | Modalità debug |
| `SECRET_KEY` | *(da impostare)* | Chiave segreta sessioni |
| `DATA_RAW_PATH` | `data_raw` | Cartella dati Excel |
| `DATABASE_URL` | *(vuoto)* | URL di connessione PostgreSQL / Supabase |
| `RAW_DATA_SOURCE` | `excel` | `excel` o `db` per leggere dati raw dal DB |
| `RAW_BEH_TABLE` | `raw_comportamento` | Nome tabella raw Comportamento |
| `RAW_PERF_TABLE` | `raw_performance` | Nome tabella raw Performance |
| `ADMIN_USERNAME` | `admin` | Username admin |
| `ADMIN_PASSWORD` | `changeme` | Password admin — **cambiare!** |

## Supabase / PostgreSQL

Per utilizzare Supabase come database del progetto:

1. Crea un progetto Supabase e copia la stringa di connessione Postgres.
2. Imposta `DATABASE_URL` nel file `.env` o nelle variabili di ambiente del deployment.
3. Se vuoi leggere i dati raw direttamente dal DB, imposta `RAW_DATA_SOURCE=db`.
4. Crea o popola le tabelle raw nel database:
   - `raw_comportamento` per il dataset Comportamento
   - `raw_performance` per il dataset Performance
5. Se vuoi nomi diversi, usa `RAW_BEH_TABLE` e `RAW_PERF_TABLE`.

### Importare i file Excel in Supabase/Postgres

Usa lo script di utilità per caricare i file Excel in Postgres:

```bash
python -m src.loader.import_raw_to_db
```

Se necessario, puoi passare la connessione e i nomi delle tabelle:

```bash
DATABASE_URL="postgresql://user:password@host:5432/dbname" python -m src.loader.import_raw_to_db \
  --beh-table raw_comportamento --perf-table raw_performance
```

In modalità `RAW_DATA_SOURCE=db`, il progetto leggerà i dati raw dal database invece che da `data_raw/`.

## Struttura Progetto

```
MCM_ENGINE_FLASK/
├── run.py                  # Entry point
├── config/                 # Configurazione app
├── app/
│   ├── ai/                 # AI Agent (ReAct + tool calling)
│   ├── reports/            # Generazione PDF
│   ├── routes/             # Blueprint Flask (auth, moduli, API, AI)
│   ├── static/             # CSS, JS, immagini
│   └── templates/          # Template HTML Jinja2
├── src/
│   ├── behavior/           # KPI analisi comportamento HCP
│   ├── performance/        # KPI analisi performance vs mercato
│   └── loader/             # Caricamento e parsing dati Excel
├── data_raw/               # Dati Excel (non versionati)
├── instance/               # Database SQLite (non versionato)
└── docs/                   # Documentazione fasi di sviluppo
```

## Moduli Principali

| Modulo | Descrizione |
|--------|-------------|
| **Modulo 1 — Comportamento HCP** | Analisi KPI comportamentali, OCV mix, funnel HCP, Sankey, download Excel |
| **Modulo 2 — Performance** | Performance vs mercato, benchmark competitor, segmentazione canali |
| **Trend** | Analisi temporale KPI con export Excel |
| **AI Assistant** | Agente ReAct con tool calling su dati reali, streaming SSE |
| **Report PDF** | Generazione report PDF con grafici, pagine dark, logo |

## Avvio in Produzione

```bash
gunicorn -w 4 -b 0.0.0.0:5001 "app:create_app()"
```

## Note di Sviluppo

- `MIN_HCP = 20` — soglia campione minimo in `app/routes/modulo1.py`
- AI Agent: `MAX_STEPS=4`, `num_predict` minimo `2048` con `think=True`
- La cache dati ha TTL di 8 ore (configurabile via `CACHE_TTL_HOURS`)
- Documentazione dettagliata delle fasi in `docs/phases/`
