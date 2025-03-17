# Запуск бэктеста

import asyncio
import pandas as pd
from backtesting import Backtest
from data_loader import load_data_for_ticker
from strategy_Random_1min import RandomEntryStrategy

async def run_backtest(ticker):
    print(f"\n{'='*50}")
    print(f"🚀 Запуск бэктеста для {ticker}")
    print(f"{'='*50}\n")

    # Получаем данные
    df = load_data_for_ticker(ticker) # Получаем start_str и end_str

    if df is None or df.empty:
        raise ValueError("❌ Ошибка: данные не загружены")

    # Информация о данных (для отладки)
    print("\n📋 Технические данные (для справки):")
    print(f"Колонки в данных: {list(df.columns)}")
    print(f"Первые 5 строк данных:")
    print(df.head())
    print(f"Типы данных:")
    print(df.dtypes)
    print("\n")

    # Проверяем, что все необходимые колонки существуют
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"❌ В данных отсутствуют необходимые колонки: {missing}")

    # Запускаем бэктест
    print("⏳ Запуск бэктеста...")
    strategy_class = RandomEntryStrategy # Класс стратегии остается прежним
    strategy_name = f"{ticker}_RandomEntryStrategy" # Динамическое имя
    DynamicStrategyClass = type(strategy_name, (strategy_class,), {}) # Создаем динамический класс стратегии

    # bt = Backtest(df, DynamicStrategyClass, cash=100_000, commission=0.002) 
    bt = Backtest(
        df,
        DynamicStrategyClass,
        cash=1_000_000, 
        commission=0.002,
        margin=0.1,  # Требование к первоначальной марже 10%
        trade_on_close=True,
        hedging=False,  
    )
    
    stats = bt.run()

    # Вывод результатов
    print("\n📊 Результаты бэктеста:")
    print(f"⚙️ Стратегия: {strategy_name}") # Выводим динамическое имя стратегии
    print(f"📅 Период тестирования: с {stats['Start']} по {stats['End']}")
    print(f"💰 Начальный капитал: 100,000 руб.")
    print(f"💵 Конечный капитал: {stats['Equity Final [$]']:.2f} руб.")
    print(f"📈 Общая доходность: {stats['Return [%]']:.2f}%")
    print(f"📊 Годовая доходность: {stats['Return (Ann.) [%]']:.2f}%") 
    print(f"📈 Коэффициент Шарпа: {stats['Sharpe Ratio']:.2f}") 
    print(f"📉 Максимальная просадка: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"🔄 Количество сделок: {stats['# Trades']}")
    print(f"✅ Процент выигрышных сделок: {stats['Win Rate [%]']:.2f}%")
    print(f"💪 Лучшая сделка: +{stats['Best Trade [%]']:.2f}%")
    print(f"🙁 Худшая сделка: {stats['Worst Trade [%]']:.2f}%")
    print(f"⏱️ Средняя продолжительность сделки: {stats['Avg. Trade Duration']}")
    # Построение графика
    print("\n📊 Построение графика результатов...")
    try:
        bt.plot()
        print("✅ График успешно построен!")
    except ValueError as e:
        print(f"❌ Ошибка при построении графика: {e}")
        print("💡 Совет: Попробуйте обновить bokeh с помощью команды 'pip install --upgrade bokeh'")
    print(f"\n{'='*50}")
    print(f"🏁 Бэктест для {ticker} завершен")
    print(f"{'='*50}\n")
    return stats