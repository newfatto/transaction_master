import pandas as pd
from pandas import DataFrame

import os
from dotenv import load_dotenv
import requests

from datetime import datetime
from typing import List, Dict, Any
import json


def excel_to_list(excel_path: str, date_str: str| Any) -> DataFrame:
    """
    Функция принимает на вход путь до excel-файла с информацией о финансовых операциях и
    дату в формате YYYY-MM-DD HH:MM:SS. Возвращает список словарей с данными
    за текущий месяц (если дата — 20.05.2025, то данные для анализа будут в
    диапазоне 01.05.2025-20.05.2025)

    В Excel-файле даты хранятся в формате DD.MM.YYYY HH:MM:SS
    """
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
    try:
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
    except ValueError:
        return "Здравствуйте"
    except Exception as e:
        return f"Ошибка: Произошла непредвиденная ошибка: {e}"


def get_cards_info(operations_list: DataFrame):
    """Функция принимает объект DataFrame с данными о банковских операциях, и возвращает список словарей, содержащий
    информацию: последние цифры карты, общая сумма расходов, кешбек (1 рубль на каждые 100 рублей)"""

    try:
        if not isinstance(operations_list, DataFrame):
            raise TypeError("Входной параметр должен быть DataFrame")

        card_data = {}
        nan_card_expenses = 0

        for index, row in operations_list.iterrows():
            try:
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
            except KeyError as e:
                return f"Ошибка: Отсутствует столбец '{e}' в DataFrame."
            except TypeError as e:
                return f"Ошибка: Некорректный тип данных в строке DataFrame: {e}"
            except Exception as e:
                return f"Ошибка: Произошла ошибка при обработке строки DataFrame: {e}"

        result = []

        for card in card_data.values():
            total_spent = card["total_spent"]
            cashback = int(total_spent / 100)
            result.append({"last_digits": card["last_digits"], "total_spent": round(total_spent, 2), "cashback": cashback})

        if nan_card_expenses > 0:
            cashback = int(nan_card_expenses / 100)
            result.append({"last_digits": "Unknown", "total_spent": round(nan_card_expenses, 2), "cashback": cashback})

        return result

    except TypeError as e:
        return f"Ошибка: Некорректный тип данных: {e}"
    except Exception as e:
        return f"Ошибка: Произошла непредвиденная ошибка: {e}"


def get_top_transactions(operations_list: DataFrame):
    try:
        if not isinstance(operations_list, DataFrame):
            raise TypeError("Входной параметр должен быть DataFrame")

        required_columns = ["Сумма операции", "Дата платежа", "Категория", "Описание"]
        for col in required_columns:
            if col not in operations_list.columns:
                raise KeyError(f"Столбец '{col}' отсутствует в DataFrame")
        negative_transactions = operations_list[operations_list["Сумма операции"] < 0]
        if negative_transactions.empty:
            return []

        top_transactions = negative_transactions.loc[
            negative_transactions["Сумма операции"].abs().sort_values(ascending=False).index
        ]
        top_5_transactions = top_transactions.head(5)
        result = []
        for index, row in top_5_transactions.iterrows():
            transaction_info = {
                "date": row["Дата платежа"],
                "amount": -row["Сумма операции"],
                "category": row["Категория"],
                "description": row["Описание"],
            }
            result.append(transaction_info)

        return result

    except TypeError as e:
        return f"Ошибка типа данных: {e}"
    except KeyError as e:
        return f"Ошибка: Отсутствует столбец: {e}"
    except Exception as e:
        return f"Произошла непредвиденная ошибка: {e}"

def get_currency(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход путь до json-файла, содержащего информацию о валютах, которые интересуют пользователя,
    и возвращает список словарей, содержащий название валюты и её курс на сегодняшний день"""
    result = []

    try:
        with open (path_to_json, 'r', encoding='utf-8') as f:
            try:
                user_data = json.load(f)
                user_currencies = user_data["user_currencies"]
            except json.JSONDecodeError:
                print(f"Ошибка: Некорректный JSON формат в файле {path_to_json}")
                return []
    except FileNotFoundError:
        print(f"Ошибка: Файл {path_to_json} не найден.")
        return []

    load_dotenv()
    api_key = os.getenv('MY_API_CURRENCY')
    if not api_key:
        print("Ошибка: API ключ 'MY_API_CURRENCY' не найден.")
        return []

    for currency in user_currencies:
        currency_rate = {"currency": currency}
        url = f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={currency}&amount=1"

        headers = {
            "apikey": api_key
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе курса для {currency}: {e}")
            continue

        try:
            response_data = response.json()
            currency_rate["rate"] = round(response_data["info"]["rate"], 2)
            result.append(currency_rate)
        except:
            print(f"Запрос не был успешным. Возможная причина: {response.reason}")
            continue

    return result



def get_stock_prices(path_to_json: str) -> List[Dict]:
    """Функция принимает на вход путь до json-файла, содержащего информацию об акциях, которые интересуют пользователя,
    и возвращает список словарей, содержащий название акции и её стоимость на сегодняшний день"""
    result = []

    try:
        with open (path_to_json, 'r', encoding='utf-8') as f:
            try:
                user_data = json.load(f)
                user_stocks = user_data["user_stocks"]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Ошибка при чтении JSON: {e}")
                return []
    except FileNotFoundError:
        print(f"Ошибка: Файл {path_to_json} не найден.")
        return []

    load_dotenv()
    api_key = os.getenv('MY_API_STOCK')
    if not api_key:
        print("Ошибка: API ключ 'MY_API_STOCK' не найден.")
        return []

    for stock in user_stocks:
        stock_info = {"stock": stock}
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={api_key}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            try:
                stock_info["price"] = round(float(response_data["Global Quote"]["05. price"]), 2)
                result.append(stock_info)
            except (KeyError, TypeError) as e:
                print(f"Ошибка при извлечении цены для {stock}: {e}, response_data={response_data}")
                continue

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе стоимости для {stock}: {e}")
            continue

    return result





if __name__ == "__main__":
    print(get_stock_prices('../user_settings.json'))
