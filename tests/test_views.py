import json
from unittest.mock import patch

import pytest

from src.views import general_page_function


def test_general_page_function_success() -> None:
    """
    Проверяет, что функция general_page_function возвращает корректный словарь с данными при успешной
    работе всех зависимостей.
    """
    fake_greeting = "Добрый день"
    fake_cards = [{"last_digits": "1234", "total_spent": 1000, "cashback": 10}]
    fake_top_transactions = [{"date": "2023-01-01", "amount": 100, "category": "Продукты", "description": "Покупка"}]
    fake_currency = [{"currency": "USD", "rate": 99.99}]
    fake_stocks = [{"stock": "AAPL", "price": 123.45}]
    fake_df = "fake_df"
    fake_filtered_df = "filtered_df"

    with (
        patch("src.views.user_greeting", return_value=fake_greeting),
        patch("src.views.excel_to_df", return_value=fake_df),
        patch("src.views.transactions_since_first_day_of_month", return_value=fake_filtered_df),
        patch("src.views.get_cards_info", return_value=fake_cards),
        patch("src.views.get_top_transactions", return_value=fake_top_transactions),
        patch("src.views.get_currency", return_value=fake_currency),
        patch("src.views.get_stock_prices", return_value=fake_stocks),
    ):

        result = general_page_function("2023-01-01 12:00:00")
        result = json.loads(result)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"greeting", "cards", "top_transactions", "currency_rates", "stock_prices"}
        assert result["greeting"] == fake_greeting
        assert result["cards"] == fake_cards
        assert result["top_transactions"] == fake_top_transactions
        assert result["currency_rates"] == fake_currency
        assert result["stock_prices"] == fake_stocks


@pytest.mark.parametrize(
    "exception,field",
    [
        (Exception("greet error"), "greeting"),
        (Exception("excel error"), "cards"),
        (Exception("excel error"), "top_transactions"),
        (Exception("cards error"), "cards"),
        (Exception("top error"), "top_transactions"),
        (Exception("currency error"), "currency_rates"),
        (Exception("stock error"), "stock_prices"),
    ],
)
def test_general_page_function_errors(exception: Exception, field: str) -> None:
    """
    Проверяет, что функция general_page_function корректно обрабатывает ошибки на каждом этапе и возвращает строку
    с ошибкой в соответствующем поле.
    """
    # Значения по умолчанию для всех зависимостей
    fake_greeting = "greet"
    fake_df = "df"
    fake_filtered_df = "filtered_df"
    fake_cards = []
    fake_top = []
    fake_currency = []
    fake_stocks = []

    # Патчим все зависимости, кроме той, которая должна выбросить ошибку
    patches = {
        "user_greeting": patch("src.views.user_greeting", return_value=fake_greeting),
        "excel_to_df": patch("src.views.excel_to_df", return_value=fake_df),
        "transactions_since_first_day_of_month": patch(
            "src.views.transactions_since_first_day_of_month", return_value=fake_filtered_df
        ),
        "get_cards_info": patch("src.views.get_cards_info", return_value=fake_cards),
        "get_top_transactions": patch("src.views.get_top_transactions", return_value=fake_top),
        "get_currency": patch("src.views.get_currency", return_value=fake_currency),
        "get_stock_prices": patch("src.views.get_stock_prices", return_value=fake_stocks),
    }

    # Определяем, какую функцию патчить с ошибкой
    error_patch_map = {
        "greeting": "user_greeting",
        "cards": "get_cards_info",
        "top_transactions": "get_top_transactions",
        "currency_rates": "get_currency",
        "stock_prices": "get_stock_prices",
    }
    # Для ошибок Excel/фильтрации патчим excel_to_df или transactions_since_first_day_of_month
    if field in ("cards", "top_transactions") and "excel" in str(exception):
        patches["excel_to_df"] = patch("src.views.excel_to_df", side_effect=exception)
    elif field in ("cards", "top_transactions") and "filter" in str(exception):
        patches["transactions_since_first_day_of_month"] = patch(
            "src.views.transactions_since_first_day_of_month", side_effect=exception
        )
    else:
        patches[error_patch_map.get(field, field)] = patch(
            f"src.views.{error_patch_map.get(field, field)}", side_effect=exception
        )

    with (
        patches["user_greeting"],
        patches["excel_to_df"],
        patches["transactions_since_first_day_of_month"],
        patches["get_cards_info"],
        patches["get_top_transactions"],
        patches["get_currency"],
        patches["get_stock_prices"],
    ):
        result = general_page_function("2023-01-01 12:00:00")
        result = json.loads(result)
        assert isinstance(result, dict)
        assert field in result
        assert "Ошибка" in str(result[field])
