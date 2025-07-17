from src.utils import excel_to_df
from pandas import DataFrame
import re
import json

def search_money_transfer_to_people(transactions_df: DataFrame) -> str:
    """
        Ищет в DataFrame переводы денег людям, если в описании указано имя в формате "Имя Ф.".
        Возвращает JSON объект с данными о подходящих транзакциях.

        Args:
            transactions_df: DataFrame с данными об операциях.

        Returns:
            JSON строка, представляющая список словарей с данными о транзакциях,
            соответствующих критериям.
            В случае ошибки возвращает JSON с ключом "error" и сообщением об ошибке.
        """
    try:
        if not isinstance(transactions_df, DataFrame):
            raise TypeError("Входной параметр должен быть DataFrame")

        if 'Категория' not in transactions_df.columns or 'Описание' not in transactions_df.columns:
            raise KeyError(
                "DataFrame должен содержать столбцы 'Категория' и 'Описание'")

        pattern = re.compile(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.')
        money_transfers = transactions_df[transactions_df['Категория'] == "Переводы"]
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
    print(search_money_transfer_to_people(excel_to_df("../data/operations.xlsx")))