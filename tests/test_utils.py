import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest
import requests
from pandas import DataFrame

from src.utils import (
    excel_to_df,
    get_cards_info,
    get_currency,
    get_stock_prices,
    get_top_transactions,
    transactions_since_first_day_of_month,
    user_greeting,
)


def test_excel_to_df_valid(sample_excel_file: str, sample_df: DataFrame) -> None:
    """
    Проверяет, что функция excel_to_df корректно читает Excel-файл и возвращает DataFrame, совпадающий с исходным.
    """
    df = excel_to_df(sample_excel_file)
    df = df.where(pd.notnull(df), None)
    sample_df = sample_df.where(pd.notnull(sample_df), None)
    pd.testing.assert_frame_equal(df, sample_df, check_dtype=False)


@pytest.mark.parametrize(
    "bad_path",
    [
        "not_existing_file.xlsx",
        "",
    ],
)
def test_excel_to_df_file_not_found(bad_path: str) -> None:
    """
    Проверяет, что функция excel_to_df выбрасывает ValueError с корректным сообщением,
    если файл не найден или путь некорректен.
    """
    with pytest.raises(ValueError) as e:
        excel_to_df(bad_path)
    assert "Файл не найден" in str(e.value)


def test_excel_to_df_none_path() -> None:
    """
    Проверяет, что функция excel_to_df выбрасывает ValueError с сообщением об ошибке чтения, если путь равен None.
    """
    with pytest.raises(ValueError) as e:
        excel_to_df(None)
    assert "Ошибка при чтении Excel-файла" in str(e.value)


def test_excel_to_df_wrong_format(tmp_path: Path) -> None:
    """
    Проверяет, что функция excel_to_df выбрасывает ValueError, если файл не является Excel-файлом.
    """
    wrong_file = tmp_path / "not_excel.txt"
    wrong_file.write_text("not an excel content")
    with pytest.raises(ValueError) as e:
        excel_to_df(str(wrong_file))
    assert "Ошибка при чтении Excel-файла" in str(e.value)


@pytest.mark.parametrize(
    "invalid_type",
    [
        123,
        3.14,
        [],
        {},
        object(),
    ],
)
def test_excel_to_df_invalid_path_type(invalid_type: Any) -> None:
    """
    Проверяет, что функция excel_to_df выбрасывает ValueError, если путь передан не строкой.
    """
    with pytest.raises(ValueError) as e:
        excel_to_df(invalid_type)
    assert "Ошибка при чтении Excel-файла" in str(e.value)


