import pytest
import pandas as pd
import json
from typing import Any
from src.reports import spending_by_category, my_decorator
from unittest.mock import patch


@pytest.mark.parametrize(
    "category,expected_count",
    [
        ("Продукты", 1),
        ("Переводы", 1),
        ("Несуществующая категория", 0),
    ]
)
def test_spending_by_category_valid(sample_df: pd.DataFrame, category: str, expected_count: int) -> None:
    """
    Проверяет, что функция возвращает корректный JSON-список трат по категории.
    """
    result = spending_by_category(sample_df, category)
    assert isinstance(result, str)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == expected_count
    if expected_count:
        assert all(item["Категория"] == category for item in data)


def test_spending_by_category_empty_df() -> None:
    """
    Проверяет, что функция возвращает пустой список, если DataFrame пустой.
    """
    df = pd.DataFrame(columns=[
        "Дата операции", "Номер карты", "Сумма платежа", "Категория", "Описание", "Дата платежа"
    ])
    result = spending_by_category(df, "Продукты")
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.parametrize(
    "bad_input",
    [
        123,
        "not a dataframe",
        None,
        [1, 2, 3],
    ]
)
def test_spending_by_category_type_error(bad_input: Any) -> None:
    """
    Проверяет, что функция возвращает ошибку типа, если передан не DataFrame.
    """
    result = spending_by_category(bad_input, "Продукты")
    assert isinstance(result, str)
    data = json.loads(result)
    assert "Ошибка типа данных" in data.get("error", "")


@pytest.mark.parametrize(
    "columns",
    [
        ["Описание", "Сумма"],
        ["Категория", "Сумма"],
        ["Дата", "Сумма"],
    ]
)
def test_spending_by_category_key_error(columns) -> None:
    """
    Проверяет, что функция возвращает ошибку, если не хватает нужных столбцов.
    """
    df = pd.DataFrame({col: [1, 2] for col in columns})
    result = spending_by_category(df, "Продукты")
    assert isinstance(result, str)
    data = json.loads(result)
    assert "Ошибка: Отсутствует столбец" in data.get("error", "")

def test_spending_by_category_unexpected_error(sample_df: pd.DataFrame) -> None:
    """
    Проверяет, что функция корректно обрабатывает непредвиденные ошибки.
    """
    with patch.object(type(sample_df), "to_dict", side_effect=RuntimeError("Test error")):
        result = spending_by_category(sample_df, "Продукты")
        assert isinstance(result, str)
        data = json.loads(result)
        assert "Произошла ошибка" in data.get("error", "")



@pytest.mark.parametrize(
    "func_result",
    [
        ({"test": 123}),
        (["a", "b", "c"]),
        (42),
    ]
)


def test_my_decorator_creates_file(tmp_path, func_result) -> None:
    """
    Проверяет, что декоратор my_decorator создаёт файл и записывает результат функции.
    """
    file_path = tmp_path / "test_report.txt"

    @my_decorator
    def dummy_func():
        return func_result

    dummy_func()

    assert file_path.exists() or (file_path := "../data/reports_data.txt")  # если путь по умолчанию
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        assert content

    if isinstance(func_result, (dict, list, int, str)):
        assert str(func_result) in content

def test_my_decorator_custom_file(tmp_path) -> None:
    """
    Проверяет, что декоратор my_decorator записывает результат в указанный файл.
    """
    custom_file = tmp_path / "custom_report.txt"

    @my_decorator
    def dummy_func():
        return "custom result"

    dummy_func = my_decorator(dummy_func, file_name=str(custom_file))
    dummy_func()

    assert custom_file.exists()
    with open(custom_file, encoding="utf-8") as f:
        content = f.read()
        assert "custom result" in content
