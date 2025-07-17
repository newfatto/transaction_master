import pytest
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from src.utils import excel_to_df, transactions_since_first_day_of_month, user_greeting


# Тесты для функции excel_to_df

def test_excel_to_df_valid(sample_excel_file, sample_df):
    """
    Проверяет, что функция excel_to_df корректно читает Excel-файл.
    """
    from src.utils import excel_to_df
    df = excel_to_df(sample_excel_file)
    # Приводим все None к np.nan для корректного сравнения
    df = df.where(pd.notnull(df), None)
    sample_df = sample_df.where(pd.notnull(sample_df), None)
    pd.testing.assert_frame_equal(df, sample_df, check_dtype=False)

@pytest.mark.parametrize("invalid_path", [
    "non_existing_file.xlsx",
    "some_text_file.txt",
])
def test_excel_to_df_invalid_path(invalid_path) -> None:
    """Тест с использованием временного файла с некорректным форматом"""
    with pytest.raises(ValueError) as excinfo:
        excel_to_df(invalid_path)
    assert "Файл не найден" in str(excinfo.value) or "Ошибка при чтении" in str(excinfo.value)


def test_excel_to_df_wrong_format_file(tmp_path) -> None:
    """Создаёт .txt-файл с текстом и пытается прочитать его как Excel"""
    txt_file = tmp_path / "not_excel.txt"
    txt_file.write_text("это не Excel")

    with pytest.raises(ValueError) as excinfo:
        excel_to_df(str(txt_file))
    assert "Ошибка при чтении" in str(excinfo.value)


# Тесты для функции transactions_since_first_day_of_month

@pytest.mark.parametrize("date_str, expected_len", [
    ("2025-05-15 00:00:00", 2),
    ("2025-04-02 00:00:00", 1),
])
def test_transactions_in_current_month(
    sample_df: DataFrame, date_str: str, expected_len: int
) -> None:
    """
    Проверяет, что функция корректно фильтрует транзакции с начала месяца до указанной даты.
    """
    result = transactions_since_first_day_of_month(sample_df.copy(), date_str)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == expected_len


def test_transactions_missing_column() -> None:
    """
    Проверяет, что функция выбрасывает исключение, если в DataFrame нет нужной колонки.
    """
    df = pd.DataFrame({
        "Дата": ["01.05.2025 12:00:00"],
        "Сумма платежа": [-100]
    })
    with pytest.raises(ValueError, match="Ожидается колонка 'Дата операции'"):
        transactions_since_first_day_of_month(df, "2025-05-10 00:00:00")


def test_transactions_invalid_date_format_in_df() -> None:
    """
    Проверяет, что некорректные значения в колонке 'Дата операции' игнорируются,
    и возвращается пустой DataFrame.
    """
    df = pd.DataFrame({
        "Дата операции": ["не дата", "1234"],
        "Сумма платежа": [-100, -200]
    })
    result = transactions_since_first_day_of_month(df, "2025-05-10 00:00:00")
    assert result.empty


def test_transactions_invalid_input_date_format(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция выбрасывает исключение при некорректной входной дате.
    """
    with pytest.raises(ValueError, match="Неверный формат входной даты"):
        transactions_since_first_day_of_month(sample_df, "15.05.2025")

# Тесты для функции user_greeting


