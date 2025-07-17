from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXCEL_FILE_PATH = BASE_DIR / "data" / "operations.xlsx"

EXCEL_FILE_PATH_STR = str(EXCEL_FILE_PATH)

USER_SETTINGS_PATH = BASE_DIR / "user_settings.json"

USER_SETTINGS_PATH_STR = str(USER_SETTINGS_PATH)
