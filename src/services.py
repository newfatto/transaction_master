import json
import logging
import re

from pandas import DataFrame

logger = logging.getLogger(__name__)


def search_money_transfer_to_people(transactions_df: DataFrame) -> str:
    """
    Функция принимает DataFrame с данными об операциях и ищет переводы денег физическим лицам, если в описании
    указано имя в формате "Имя Ф.". Возвращает JSON объект с данными о подходящих транзакциях.
    """
    logger.debug(logger.info("Запущен поиск переводов физическим лицам"))
    try:
        if not isinstance(transactions_df, DataFrame):
            logger.error("Входной параметр не является DataFrame")
            raise TypeError("Входной параметр должен быть DataFrame")

        if "Категория" not in transactions_df.columns or "Описание" not in transactions_df.columns:
            logger.error("DataFrame должен содержать столбцы 'Категория' и 'Описание'")
            raise KeyError("DataFrame должен содержать столбцы 'Категория' и 'Описание'")

        pattern = re.compile(r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.")
        money_transfers = transactions_df[transactions_df["Категория"] == "Переводы"]
        filtered_transfers = money_transfers[money_transfers["Описание"].str.contains(pattern, regex=True, na=False)]
        filtered_transfers = filtered_transfers.apply(lambda x: x.astype(str) if x.dtype == "datetime64[ns]" else x)
        result = filtered_transfers.to_dict(orient="records")

        logger.info(f"Найдено переводов физическим лицам: {len(result)}")

        return json.dumps(result, ensure_ascii=False, indent=4)  # Добавлено форматирование для читабельности

    except TypeError as e:
        error_message = f"Ошибка типа данных: {e}"
        logger.error(error_message)
        return json.dumps({"error": error_message}, ensure_ascii=False)
    except KeyError as e:
        error_message = f"Ошибка: Отсутствует столбец: {e}"
        logger.error(error_message)
        return json.dumps({"error": error_message}, ensure_ascii=False)
    except Exception as e:
        error_message = f"Произошла непредвиденная ошибка: {e}"
        logger.error(error_message)
        return json.dumps({"error": error_message}, ensure_ascii=False)
