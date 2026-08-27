# config.py
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

URL_BASE = "https://www.autocosmos.com.ar/auto/usado"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
 
TEST_SIZE = 0.2
RANDOM_STATE = 42

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "autos_autocosmos.csv"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "autos_dolarizado.csv"
CLEAN_DATA_PATH = BASE_DIR / "data" / "processed" / "clean_data.csv"
ENCODED_DATA_PATH = BASE_DIR / "data" / "processed" / "df_encoded.csv"
MODEL_PATH = BASE_DIR / "model.pkl"
MIDPOINT_DATA_PATH = BASE_DIR / "data" / "processed" / "df_mid"
