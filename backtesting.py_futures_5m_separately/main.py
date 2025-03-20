# pip install -r requirements.txt

# Запускает сканирование и тестирование

# Подробнее о моих поисках торговых стратегий в статьях на Хабре и Смартлабе: 
# https://github.com/empenoso/SilverFir-TradingBot_backtesting

import asyncio
from backtester import run_backtest

async def main():
    top_futures = ["CRH5", "NGH5", "SiH5", "RIH5"]

    for ticker in top_futures:
        await run_backtest(ticker)

if __name__ == "__main__":
    asyncio.run(main())
