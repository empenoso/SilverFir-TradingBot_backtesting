# Отвечает за загрузку данных с Мосбиржи

import pandas as pd
import aiohttp
from datetime import datetime, timedelta
import aiomoex
import asyncio

async def fetch_moex_data(ticker, timeframe='D', days=1825):
    """
    Асинхронная загрузка свечных данных с Московской биржи через aiomoex.
    """
    # Определяем конечную и начальную даты
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Приводим к строковому формату YYYY-MM-DD
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # Маппинг интервалов
    interval_map = {'D': 24, 'W': 7, 'H': 60, 'M': 31}
    interval = interval_map.get(timeframe, 24)  # По умолчанию дневные свечи

    print(f"📊 Загружаем данные для {ticker} с {start_str} по {end_str} (таймфрейм: {timeframe})")

    async with aiohttp.ClientSession() as session:
        # Запрашиваем свечные данные
        data = await aiomoex.get_market_candles(
            session,
            security=ticker,
            interval=interval,
            start=start_str,
            end=end_str
        )

    # Проверяем, есть ли данные
    if not data:
        raise ValueError(f"❌ Не удалось получить данные для {ticker} за последние {days} дней")

    # Создаем DataFrame
    df = pd.DataFrame(data)

    # Переименовываем колонки
    column_mapping = {
        'begin': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'value': 'Volume' # если volume, то объём торгов в штуках
    }
    df = df.rename(columns=column_mapping)

    # Преобразуем дату в datetime и ставим индекс
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # Оставляем только нужные столбцы
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

    print(f"✅ Загружено {len(df)} свечей для {ticker}")

    return df, start_str, end_str  # Возвращаем start_str и end_str


# Простой тест для fetch_moex_data

async def test_fetch_moex_data_output_simple(ticker='SBER', timeframe='D', days=30):
    try:
        df, start_str, end_str = await fetch_moex_data(ticker, timeframe, days)

        # Проверяем, что возвращается DataFrame
        if not isinstance(df, pd.DataFrame):
            print("❌ Ошибка: Функция не вернула pandas DataFrame")
            return False

        # Проверяем, что DataFrame не пустой
        if df.empty:
            print("❌ Ошибка: DataFrame пустой")
            return False

        # Выводим первые 15 строк
        print(f"\nПервые 15 строк DataFrame для {ticker}:")
        print(df.head(15))

        # Выводим последние 15 строк
        print(f"\nПоследние 15 строк DataFrame для {ticker}:")
        print(df.tail(15))

        # Выводим типы данных
        print(f"\nТипы данных DataFrame для {ticker}:")
        print(df.dtypes)
        
        print(f"\n✅ Тест пройден для {ticker} с {start_str} по {end_str}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при выполнении теста для {ticker}: {e}")
        return False

# Запускаем тест
if __name__ == "__main__":
    asyncio.run(test_fetch_moex_data_output_simple())