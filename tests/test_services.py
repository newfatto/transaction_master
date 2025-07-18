from typing import Any
from unittest.mock import patch

import pytest
from pandas import DataFrame

from src.services import search_money_transfer_to_people


def test_search_money_transfer_to_people_no_matches() -> None:
    """
    Проверяет, что функция возвращает пустой список, если нет подходящих транзакций.
    """
    df = DataFrame({"Категория": ["Покупки"], "Описание": ["Покупка в магазине"]})
    result_json = search_money_transfer_to_people(df)
    assert isinstance(result_json, str)
    assert "[]" in result_json


def test_search_money_transfer_to_people_success(sample_df: DataFrame) -> None:
    """
    Проверяет корректную работу поиска переводов людям по шаблону 'Имя Ф.'.
    """
    result_json = search_money_transfer_to_people(sample_df)
    assert isinstance(result_json, str)
    assert '"Описание": "Иван И."' in result_json


@pytest.mark.parametrize(
    "bad_input",
    [
        123,  # не DataFrame
        "not a dataframe",
        None,
        [1, 2, 3],
    ],
)
def test_search_money_transfer_to_people_type_error(bad_input: Any) -> None:
    """
    Проверяет, что функция возвращает ошибку типа, если передан не DataFrame.
    """
    result_json = search_money_transfer_to_people(bad_input)
    assert isinstance(result_json, str)
    assert "Ошибка типа данных" in result_json


@pytest.mark.parametrize(
    "columns",
    [
        ["Описание", "Сумма"],
        ["Категория", "Сумма"],
        ["Дата", "Сумма"],
    ],
)
def test_search_money_transfer_to_people_key_error(columns: list[str]) -> None:
    """
    Проверяет, что функция возвращает ошибку, если не хватает нужных столбцов.
    """
    df = DataFrame({col: [1, 2] for col in columns})
    result_json = search_money_transfer_to_people(df)
    assert isinstance(result_json, str)
    assert "Ошибка: Отсутствует столбец" in result_json


def test_search_money_transfer_to_people_unexpected_error(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция корректно обрабатывает непредвиденные ошибки.
    """
    with patch.object(DataFrame, "to_dict", side_effect=RuntimeError("Test error")):
        result_json = search_money_transfer_to_people(sample_df)
        assert isinstance(result_json, str)
        assert "Произошла непредвиденная ошибка" in result_json
