import os

_BASE = os.path.dirname(os.path.dirname(__file__))

class Config:
    SECRET_KEY       = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    DATA_RAW_PATH    = os.path.join(_BASE, "data_raw")
    UPLOAD_FOLDER    = os.path.join(_BASE, "data_raw")
    CACHE_TTL_HOURS  = int(os.environ.get("CACHE_TTL_HOURS", 8))
    RAW_DATA_SOURCE  = os.environ.get("RAW_DATA_SOURCE", "excel")
    RAW_BEH_TABLE    = os.environ.get("RAW_BEH_TABLE", "raw_comportamento")
    RAW_PERF_TABLE   = os.environ.get("RAW_PERF_TABLE", "raw_performance")

    # SQLite — file nella cartella instance/ (creata automaticamente da Flask)
    SQLALCHEMY_DATABASE_URI    = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(_BASE, "instance", "mcm.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Primo admin — creato automaticamente se il DB è vuoto
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")


class DevelopmentConfig(Config):
    DEBUG   = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG   = False
    TESTING = False


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
