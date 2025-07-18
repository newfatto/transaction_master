from typing import Any

from config import EXCEL_FILE_PATH_STR
from src.utils import (
    excel_to_df,
    get_cards_info,
    get_currency,
    get_stock_prices,
    get_top_transactions,
    transactions_since_first_day_of_month,
    user_greeting,
)


def general_page_function(date_str: str) -> dict[str, Any]:
    """
    Функция принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращает JSON-ответ,
    содержащий:
    — форму приветствия (в зависимости от времени суток),
    — отчёт по каждой карте (отчёт включает: последние 4 цифры номера карты, сумма расходов за месяц, в котором
    находится указанная дата (до этой даты), размер накопленного кешбека)
    — Топ-5 транзакций за месяц по сумме платежа
    — Курс валют, указанных пользователем
    - Стоимость акций, указанных пользователем

    Все ошибки на каждом этапе обрабатываются и возвращаются в соответствующем поле результата.
    """
    result = {}

    # Приветствие
    try:
        result["greeting"] = user_greeting()
    except Exception as e:
        result["greeting"] = f"Ошибка при получении приветствия: {e}"

    # Загрузка и фильтрация данных
    try:
        df = excel_to_df(EXCEL_FILE_PATH_STR)
        filtered_df = transactions_since_first_day_of_month(df, date_str)
    except Exception as e:
        result["cards"] = f"Ошибка при обработке данных Excel: {e}"
        result["top_transactions"] = f"Ошибка при обработке данных Excel: {e}"
        filtered_df = None

    # Карты
    if "cards" not in result:
        try:
            cards_info = get_cards_info(filtered_df)
            result["cards"] = cards_info
        except Exception as e:
            result["cards"] = f"Ошибка при получении отчёта по картам: {e}"

    # Топ транзакций
    if "top_transactions" not in result:
        try:
            top_transactions = get_top_transactions(filtered_df)
            result["top_transactions"] = top_transactions
        except Exception as e:
            result["top_transactions"] = f"Ошибка при получении топ транзакций: {e}"

    # Курсы валют
    try:
        currency_rates = get_currency()
        result["currency_rates"] = currency_rates
    except Exception as e:
        result["currency_rates"] = f"Ошибка при получении курсов валют: {e}"

    # Акции
    try:
        stock_prices = get_stock_prices()
        result["stock_prices"] = stock_prices
    except Exception as e:
        result["stock_prices"] = f"Ошибка при получении стоимости акций: {e}"

    return result


if __name__ == "__main__":
    print(general_page_function("2020-12-25 00:00:00"))
