from utils import user_greeting, get_cards_info, excel_to_list, get_top_transactions, get_currency
import json


def general_page_function(date_str: str):
    """функция, принимает на вход строку с датой и временем в формате YYYY-MM-DD HH: MM:SS возвращает JSON-ответ"""

    result = {
        "greeting": user_greeting(),
        "cards": get_cards_info(excel_to_list("../data/operations.xlsx", date_str)),
        "top_transactions": get_top_transactions(excel_to_list("../data/operations.xlsx", date_str)),
        "currency_rates": get_currency('../user_settings.json'),
        "stock_prices": []
    }

    json_string = json.dumps(result, ensure_ascii=False)
    print(json_string)
    return result


if __name__ == "__main__":

    print(general_page_function("2019-10-12 14:42:26"))
