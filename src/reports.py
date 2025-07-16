import os
import json
import pandas as  pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.utils import excel_to_df
from dateutil.relativedelta import relativedelta

def my_decorator(function, file_name="../data/reports_data.txt"):
    """Декоратор принимает на вход имя файла, куда будет записан результат работы функции.
    При отсутствии имени, результат работу функции записывается в '.data/reports_data.txt'
    Данные, полученные после каждого вызова функции, добавляются в файл.
    """
    def inner(*args, **kwargs):
        result = str(function(*args, **kwargs))
        with open (file_name, 'a', encoding='utf-8') as file:
            file.write(f'{result}\n')
        return result
    return inner


@my_decorator
def spending_by_category(transactions_df: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> str | None:
    """Функция принимает на вход: датафрейм с транзакциями, название категории,
    опциональную дату в формате YYYY-MM-DD HH:MM:SS.
    Если дата не передана, то берется текущая дата.
    Функция возвращает траты по заданной категории за последние три месяца (от переданной даты)."""
    try:
        transactions_df["Дата операции"] = pd.to_datetime(transactions_df["Дата операции"],
                                                          format="%d.%m.%Y %H:%M:%S",
                                                          errors='coerce')
        if transactions_df["Дата операции"].isnull().any():  # Проверяем, появились ли NaN
            raise ValueError(
                "Не удалось преобразовать столбец 'Дата операции' в datetime. Убедитесь, что формат даты верен.")
        if date is None:
            date = datetime.now()

        else:
            try:
                date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError(f"Неверный формат даты: {date}. Ожидается YYYY-MM-DD HH:MM:SS")

        first_day = date - relativedelta(months=3)

        current_transactions = transactions_df[(transactions_df["Дата операции"] >= first_day) &
                                                (transactions_df["Дата операции"] <= date) &
                                                (transactions_df['Категория'] == category)]

        transactions_list = current_transactions.to_dict(orient='records')
        return json.dumps(transactions_list, default=str, ensure_ascii=False)

    except KeyError as ke:
        print(f"Ошибка: отсутствует столбец {ke} в DataFrame")
        return None

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None

if __name__ == '__main__':
    print(spending_by_category(excel_to_df("../data/operations.xlsx"), "Каршеринг", "2021-12-30 14:42:26"))


