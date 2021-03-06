import os

PRIVATE_KEY = None
DB_SERVER = os.getenv("DB_PORT_3306_TCP_ADDR", "localhost")
DB_PORT = int(os.getenv("DB_PORT_3306_TCP_PORT", "3306"))
DB_LOGIN = os.getenv("FAF_DB_LOGIN", "root")
DB_PASSWORD = os.getenv("FAF_DB_PASSWORD", "banana")
DB_NAME = os.getenv("FAF_DB_NAME", "faf_test")

CHALLONGE_KEY = "challonge_key"
CHALLONGE_USER = "challonge_user"

VERIFICATION_SECRET_KEY = "IT'S STILL TOASTER TIME"
VERIFICATION_HASH_SECRET = "IT'S TOASTER TIME"

API_CLIENT_ID = os.getenv("API_CLIENT_ID", "6ccaf75b-a1f3-48be-bac3-4e9ffba81eb7")
API_CLIENT_SECRET = os.getenv("API_CLIENT_SECRET", "banana")
API_TOKEN_URI = os.getenv("API_TOKEN_URI", "http://api.dev.faforever.com/jwt/auth")
API_BASE_URL = os.getenv("API_BASE_URL", "http://api.dev.faforever.com/jwt")
