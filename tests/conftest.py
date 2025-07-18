import json
from pathlib import Path

import pandas as pd
import pytest
from pandas import DataFrame


@pytest.fixture
def sample_df() -> DataFrame:
    """Тестовый DataFrame с транзакциями"""
    data = {
        "Дата операции": ["01.05.2025 12:00:00", "10.05.2025 14:00:00", "01.04.2025 12:00:00"],
        "Номер карты": ["****1234", None, "****5678"],
        "Сумма платежа": [-150.0, -200.0, -300.0],
        "Категория": ["Продукты", "Переводы", "Каршеринг"],
        "Описание": ["Покупка в магазине", "Иван И.", "Аренда авто"],
        "Дата платежа": ["01.05.2025 12:00:00", "10.05.2025 14:00:00", "01.04.2025 12:00:00"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_excel_file(tmp_path: Path, sample_df: DataFrame) -> str:
    """Сохраняет sample_df в Excel и возвращает путь"""
    excel_path = tmp_path / "test.xlsx"
    sample_df.to_excel(excel_path, index=False)
    return str(excel_path)


@pytest.fixture
def sample_json_file(tmp_path: Path) -> str:
    """Создает JSON-файл с пользовательскими настройками и возвращает путь"""
    json_path = tmp_path / "user_settings.json"
    data = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return str(json_path)
