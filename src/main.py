from datetime import datetime

import pandas as pd

from config import EXCEL_FILE_PATH_STR
from src.reports import spending_by_category
from src.services import search_money_transfer_to_people
from src.utils import excel_to_df
from src.views import general_page_function


def main() -> None:
    print("Рады приветствовать!")
    while True:
        user_input = input(
            "Вы находитесь в главном меню приложения, анализирующего транзакции.\n\n"
            "Выберите раздел, в который хотите переместиться:\n\n"
            "1. Главная страница\n"
            "2. Сервисы\n"
            "3. Отчёты\n"
            "0. Выйти из приложения\n\n"
            "Введите 1, 2, 3 или 0: "
        )
        if user_input == "1":
            user_date_for_general_page = input("Введите дату в формате YYYY-MM-DD HH:MM:SS : ")
            try:
                datetime.strptime(user_date_for_general_page, "%Y-%m-%d %H:%M:%S")
                general_page = general_page_function(user_date_for_general_page)
                print(f"\n{general_page['greeting']}\n\n" "Ваши карты:\n")
                for card in general_page["cards"]:
                    print(
                        f"Последние цифры: {card['last_digits']} "
                        f"Расходы за этот месяц: {card['total_spent']} "
                        f"Кешбек: {card['cashback']}"
                    )
                print(
                    f"Топ-5 транзакций по сумме платежа: \n{general_page['top_transactions']}\n\n"
                    f"Курс валют: \n{general_page['currency_rates']}\n"
                    f'Стоимость акций: \n{general_page["stock_prices"]}\n\n'
                )
            except ValueError:
                print("Неправильный формат даты\n")
        elif user_input == "2":
            while True:
                user_input = input(
                    'Вы находитесь в разделе "Сервисы"\n'
                    "В настоящий момент доступны сервисы:\n"
                    "1. Поиск переводов физическим лицам\n\n"
                    "*. Выход в главное меню\n"
                    "0. Выход из программы\n\n"
                    "Введите 1, * или 0: "
                )
                if user_input == "1":
                    print(search_money_transfer_to_people(excel_to_df(EXCEL_FILE_PATH_STR)))
                    break
                if user_input == "*":
                    break
                elif user_input == "0":
                    break
                elif user_input not in ["1", "*", "0"]:
                    print("Неверный ввод\n")
        elif user_input == "3":
            while True:
                user_input = input(
                    'Вы находитесь в разделе "Отчёты"\n'
                    "В настоящий момент доступны отчёты:\n"
                    "1. Отчёт по тратам в категории за 3 месяца, предшествующих дате\n\n"
                    "*. Выход в главное меню\n"
                    "0. Выход из программы\n\n"
                    "Введите 1, * или 0: "
                )
                if user_input == "1":
                    df = excel_to_df(EXCEL_FILE_PATH_STR)
                    categories = df["Категория"].unique()
                    print(f"Вам доступны следующие категории: {categories}")
                    user_category = str(input("Введите название категории: "))
                    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True)
                    print(
                        f"Вам доступны данные в период с {df['Дата платежа'].min().strftime('%Y-%m-%d %H:%M:%S')} по "
                        f"{df['Дата платежа'].max().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    user_date_for_report = input("Введите дату в формате YYYY-MM-DD HH:MM:SS : ")
                    try:
                        datetime.strptime(user_date_for_report, "%Y-%m-%d %H:%M:%S")

                        if user_category in categories:
                            report_data = spending_by_category(df, user_category, user_date_for_report)
                            print(report_data)
                            break
                        else:
                            print("Указанной категории не существует.\n")
                    except ValueError:
                        print("Неправильный формат даты\n")
                if user_input == "*":
                    break
                elif user_input == "0":
                    break
                elif user_input not in ["1", "*", "0"]:
                    print("Неверный ввод\n")
        elif user_input == "0":
            break
        elif user_input not in ["1", "2", "3", "0"]:
            print("Неверный ввод\n")


if __name__ == "__main__":
    main()
