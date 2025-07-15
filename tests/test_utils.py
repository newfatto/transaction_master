import pytest
import pandas as pd
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch
import os

from src.utils import excel_to_list


# Тесты для функции excel_to_list

@pytest.fixture
def sample_excel_data():
    """
    Fixture для создания временного Excel-файла с тестовыми данными.
    """
    data = {
        "Дата операции": [
            "15.05.2025 10:00:00",
            "20.05.2025 12:00:00",
            "05.06.2025 14:00:00",
            "01.05.2025 08:00:00",
            "21.05.2025 16:00:00",
        ],
        "Сумма": [100, 200, 300, 50, 250],
        "Описание": ["Покупка", "Продажа", "Покупка", "Покупка", "Продажа"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    return df

@pytest.fixture
def sample_excel_data():
    """
    Fixture для создания временного Excel-файла с тестовыми данными.
    """
    data = {
        "Дата операции": [
            "15.05.2025 10:00:00",
            "20.05.2025 12:00:00",
            "05.06.2025 14:00:00",
            "01.05.2025 08:00:00",
            "21.05.2025 16:00:00",
        ],
        "Сумма": [100, 200, 300, 50, 250],
        "Описание": ["Покупка", "Продажа", "Покупка", "Покупка", "Продажа"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    return df

@pytest.fixture
def sample_excel_file(sample_excel_data, tmpdir):
    """
    Fixture для создания временного Excel-файла и возврата его пути.
    """
    excel_path = os.path.join(tmpdir.strpath, "test_data.xlsx")
    sample_excel_data.to_excel(excel_path, index=False)
    return excel_path

@pytest.mark.parametrize(
    "date_str, expected_rows",
    [
        ("2025-05-20 12:00:00", 2),  # Данные за май до 20-го
        ("2025-05-01 08:00:00", 1),  # Только первая операция
        ("2025-06-01 00:00:00", 0),  # Нет данных в мае
        ("2025-05-31 23:59:59", 3), # Все данные за май
    ],
)

def test_excel_to_list_success_parametrized(sample_excel_file, sample_excel_data, date_str, expected_rows):
    """
    Параметризованный тест успешного выполнения функции.
    Проверяет разные сценарии с разными датами.
    """
    result_df = excel_to_list(sample_excel_file, date_str)
    assert len(result_df) == expected_rows


