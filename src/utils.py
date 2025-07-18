import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

from config import USER_SETTINGS_PATH_STR

logger = logging.getLogger(__name__)


def excel_to_df(excel_path: str | Any) -> DataFrame:
    """
    Загружает Excel-файл по указанному пути и возвращает DataFrame.
    В случае ошибки выбрасывает ValueError с пояснением.
    """
    logger.debug(f"Загрузка Excel-файла: {excel_path}")
    try:
        transactions_df = pd.read_excel(excel_path)
        logger.info(f"Успешно загружен Excel-файл: {excel_path}")
        return transactions_df
    except FileNotFoundError:
        logger.error(f"Файл не найден: {excel_path}")
        raise ValueError(f"Файл не найден: {excel_path}")
    except Exception as e:
        logger.error(f"Ошибка при чтении Excel-файла: {excel_path}")
        raise ValueError(f"Ошибка при чтении Excel-файла: {e}")


def transactions_since_first_day_of_month(transactions_df: DataFrame, date_str: str) -> DataFrame:
    """
    Функция принимает на вход Dataframe с информацией о финансовых операциях и
    дату в формате YYYY-MM-DD HH:MM:SS. Возвращает список словарей с данными
    за текущий месяц (если дата 2025-05-20 00:00:00, то данные для анализа будут в
    диапазоне 2025-05-01 00:00:00 - 2025-05-20 00:00:00)
    """
    logger.debug(f"Вызвана функция transactions_since_first_day_of_month с датой: {date_str}")
    if "Дата операции" not in transactions_df.columns:
        logger.error("Отсутствует колонка 'Дата операции' в DataFrame")
        raise ValueError("Ожидается колонка 'Дата операции'")
    try:
        transactions_df["Дата операции"] = pd.to_datetime(
            transactions_df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
        )
    except Exception as e:
        logger.exception(f"Ошибка при преобразовании 'Дата операции': {e}")
        raise ValueError(f"Ошибка при преобразовании 'Дата операции': {e}")
    if not isinstance(date_str, str):
        logger.error(f"Неверный формат входной даты: {date_str}")
        raise ValueError(f"Неверный формат входной даты: {date_str}")
    try:
        target_date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Неверный формат входной даты: {date_str}")
        raise ValueError(f"Неверный формат входной даты: {date_str}")

    first_day_of_month = target_date_obj.replace(day=1, hour=0, minute=0, second=0)

    result = transactions_df[
        (transactions_df["Дата операции"] >= first_day_of_month)
        & (transactions_df["Дата операции"] <= target_date_obj)
    ]
    logger.info(
        f"Функция transactions_since_first_day_of_month успешно завершена. Количество строк в результате: "
        f"{len(result)}"
    )
    return result


def user_greeting() -> str:
    """
    Функция получает информацию об актуальной дате и времени, и в зависимости от времени возвращает приветствие
    пользователя:
    с 6 до 11 'Доброе утро',
    с 12 до 16 'Добрый день',
    с 17 до 22 'Добрый вечер',
    с 23 до 5 'Доброй ночи'
    """
    logger.debug("Вызвана функция user_greeting")
    try:
        current_date = datetime.now()
        current_hour = int(current_date.strftime("%H"))
        logger.debug(f"Актуальная дата и время: {current_date}, час: {current_hour}")
        greeting = ""
        if current_hour == 23 or current_hour <= 5:
            greeting = "Доброй ночи"
        elif 5 < current_hour <= 11:
            greeting = "Доброе утро"
        elif 11 < current_hour <= 16:
            greeting = "Добрый день"
        elif 16 < current_hour <= 22:
            greeting = "Добрый вечер"
        logger.info(f"Сформировано приветствие: {greeting}")
        return greeting
    except ValueError as e:
        logger.error(f"Ошибка преобразования времени: {e}")
        return "Здравствуйте"
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка: {e}")
        return f"Ошибка: Произошла непредвиденная ошибка: {e}"


