# Определяет топ-20 акций по объему в рублях за последние 14 дней

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import aiomoex
from data_loader import fetch_moex_data

async def get_tqbr_securities():
    """Получает список всех бумаг из TQBR."""
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json"
    query = {"iss.meta": "off", "iss.only": "marketdata", "marketdata.columns": "SECID"}

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            iss_client = aiomoex.ISSClient(session, url, query)
            data = await iss_client.get()

            if not data or "marketdata" not in data:
                return []

            df = pd.DataFrame(data["marketdata"])
            return df["SECID"].tolist() if "SECID" in df.columns else []

    except Exception:
        return []


async def get_top_20_stocks():
    """
    Определяет топ-20 акций по сумме объемов торгов за последние 14 дней.

    Returns:
        pandas.DataFrame: DataFrame с топ-20 акциями, отсортированными по суммарному объему.
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Получаем список всех тикеров
    print("Получение списка акций на TQBR...")
    tickers = await get_tqbr_securities()

    if not tickers:
        raise ValueError("Не удалось получить список акций")

    print(f"Получено {len(tickers)} акций. Загрузка данных об объемах за 14 дней...")

    # Словарь для хранения данных об объемах
    volumes_data = {}

    # Асинхронная загрузка данных для всех тикеров
    tasks = [fetch_moex_data(ticker, timeframe="D", days=14) for ticker in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обработка результатов
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            print(f"Ошибка при загрузке данных для {ticker}: {result}")
            continue

        df, _, _ = result

        if "Volume" not in df.columns or df.empty:
            print(f"Нет данных об объемах для {ticker}")
            continue

        # Суммируем объем за последние 14 дней
        total_volume = df["Volume"].sum()

        if total_volume > 0:
            volumes_data[ticker] = {
                "Ticker": ticker,
                "TotalVolume": total_volume / 1e9,  # Перевод в миллиарды
            }

    if not volumes_data:
        raise ValueError("Не удалось получить данные об объемах ни для одной акции")

    # Создаем DataFrame из собранных данных
    volumes_df = pd.DataFrame(volumes_data.values())

    # Сортируем по объему и берем топ-20
    top_20 = volumes_df.sort_values(by="TotalVolume", ascending=False).head(20).reset_index(drop=True)

    print(f"\nГотово! Топ-20 акций по суммарному объему за 14 дней:")
    print(top_20)

    return top_20['Ticker'].tolist()

# async def main():
#     top_stocks = await get_top_20_stocks()
#     print("\nТоп-20 акций по объему (млрд рублей):")
#     print(top_stocks)

# if __name__ == "__main__":
#     asyncio.run(main())
