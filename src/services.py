from src.utils import excel_to_list
from pandas import DataFrame
import re
import json

def search_money_transfer_to_people(operations_list: DataFrame) -> str:
    """
        Ищет в DataFrame переводы денег людям, чье имя указано в описании в формате "Имя Ф.".
        Возвращает JSON объект с данными о подходящих транзакциях.

        Args:
            operations_list: DataFrame с данными об операциях.

        Returns:
            JSON строка, представляющая список словарей с данными о транзакциях,
            соответствующих критериям.
            В случае ошибки возвращает JSON с ключом "error" и сообщением об ошибке.
        """
    try:
        if not isinstance(operations_list, DataFrame):
            raise TypeError("Входной параметр должен быть DataFrame")

        if 'Категория' not in operations_list.columns or 'Описание' not in operations_list.columns:
            raise KeyError(
                "DataFrame должен содержать столбцы 'Категория' и 'Описание'")

        pattern = re.compile(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.')
        money_transfers = operations_list[operations_list['Категория'] == "Переводы"]
        filtered_transfers = money_transfers[money_transfers['Описание'].str.contains(pattern, regex=True, na=False)]
        filtered_transfers = filtered_transfers.apply(lambda x: x.astype(str) if x.dtype == 'datetime64[ns]' else x)
        result = filtered_transfers.to_dict(orient="records")

        return json.dumps(result, ensure_ascii=False, indent=4)  # Добавлено форматирование для читабельности

    except TypeError as e:
        error_message = f"Ошибка типа данных: {e}"
        return json.dumps({"error": error_message}, ensure_ascii=False)
    except KeyError as e:
        error_message = f"Ошибка: Отсутствует столбец: {e}"
        return json.dumps({"error": error_message}, ensure_ascii=False)
    except Exception as e:
        error_message = f"Произошла непредвиденная ошибка: {e}"
        return json.dumps({"error": error_message}, ensure_ascii=False)


if __name__ == '__main__':
    print(search_money_transfer_to_people(excel_to_list("../data/operations.xlsx", "2020-10-26 14:42:26")))