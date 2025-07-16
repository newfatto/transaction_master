from src.views import general_page_function
from services import search_money_transfer_to_people
from reports import spending_by_category
from datetime import datetime
from src.utils import excel_to_df
import pandas as pd

def main():
    print("Рады приветствовать!")
    user_path_to_excel = "../data/operations.xlsx"
    while True:
        user_input = input('Вы находитесь в главном меню приложения, анализирующего транзакции.\n\n'
                           'Выберите раздел, в который хотите переместиться:\n\n'
                           '1. Главная страница\n'
                           '2. Сервисы\n'
                           '3. Отчёты\n'
                           '0. Выйти из приложения\n\n'
                           'Введите 1, 2, 3 или 0: ')
        if user_input == "1":
            user_date_for_general_page = input('Введите дату в формате YYYY-MM-DD HH:MM:SS : ')
            while True:
                if datetime.strptime(user_date_for_general_page, "%Y-%m-%d %H:%M:%S"):
                    general_page = general_page_function(user_date_for_general_page)
                    print(f'\n{general_page['greeting']}\n\n'
                          'Ваши карты:\n')
                    for card in general_page['cards']:
                        print(f'Последние цифры: {card['last_digits']} '
                              f'Расходы за этот месяц: {card['total_spent']} '
                              f'Кешбек: {card['cashback']}')
                    print(f'Топ-5 транзакций по сумме платежа: \n{general_page['top_transactions']}\n\n'
                          f'Курс валют: \n{general_page['currency_rates']}\n'
                          f'Стоимость акций: \n{general_page["stock_prices"]}\n\n')
                    break
                else:
                    "Неправильный формат даты\n"
        elif user_input == "2":
            while True:
                user_input = input('Вы находитесь в разделе "Сервисы"\n'
                                   'В настоящий момент доступны сервисы:\n'''
                                   '1. Поиск переводов людям\n\n'
                                   '*. Выход в главное меню\n'
                                   '0. Выход из программы\n\n'
                                   'Введите 1, * или 0: ')
                if user_input == "1":
                    print(search_money_transfer_to_people(excel_to_df(user_path_to_excel)))
                    break
                if user_input == "*":
                    break
                elif user_input == "0":
                    break
                elif user_input not in ['1', '*', '0']:
                    print('Неверный ввод\n')
        elif user_input == "3":
            while True:
                user_input = input('Вы находитесь в разделе "Отчёты"\n'
                                   'В настоящий момент доступны отчёты:\n'''
                                   '1. Отчёт по тратам в категории за 3 месяца, предшествующих дате\n\n'
                                   '*. Выход в главное меню\n'
                                   '0. Выход из программы\n\n'
                                   'Введите 1, * или 0: ')
                if user_input == "1":
                    categories = excel_to_df(user_path_to_excel)['Категория'].unique()
                    print(f"Вам доступны следующие категории: {categories}")
                    user_category = str(input('Введите название категории: '))
                    user_date_for_report = input('Введите дату в формате YYYY-MM-DD HH:MM:SS : ')
                    while True:
                        if (datetime.strptime(user_date_for_report, "%Y-%m-%d %H:%M:%S") and
                                user_category in categories):
                            print(spending_by_category(excel_to_df(user_path_to_excel),
                                                       user_category,
                                                       user_date_for_report))
                            break
                        else:
                            print('Неверный ввод\n')
                if user_input == "*":
                    break
                elif user_input == "0":
                    break
                elif user_input not in ['1', '*', '0']:
                    print('Неверный ввод\n')

        if user_input == "0":
            break

        elif user_input not in ['1', '2', '3', '0']:
            print('Неверный ввод\n')

    print('Благодарим за использование. Приходите ещё.')


main()
