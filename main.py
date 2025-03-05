# pip install -r requirements.txt

# Запускает сканирование и тестирование

import asyncio
from scanner import get_top_20_stocks
from backtester import run_backtest

async def main():
    top_stocks = await get_top_20_stocks()

    for ticker in top_stocks:
        await run_backtest(ticker)

if __name__ == "__main__":
    asyncio.run(main())
