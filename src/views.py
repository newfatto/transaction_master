from utils import (user_greeting, get_cards_info, transactions_since_first_day_of_month, get_top_transactions,
                   get_currency, get_stock_prices, excel_to_df)

def general_page_function(date_str: str):
    """Функция принимает на вход строку с датой и временем в формате YYYY-MM-DD HH: MM:SS возвращает JSON-ответ,
    содержащий:
    — форму приветствия (в зависимости от времени суток),
    — отчёт по каждой карте (отчёт включает: последние 4 цифры номера карты, сумма расходов за месяц, в котором
    находится указанная дата (до этой даты), размер накопленного кешбека)
    — Топ-5 транзакций за месяц по сумме платежа
    — Курс валют, указанных пользователем
    - Стоимость акций, указанных пользователем
    """

    result = {
        "greeting": user_greeting(),
        "cards": get_cards_info(transactions_since_first_day_of_month(excel_to_df("../data/operations.xlsx"), date_str)),
        "top_transactions": get_top_transactions(transactions_since_first_day_of_month
                                                 (excel_to_df("../data/operations.xlsx"), date_str)),
        "currency_rates": get_currency('../user_settings.json'),
        "stock_prices": get_stock_prices('../user_settings.json')
    }

    return result

if __name__ == "__main__":

    print(general_page_function("2019-10-12 14:42:26"))
