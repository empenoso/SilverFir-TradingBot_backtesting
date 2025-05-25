import asyncio
import aiohttp
import pandas as pd
import numpy as np
from db_functions import load_table, load_all_sec
from constants import ALL_CATALOGS
from dns_client import DNS_ISSClient
import aiomoex

aiomoex.ISSClient = DNS_ISSClient


"""
Содержание:
1. Функция для загрузки Справочников MOEX.
2. Функция для загрузки всех бумаг с MOEX.
"""


# 1. Функция для загрузки Справочников MOEX.
async def get_catalogs(placeholder: list = ALL_CATALOGS):
    for tbl in placeholder:
        async with aiohttp.ClientSession() as session:
            """
            Справочники MOEX: 
            engines, markets, boards, boardgroups, durations, securitytypes, securitygroups, securitycollections.
            Наименование нужного (обновляемого в БД) Справочника помещаем в переменную placeholder при запуске.
            Все Справочники можно посмотреть здесь: https://iss.moex.com/iss/index
            """
            data = await aiomoex.get_reference(session, placeholder=tbl)
            df = pd.DataFrame(data)
            df.replace({np.nan: None}, inplace=True)
            # Для тестирования:
            # print(df.head(), '\n')
            # print(df.tail(), '\n')
            # print(df.iloc[0])
            # print(df.columns.tolist())
            # df.info()

        load_table(tbl, df)


#2. Функция для загрузки всех бумаг с MOEX.
async def get_all_securities():
    async with aiohttp.ClientSession() as session:
        """
        MOEX выдает все бумаги в ответах по 100 штук. Чтобы объединить все ответы в один
        df, используем функцию iss.get_all(). Загрузка продолжается около 2,5 часов.
        04-01-2024 выгружено 608K+ бумаг, торгуемых или когда либо торговавшихся на MOEX.
        Пример ответа MOEX можно посмотреть здесь:
        https://iss.moex.com/iss/securities.xml?start=600000
        start=600000 - стартовая позиция, взята с потолка для примера.
        """
        request_url = "https://iss.moex.com/iss/securities.json"
        arguments = None
        iss = aiomoex.ISSClient(session, request_url, arguments)
        data = await iss.get_all()
        df = pd.DataFrame(data["securities"])
        df.replace({np.nan: None}, inplace=True)
        # Для тестирования:
        print(df.head(), "\n")
        print(df.tail(), "\n")
        df.info()

    load_all_sec(df)


# !!! Если работаем в Windows - раскомментируйте это тоже:
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#  1. Запуск функции для загрузки Справочников MOEX. Примеры:
# Справочники MOEX: engines, markets, boards, boardgroups, durations,
# securitytypes, securitygroups, securitycollections.

asyncio.run(get_catalogs()) # все справочники разом

#  2. Запуск функции для загрузки всех бумаг с MOEX. Запускаем только после загрузки всех справочников по п.1,
# т.к. они нужны для создания одной из таблиц БД. Занимает от 2 до 4 часов

asyncio.run(get_all_securities())