def get_cards_info(transactions_df: DataFrame | Any) -> str | list[Any]:
    """Функция принимает объект DataFrame с данными о банковских операциях, и возвращает список словарей, содержащий
    информацию: последние цифры карты, общая сумма расходов, кешбек (1 рубль на каждые 100 рублей)"""

    logger.debug("Вызвана функция get_cards_info")
    try:
        if not isinstance(transactions_df, DataFrame):
            logger.error("Входной параметр не является DataFrame")
            raise TypeError("Входной параметр должен быть DataFrame")

        card_data = {}
        nan_card_expenses = 0

        for index, row in transactions_df.iterrows():
            try:
                card_number = row["Номер карты"]
                amount = row["Сумма платежа"]

                if not (isinstance(amount, (int, float)) or pd.isna(amount)):
                    logger.error(f"Некорректный тип данных в строке {index}: {type(amount)}")
                    raise TypeError(f"Некорректный тип данных в строке DataFrame: {type(amount)}")

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
                logger.error(f"Отсутствует столбец '{e}' в строке {index}")
                return f"Ошибка: Отсутствует столбец '{e}' в DataFrame."
            except TypeError as e:
                logger.error(f"Некорректный тип данных в строке {index}: {e}")
                return f"Ошибка: Некорректный тип данных в строке DataFrame: {e}"
            except Exception as e:
                logger.exception(f"Ошибка при обработке строки {index}: {e}")
                return f"Ошибка: Произошла ошибка при обработке строки DataFrame: {e}"

        result = []

        for card in card_data.values():
            total_spent = card["total_spent"]
            cashback = int(total_spent / 100)
            result.append(
                {"last_digits": card["last_digits"], "total_spent": round(total_spent, 2), "cashback": cashback}
            )

        if nan_card_expenses > 0:
            cashback = int(nan_card_expenses / 100)
            result.append({"last_digits": "Unknown", "total_spent": round(nan_card_expenses, 2), "cashback": cashback})

        logger.info(f"Функция get_cards_info успешно завершена. Количество карт: {len(result)}")
        return result

    except TypeError as e:
        logger.error(f"Некорректный тип данных: {e}")
        return f"Ошибка: Некорректный тип данных: {e}"
    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")
        return f"Ошибка: Произошла непредвиденная ошибка: {e}"


def get_top_transactions(transactions_df: DataFrame | Any) -> str | list[Any]:
    """Функция принимает на вход объект Dataframe с банковскими операциями, и возвращает список словарей,
    представляющих собой описание пяти транзакций с самой большой суммой платежа"""
    logger.debug("Вызвана функция get_top_transactions")
    try:
        if not isinstance(transactions_df, DataFrame):
            logger.error("Входной параметр не является DataFrame")
            raise TypeError("Входной параметр должен быть DataFrame")

        required_columns = ["Сумма платежа", "Дата платежа", "Категория", "Описание"]
        for col in required_columns:
            if col not in transactions_df.columns:
                logger.error(f"Столбец '{col}' отсутствует в DataFrame")
                raise KeyError(f"Столбец '{col}' отсутствует в DataFrame")
        negative_transactions = transactions_df[transactions_df["Сумма платежа"] < 0]
        if negative_transactions.empty:
            logger.info("В DataFrame нет отрицательных транзакций (расходов)")
            return []

        top_transactions = negative_transactions.loc[
            negative_transactions["Сумма платежа"].abs().sort_values(ascending=False).index
        ]
        top_5_transactions = top_transactions.head(5)
        result = []
        for index, row in top_5_transactions.iterrows():
            transaction_info = {
                "date": row["Дата платежа"],
                "amount": -row["Сумма платежа"],
                "category": row["Категория"],
                "description": row["Описание"],
            }
            result.append(transaction_info)

            logger.info(
                f"Функция get_top_transactions успешно завершена. Количество транзакций в результате: {len(result)}"
            )
        return result

    except TypeError as e:
        logger.error(f"Ошибка типа данных: {e}")
        return f"Ошибка типа данных: {e}"
    except KeyError as e:
        logger.error(f"Ошибка: Отсутствует столбец: {e}")
        return f"Ошибка: Отсутствует столбец: {e}"
    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")
        return f"Произошла непредвиденная ошибка: {e}"


