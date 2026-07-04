import os
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Ajay@0412"
MYSQL_DB = "ev_charging_db"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ev_charging_secret_key_2026")

    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Ajay@0412")
    MYSQL_DB = os.environ.get("MYSQL_DB", "ev_charging_db")
    MYSQL_CURSORCLASS = "DictCursor"

    APP_NAME = "EV Charging Monitoring & Billing System"
    DEFAULT_PRICE_PER_UNIT = 12.00