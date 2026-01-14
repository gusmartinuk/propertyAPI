import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app_password@db:5432/ppd_db",
)
ENV = os.getenv("ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
MIN_GROUP_COUNT = int(os.getenv("MIN_GROUP_COUNT", "2"))
MAX_DATE_RANGE_YEARS = int(os.getenv("MAX_DATE_RANGE_YEARS", "10"))
DEFAULT_NO_LOCATION_MONTHS = int(os.getenv("DEFAULT_NO_LOCATION_MONTHS", "12"))
CACHE_MAX_AGE = int(os.getenv("CACHE_MAX_AGE", "300"))
CACHE_MAX_AGE_SUMMARY = int(os.getenv("CACHE_MAX_AGE_SUMMARY", "900"))
RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET") or None
