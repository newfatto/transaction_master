import os
import pandas as pd
from pandas import DataFrame

# import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import json


def excel_to_list(date_str: str) -> DataFrame:
    """
    Функция принимает на вход дату в формате YYYY-MM-DD HH:MM:SS, и возвращает список словарей с данными
    за текущий месяц (если дата — 20.05.2025, то данные для анализа будут в
    диапазоне 01.05.2025-20.05.2025)

    В Excel-файле даты хранятся в формате DD.MM.YYYY HH:MM:SS
    """
    current_dir = Path(__file__).parent
    excel_path = current_dir / "../data/operations.xlsx"
    target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    first_day_of_month = target_date.replace(day=1, hour=0, minute=0, second=0)
    try:
        df = pd.read_excel(excel_path, parse_dates=["Дата операции"], date_format="%d.%m.%Y %H:%M:%S")

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {excel_path} не найден")
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла: {str(e)}")

    filtered_df = df[(df["Дата операции"] >= first_day_of_month) & (df["Дата операции"] <= target_date)]
    result = filtered_df

    return result


def user_greeting() -> str:
    """
    Функция получает информацию об актуальной дате и времени, и в зависимости от времени возвращает приветствие
    пользователя: с 6 до 11 'Доброе утро', с 12 до 16 'Добрый день', с 17 до 22 'Добрый вечер', с 23 до 5 'Доброй ночи'
    """
    current_date = datetime.now()
    current_hour = int(current_date.strftime("%H"))
    greeting = ""
    if current_hour == 23 or current_hour <= 5:
        greeting = "Доброй ночи"
    elif 5 < current_hour <= 11:
        greeting = "Доброе утро"
    elif 11 < current_hour <= 16:
        greeting = "Добрый день"
    elif 16 < current_hour <= 22:
        greeting = "Добрый вечер"
    return greeting


def get_cards_info(operations_list: DataFrame):
    """Функция принимает объект DataFrame с данными о банковских операциях, и возвращает список словарей, содержащий
    информацию: последние цифры карты, общая сумма расходов, кешбек (1 рубль на каждые 100 рублей)"""

    card_data = {}
    nan_card_expenses = 0

    for index, row in operations_list.iterrows():
        card_number = row["Номер карты"]
        amount = row["Сумма платежа"]

        if pd.isna(card_number):
            if isinstance(amount, (int, float)):
                nan_card_expenses += abs(amount)
        else:
            last_digits = str(card_number).replace("*", "")

            if last_digits not in card_data:
                card_data[last_digits] = {"last_digits": last_digits, "total_spent": 0, "cashback": 0}

            if isinstance(amount, (int, float)):
                card_data[last_digits]["total_spent"] += abs(amount)

    result = []

    for card in card_data.values():
        total_spent = card["total_spent"]
        cashback = int(total_spent / 100)
        result.append({"last_digits": card["last_digits"], "total_spent": round(total_spent, 2), "cashback": cashback})

    if nan_card_expenses > 0:
        cashback = int(nan_card_expenses / 100)
        result.append({"last_digits": "Unknown", "total_spent": round(nan_card_expenses, 2), "cashback": cashback})

    return result


def get_top_transactions(operations_list: DataFrame):
    negative_transactions = operations_list[operations_list["Сумма операции"] < 0]
    top_transactions = negative_transactions.loc[
        negative_transactions["Сумма операции"].abs().sort_values(ascending=False).index
    ]
    top_5_transactions = top_transactions.head(5)
    print(top_5_transactions)
    result = []
    for index, row in top_5_transactions.iterrows():
        transaction_info = {
            "date": row["Дата платежа"],
            "amount": -row["Сумма операции"],
            "category": row["Категория"],
            "description": row["Описание"],
        }
        result.append(transaction_info)

    print(result)
    return result


def general_page_function(date_str: str):
    """функция, принимает на вход строку с датой и временем в формате YYYY-MM-DD HH: MM:SS возвращает JSON-ответ"""

    result = {
        "greeting": user_greeting(),
        "cards": get_cards_info(excel_to_list(date_str)),
        "top_transactions": get_top_transactions(excel_to_list(date_str)),
        "currency_rates": [],
    }

    json_string = json.dumps(result, ensure_ascii=False)
    print(json_string)
    return None


if __name__ == "__main__":

    general_page_function("2019-10-12 14:42:26")