def test_transactions_since_first_day_of_month_valid(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает только операции текущего месяца до указанной даты.
    """
    # В sample_df есть операции за 01.05.2025, 10.05.2025, 01.04.2025
    date_str = "2025-05-20 00:00:00"
    result = transactions_since_first_day_of_month(sample_df, date_str)
    # Должны остаться только строки за май 2025
    assert not result.empty
    assert (result["Дата операции"].dt.month == 5).all()  # type: ignore
    assert (result["Дата операции"].dt.year == 2025).all()  # type: ignore
    assert (result["Дата операции"] <= pd.to_datetime(date_str)).all()


def test_transactions_since_first_day_of_month_no_rows_in_month(sample_df: DataFrame) -> None:
    """
    Проверяет, что если в текущем месяце нет операций, возвращается пустой DataFrame.
    """
    date_str = "2025-06-15 00:00:00"
    result = transactions_since_first_day_of_month(sample_df, date_str)
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_transactions_since_first_day_of_month_missing_column(sample_df: DataFrame) -> None:
    """
    Проверяет, что если нет колонки 'Дата операции', выбрасывается ValueError.
    """
    df = sample_df.drop(columns=["Дата операции"])
    with pytest.raises(ValueError) as e:
        transactions_since_first_day_of_month(df, "2025-05-20 00:00:00")
    assert "Ожидается колонка 'Дата операции'" in str(e.value)


@pytest.mark.parametrize(
    "bad_date",
    [
        "2025/05/20 00:00:00",
        "20-05-2025 00:00:00",
        "2025-05-20",
        "not a date",
        "",
        None,
    ],
)
def test_transactions_since_first_day_of_month_bad_date_format(sample_df: DataFrame, bad_date: Any) -> None:
    """
    Проверяет, что при неверном формате даты выбрасывается ValueError.
    """
    with pytest.raises(ValueError) as e:
        transactions_since_first_day_of_month(sample_df, bad_date)
    assert "Неверный формат входной даты" in str(e.value)


def test_transactions_since_first_day_of_month_bad_column_format(sample_df: DataFrame) -> None:
    """
    Проверяет, что при некорректных значениях в колонке 'Дата операции' выбрасывается ValueError
    или значения становятся NaT.
    """
    df = sample_df.copy()
    df.loc[0, "Дата операции"] = "not a date"
    date_str = "2025-05-20 00:00:00"
    result = transactions_since_first_day_of_month(df, date_str)
    # Проверяем, что в результате нет строк с NaT в 'Дата операции'
    assert pd.notnull(result["Дата операции"]).all()


def test_transactions_since_first_day_of_month_boundary(sample_df: DataFrame) -> None:
    """
    Проверяет, что операция на границе диапазона (первое число месяца) включается в результат.
    """
    date_str = "2025-05-01 12:00:00"
    result = transactions_since_first_day_of_month(sample_df, date_str)
    assert not result.empty
    assert pd.to_datetime("01.05.2025 12:00:00", format="%d.%m.%Y %H:%M:%S") in result["Дата операции"].values


@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (16, "Добрый день"),
        (17, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (0, "Доброй ночи"),
        (5, "Доброй ночи"),
    ],
)
def test_user_greeting_by_hour(hour: int, expected: str) -> None:
    """
    Проверяет, что функция user_greeting возвращает корректное приветствие для каждого часа суток.
    """
    fake_date = datetime(2025, 5, 1, hour, 0, 0)
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_date
        mock_datetime.strftime = datetime.strftime
        result = user_greeting()
        assert result == expected


def test_user_greeting_value_error() -> None:
    """
    Проверяет, что при ошибке преобразования времени функция user_greeting возвращает сообщение об ошибке.
    """
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = "not a datetime"
        mock_datetime.strftime = lambda self, fmt: "not a number"
        result = user_greeting()
        assert "Ошибка: Произошла непредвиденная ошибка" in result


def test_user_greeting_returns_hello() -> None:
    """
    Проверяет, что при ValueError функция user_greeting возвращает 'Здравствуйте'.
    """
    with patch("src.utils.datetime") as mock_datetime:
        mock_now = mock_datetime.now.return_value
        mock_now.strftime.side_effect = ValueError("test error")
        result = user_greeting()
        assert result == "Здравствуйте"


def test_user_greeting_unexpected_error() -> None:
    """
    Проверяет, что при неожиданной ошибке возвращается сообщение об ошибке.
    """
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.side_effect = Exception("Test error")
        result = user_greeting()
        assert "Ошибка: Произошла непредвиденная ошибка" in result


def test_get_cards_info_valid(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает корректную информацию по картам и кешбеку.
    """
    result = get_cards_info(sample_df)
    assert isinstance(result, list)
    # Проверяем, что в результате есть словари с нужными ключами
    for card in result:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card
        assert isinstance(card["cashback"], int)
    # Проверяем, что кешбек считается правильно
    for card in result:
        assert card["cashback"] == int(card["total_spent"] // 100)


def test_get_cards_info_empty_df() -> None:
    """
    Проверяет, что функция возвращает пустой список для пустого DataFrame.
    """
    df = pd.DataFrame(columns=["Номер карты", "Сумма платежа"])
    result = get_cards_info(df)
    assert isinstance(result, list)
    assert result == []


def test_get_cards_info_no_card_column(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает ошибку, если нет столбца 'Номер карты'.
    """
    df = sample_df.drop(columns=["Номер карты"])
    result = get_cards_info(df)
    assert isinstance(result, str)
    assert "Ошибка: Отсутствует столбец" in result


def test_get_cards_info_no_amount_column(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает ошибку, если нет столбца 'Сумма платежа'.
    """
    df = sample_df.drop(columns=["Сумма платежа"])
    result = get_cards_info(df)
    assert isinstance(result, str)
    assert "Ошибка: Отсутствует столбец" in result


@pytest.mark.parametrize(
    "bad_input",
    [
        123,
        "not a dataframe",
        None,
        [1, 2, 3],
    ],
)
def test_get_cards_info_type_error(bad_input: Any) -> None:
    """
    Проверяет, что функция возвращает ошибку типа, если передан не DataFrame.
    """
    result = get_cards_info(bad_input)
    assert isinstance(result, str)
    assert "Ошибка: Некорректный тип данных" in result


def test_get_cards_info_nan_card(sample_df: DataFrame) -> None:
    """
    Проверяет, что расходы без номера карты учитываются как 'Unknown'.
    """
    df = sample_df.copy()
    df.loc[0, "Номер карты"] = float("nan")
    result = get_cards_info(df)
    assert isinstance(result, list)
    assert any(card["last_digits"] == "Unknown" for card in result)


def test_get_cards_info_row_type_error(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает ошибку при некорректном типе данных в строке.
    """
    df = sample_df.copy()
    df["Сумма платежа"] = df["Сумма платежа"].astype(object)
    df.loc[:, "Сумма платежа"] = "not a number"  # строка вместо числа
    result = get_cards_info(df)
    assert isinstance(result, str)
    assert "Ошибка: Некорректный тип данных в строке DataFrame" in result


def test_get_cards_info_row_unexpected_error(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает ошибку при неожиданной ошибке в строке.
    """
    df = sample_df.copy()
    # Удаляем столбец только в одной строке, чтобы вызвать KeyError
    df.at[0, "Номер карты"] = None
    df = df.drop(columns=["Номер карты"])
    result = get_cards_info(df)
    assert isinstance(result, str)
    assert (
        "Ошибка: Отсутствует столбец" in result or "Ошибка: Произошла ошибка при обработке строки DataFrame" in result
    )


def test_get_top_transactions_valid(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает список из 5 транзакций (максимум) с наибольшими расходами.
    """
    df = sample_df.copy()
    for i in range(4):
        df.loc[len(df)] = [
            "01.05.2025 12:00:00",
            f"****{1000 + i}",
            -1000 - i * 100,
            "Продукты",
            f"Описание {i}",
            "01.05.2025 12:00:00",
        ]
    result = get_top_transactions(df)
    assert isinstance(result, list)
    assert len(result) == 5
    # Проверяем, что суммы идут по убыванию
    amounts = [item["amount"] for item in result]
    assert amounts == sorted(amounts, reverse=True)
    # Проверяем, что все суммы положительные (расходы)
    assert all(a > 0 for a in amounts)


def test_get_top_transactions_less_than_5(sample_df: DataFrame) -> None:
    """
    Проверяет, что если транзакций меньше 5, возвращаются все.
    """
    df = sample_df.copy()
    df = df[df["Сумма платежа"] < 0].head(2)
    result = get_top_transactions(df)
    assert isinstance(result, list)
    assert len(result) == 2


def test_get_top_transactions_no_expenses(sample_df: DataFrame) -> None:
    """
    Проверяет, что если нет расходов, возвращается пустой список.
    """
    df = sample_df.copy()
    df["Сумма платежа"] = abs(df["Сумма платежа"])
    result = get_top_transactions(df)
    assert isinstance(result, list)
    assert result == []


def test_get_top_transactions_missing_column(sample_df: DataFrame) -> None:
    """
    Проверяет, что если отсутствует нужный столбец, возвращается строка с ошибкой.
    """
    for col in ["Сумма платежа", "Дата платежа", "Категория", "Описание"]:
        df = sample_df.copy().drop(columns=[col])
        result = get_top_transactions(df)
        assert isinstance(result, str)
        assert "Ошибка: Отсутствует столбец" in result


@pytest.mark.parametrize(
    "bad_input",
    [
        123,
        "not a dataframe",
        None,
        [1, 2, 3],
    ],
)
def test_get_top_transactions_type_error(bad_input: Any) -> None:
    """
    Проверяет, что функция возвращает ошибку типа, если передан не DataFrame.
    """
    result = get_top_transactions(bad_input)
    assert isinstance(result, str)
    assert "Ошибка типа данных" in result


def test_get_top_transactions_unexpected_error(sample_df: DataFrame) -> None:
    """
    Проверяет, что функция возвращает строку с ошибкой при неожиданной ошибке.
    """
    df = sample_df.copy()
    df["Сумма платежа"] = "not a number"
    result = get_top_transactions(df)
    assert isinstance(result, str)
    assert "Ошибка типа данных" in result


@pytest.fixture
def user_settings(tmp_path: Path) -> tuple[str, list[str]]:
    """
    Создаёт временный JSON-файл с пользовательскими валютами.
    """
    data = {"user_currencies": ["USD", "EUR"]}
    file_path = tmp_path / "user_settings.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return str(file_path), data["user_currencies"]


def test_get_currency_success(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает корректный список курсов валют при успешном запросе.
    """
    file_path, currencies = user_settings

    def fake_get(*args, **kwargs) -> None:
        _ = args
        _ = kwargs

        def raise_for_status() -> None:
            pass

        def json_func() -> json:
            return {"info": {"rate": 99.99}}

        return type(
            "FakeResponse", (), {"raise_for_status": staticmethod(raise_for_status), "json": staticmethod(json_func)}
        )()

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):

        result = get_currency()
        assert isinstance(result, list)
        assert len(result) == len(currencies)
        for item, currency in zip(result, currencies):
            assert item["currency"] == currency
            assert item["rate"] == 99.99


def test_get_currency_file_not_found() -> None:
    """
    Проверяет, что функция возвращает пустой список, если файл с настройками не найден.
    """
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", "not_existing_file.json"),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
    ):
        result = get_currency()
        assert result == []


def test_get_currency_bad_json(tmp_path: Path) -> None:
    """
    Проверяет, что функция возвращает пустой список при некорректном JSON в файле настроек.
    """
    file_path = tmp_path / "bad.json"
    file_path.write_text("{not a json}", encoding="utf-8")
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", str(file_path)),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
    ):
        result = get_currency()
        assert result == []


def test_get_currency_no_api_key(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список, если API ключ не найден.
    """
    file_path, _ = user_settings
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value=None),
    ):
        result = get_currency()
        assert result == []


def test_get_currency_request_error(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список, если при запросе к API возникает ошибка.
    """
    file_path, currencies = user_settings

    def fake_get(url: str, headers: str, timeout: str):
        _ = url
        _ = headers
        _ = timeout
        raise requests.exceptions.RequestException("Request failed")

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):
        result = get_currency()
        assert result == []


def test_get_currency_bad_response(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список, если ответ API не содержит ожидаемых данных.
    """
    file_path, currencies = user_settings

    def fake_get(url: str, headers: str, timeout: str) -> None:
        _ = url
        _ = headers
        _ = timeout

        def raise_for_status() -> None:
            pass

        def json_func() -> json:
            return {"bad": "data"}

        def reason() -> str:
            return "Bad response"

        resp = type(
            "FakeResponse",
            (),
            {
                "raise_for_status": staticmethod(raise_for_status),
                "json": staticmethod(json_func),
                "reason": property(lambda self: reason),
            },
        )()
        return resp

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):
        result = get_currency()
        assert result == []


@pytest.fixture
def user_settings_stocks(tmp_path: Any) -> tuple[str, list[str]]:
    """
    Создаёт временный JSON-файл с пользовательскими акциями.
    """
    data = {"user_stocks": ["AAPL", "TSLA"]}
    file_path = tmp_path / "user_settings.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return str(file_path), data["user_stocks"]


def test_get_stock_prices_success(user_settings_stocks: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает корректный список цен акций при успешном запросе.
    """
    file_path, stocks = user_settings_stocks

    def fake_get(url, timeout):
        _ = url
        _ = timeout

        def raise_for_status() -> None:
            pass

        def json_func():
            return {"Global Quote": {"05. price": "123.45"}}

        return type(
            "FakeResponse", (), {"raise_for_status": staticmethod(raise_for_status), "json": staticmethod(json_func)}
        )()

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):

        result = get_stock_prices()
        assert isinstance(result, list)
        assert len(result) == len(stocks)
        for item, stock in zip(result, stocks):
            assert item["stock"] == stock
            assert item["price"] == 123.45


def test_get_stock_prices_file_not_found() -> None:
    """
    Проверяет, что функция возвращает пустой список, если файл с настройками не найден.
    """
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", "not_existing_file.json"),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
    ):
        result = get_stock_prices()
        assert result == []


def test_get_stock_prices_bad_json(tmp_path: Path) -> None:
    """
    Проверяет, что функция возвращает пустой список при некорректном JSON в файле настроек.
    """
    file_path = tmp_path / "bad.json"
    file_path.write_text("{not a json}", encoding="utf-8")
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", str(file_path)),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
    ):
        result = get_stock_prices()
        assert result == []


