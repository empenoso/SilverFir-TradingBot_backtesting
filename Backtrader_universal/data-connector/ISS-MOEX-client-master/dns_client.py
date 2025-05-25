"""Асинхронный клиент для MOEX ISS."""
from collections.abc import AsyncIterable, AsyncIterator
from typing import cast
from datetime import datetime

import aiohttp
from aiohttp import client_exceptions
import asyncio
import socket
from aiomoex.client import ISSClient, ISSMoexError, Table, TablesDict, WebQuery


class DNS_ISSClient(ISSClient):
    """Асинхронный клиент для MOEX ISS - может быть использован с async for.

    Загружает данные для простых ответов с помощью метода get. Для ответов состоящих из нескольких блоков
    поддерживается протокол асинхронного генератора отдельных блоков или метод get_all для их
    автоматического сбора.
    """

    async def get(self, start: int | None = None) -> TablesDict:
        """Загрузка данных.

        :param start:
            Номер элемента с которого нужно загрузить данные. Используется для дозагрузки данных,
            состоящих из нескольких блоков. При отсутствии данные загружаются с начального элемента.

        :return:
            Блок данных с отброшенной вспомогательной информацией - словарь, каждый ключ которого
            соответствует одной из таблиц с данными. Таблицы являются списками словарей, которые напрямую
            конвертируются в pandas.DataFrame.
        :raises ISSMoexError:
            Ошибка при обращении к ISS Moex.
        """
        url = self._url
        query = self._make_query(start)
        print(f"{datetime.now()}: DNS_ISSClient.get.url: {url}")
        for dns_server in ['77.88.8.1', '8.8.8.8', ]:
            connector = None
            try:
                resolver = aiohttp.resolver.AsyncResolver(nameservers=[dns_server])
                connector = aiohttp.TCPConnector(resolver=resolver)
                self._session._connector = connector
                async with self._session.get(url, params=query) as response:
                    try:
                        response.raise_for_status()
                    except client_exceptions.ClientResponseError as err:
                        raise ISSMoexError("Неверный url", result.url) from err
                    else:
                        result = await response.json()
                        return result[1]
            except (aiohttp.ClientError, socket.gaierror) as e:
                print(f"Failed to make a request to '{url}' using DNS server '{dns_server}'. Error: {e}")
                continue
            finally:
                if connector and not connector.closed:
                    await connector.close()
        return None