def get_currency() -> List[Dict]:
    """Функция возвращает список словарей, содержащий название валюты, интересующей пользователя и её курс
    на сегодняшний день"""
    logger.debug("Вызвана функция get_currency")
    result = []

    try:
        with open(USER_SETTINGS_PATH_STR, "r", encoding="utf-8") as f:
            try:
                user_data = json.load(f)
                user_currencies = user_data["user_currencies"]
                logger.info(f"Загружены пользовательские валюты: {user_currencies}")
            except json.JSONDecodeError:
                logger.error(f"Некорректный JSON формат в файле {USER_SETTINGS_PATH_STR}")
                print(f"Ошибка: Некорректный JSON формат в файле {USER_SETTINGS_PATH_STR}")
                return []
    except FileNotFoundError:
        logger.error(f"Файл {USER_SETTINGS_PATH_STR} не найден.")
        print(f"Ошибка: Файл {USER_SETTINGS_PATH_STR} не найден.")
        return []

    load_dotenv()
    api_key = os.getenv("MY_API_CURRENCY")
    if not api_key:
        logger.error("API ключ 'MY_API_CURRENCY' не найден.")
        print("Ошибка: API ключ 'MY_API_CURRENCY' не найден.")
        return []

    for currency in user_currencies:
        currency_rate = {"currency": currency}
        url = f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={currency}&amount=1"

        headers = {"apikey": api_key}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            logger.debug(f"Успешный запрос курса для {currency}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе курса для {currency}: {e}")
            print(f"Ошибка при запросе курса для {currency}: {e}")
            continue

        try:
            response_data = response.json()
            currency_rate["rate"] = round(response_data["info"]["rate"], 2)
            logger.info(f"Курс для {currency}: {currency_rate['rate']}")
            result.append(currency_rate)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            logger.error(
                f"Запрос не был успешным для {currency}. Возможная причина: "
                f"{getattr(response, 'reason', 'нет данных')}, ошибка: {e}"
            )
            print(f"Запрос не был успешным. Возможная причина: {response.reason}, ошибка: {e}")
            continue

    return result


def get_stock_prices() -> List[Dict]:
    """Функция принимает на вход путь до json-файла, содержащего информацию об акциях, которые интересуют пользователя,
    и возвращает список словарей, содержащий название акции и её стоимость на сегодняшний день"""
    logger.debug("Вызвана функция get_stock_prices")
    result = []

    try:
        with open(USER_SETTINGS_PATH_STR, "r", encoding="utf-8") as f:
            try:
                user_data = json.load(f)
                user_stocks = user_data["user_stocks"]
                logger.info(f"Загружены пользовательские акции: {user_stocks}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Ошибка при чтении JSON: {e}")
                print(f"Ошибка при чтении JSON: {e}")
                return []
    except FileNotFoundError:
        logger.error(f"Файл {USER_SETTINGS_PATH_STR} не найден.")
        print(f"Ошибка: Файл {USER_SETTINGS_PATH_STR} не найден.")
        return []

    load_dotenv()
    api_key = os.getenv("MY_API_STOCK")
    if not api_key:
        logger.error("API ключ 'MY_API_STOCK' не найден.")
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
                logger.info(f"Цена для {stock}: {stock_info['price']}")
            except (KeyError, TypeError) as e:
                logger.error(f"Ошибка при извлечении цены для {stock}: {e}, response_data={response_data}")
                print(f"Ошибка при извлечении цены для {stock}: {e}, response_data={response_data}")
                continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе стоимости для {stock}: {e}")
            print(f"Ошибка при запросе стоимости для {stock}: {e}")
            continue
    logger.info(f"Функция get_stock_prices завершена. Количество акций: {len(result)}")
    return result