def test_get_stock_prices_no_api_key(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список, если API ключ не найден.
    """
    file_path, _ = user_settings
    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value=None),
    ):
        result = get_stock_prices()
        assert result == []


def test_get_stock_prices_request_error(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список если при запросе к
    API возникает ошибка (например, сеть недоступна или сервер не отвечает).
    """
    file_path, stocks = user_settings

    def fake_get(url: str, timeout: str) -> None:
        _ = url
        _ = timeout
        raise requests.exceptions.RequestException("Request failed")

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):
        result = get_stock_prices()
        assert result == []


def test_get_stock_prices_bad_response(user_settings: tuple[str, list[str]]) -> None:
    """
    Проверяет, что функция возвращает пустой список если ответ API
    не содержит ожидаемых данных (например, отсутствует ключ 'Global Quote' или '05. price').
    """
    file_path, stocks = user_settings

    def fake_get(url: str, timeout: str) -> None:
        _ = url
        _ = timeout

        def raise_for_status() -> None:
            pass

        def json_func() -> object:
            return {"bad": "data"}

        return type(
            "FakeResponse", (), {"raise_for_status": staticmethod(raise_for_status), "json": staticmethod(json_func)}
        )()

    with (
        patch("src.utils.USER_SETTINGS_PATH_STR", file_path),
        patch("src.utils.load_dotenv", lambda: None),
        patch("src.utils.os.getenv", return_value="fake_api_key"),
        patch("src.utils.requests.get", fake_get),
    ):
        result = get_stock_prices()
        assert result == []
