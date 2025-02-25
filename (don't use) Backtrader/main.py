# ==============================================================================
# Project Name:        SilverFir-TradingBot_backtesting
# Repository:          https://github.com/empenoso/SilverFir-TradingBot_backtesting
# Author:              Mikhail Shardin, https://shardin.name/
# Created Date:        2024-10-25
# Last Modified Date:  2024-11-13
# Description:         https://habr.com/ru/articles/857402/
# Version:             1.0
# License:             Apache 2.0
# ==============================================================================

import sys
import time
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from src.data_loader import load_data_for_ticker, load_ticker_mapping

import pandas as pd
import backtrader as bt
import backtrader.analyzers as btanalyzers

from src.strategy0_ma_5min_hourly import MovingAveragesOnDifferentTimeIntervalsStrategy

# отобразить имена всех столбцов в большом фреймворке данных pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Начало времени
start_time = time.perf_counter()

# Путь к JSON файлу с сопоставлениями
mapping_file = "./data/+mappings.json"

# Загрузка сопоставлений тикеров
ticker_mapping = load_ticker_mapping(mapping_file)

# Промежуточное время выполнения
total_end_time = time.perf_counter()
elapsed_time = total_end_time - start_time
print(f"Промежуточное время выполнения: {elapsed_time:.4f} секунд.")

current_time = datetime.now().strftime("%Y-%m-%d %H-%M") # Генерируем текущее время в формате 'yyyy-mm-dd HH-mm'

# Следующая часть кода запускается только если это основной модуль
if __name__ == '__main__':  # Исправление для работы с multiprocessing

    # Создаем объект Cerebro
    cerebro = bt.Cerebro(optreturn=False)    

    # Получаем количество бумаг в ticker_mapping.items()
    num_securities = len(ticker_mapping.items())

    # Рассчитываем процент капитала на одну бумагу
    percent_per_security = 100 / num_securities
    print(f"Процент капитала на одну бумагу: {percent_per_security:.2f}%")

    # Условия капитала
    cerebro.broker.set_cash(100000)  # Устанавливаем стартовый капитал
    cerebro.broker.setcommission(commission=0.005)  # Комиссия 0.5%
    cerebro.addsizer(bt.sizers.PercentSizer, percents=percent_per_security)  # Настраиваем размер позиций как процент от капитала

    # Для каждого инструмента добавляем оба временных интервала
    for uid, ticker in ticker_mapping.items():
        print(f"Загружаем данные для {ticker}")

        # Загрузка данных с таймфреймами 5 минут и час
        data_5min, data_hourly = load_data_for_ticker(ticker)

        # Пропуск, если данные не были загружены
        if data_5min is None or data_hourly is None:
            continue

        # Добавляем 5-минутные данные в Cerebro
        data_5min_bt = bt.feeds.PandasData(dataname=data_5min, timeframe=bt.TimeFrame.Minutes, compression=5)
        cerebro.adddata(data_5min_bt, name=f"{ticker}_5min")

        # Добавляем часовые данные в Cerebro
        data_hourly_bt = bt.feeds.PandasData(dataname=data_hourly, timeframe=bt.TimeFrame.Minutes, compression=60)

        # Совмещаем графики 5 минут и часа на одном виде
        data_hourly_bt.plotinfo.plotmaster = data_5min_bt  # Связываем графики
        data_hourly_bt.plotinfo.sameaxis = True            # Отображаем на той же оси
        cerebro.adddata(data_hourly_bt, name=f"{ticker}_hourly")


    # Переключатель одиночный тест или оптимизация
    SingleTestOrOptimization = "optimization" # singleTest / optimization

    if SingleTestOrOptimization == "singleTest":
        print(f"{current_time} Проводим одиночный тест стратегии.")

        # Добавляем стратегию для одичного теста MovingAveragesOnDifferentTimeIntervalsStrategy
        cerebro.addstrategy(MovingAveragesOnDifferentTimeIntervalsStrategy, 
                      ma_period_5min = 30,    # Период для скользящей средней на 5-минутках
                      ma_period_hourly = 45,  # Период для скользящей средней на часовом интервале
                      trailing_stop = 0.03)   # Процент для трейлинг-стопа

        # Writer только для одиночного теста для вывода результатов в CSV-файл    
        cerebro.addwriter(bt.WriterFile, csv=True, out=f"./results/{current_time}_log.csv")
        
        # Добавляем анализаторы
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trade_analyzer')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, riskfreerate=10) 
        cerebro.addanalyzer(btanalyzers.SQN, _name='sqn')
        cerebro.addanalyzer(btanalyzers.PyFolio, _name='PyFolio') 

        # Запуск тестирования
        results = cerebro.run(maxcpus=1)  # Ограничение одним ядром для избежания многопроцессорности
        
        # Выводим результаты анализа одиночного теста
        print(f"\nОкончательная стоимость портфеля: {cerebro.broker.getvalue()}")
        returnsAnalyzer = results[0].analyzers.returns.get_analysis()
        print(f"Годовая/нормализованная доходность: {returnsAnalyzer['rnorm100']}%")
        drawdownAnalyzer = results[0].analyzers.drawdown.get_analysis()
        print(f"Максимальное значение просадки: {drawdownAnalyzer['max']['drawdown']}%")
        trade_analyzer = results[0].analyzers.trade_analyzer.get_analysis()
        print(f"Всего сделок: {trade_analyzer.total.closed} шт.")
        print(f"Выигрышные сделки: {trade_analyzer.won.total} шт.")
        print(f"Убыточные сделки: {trade_analyzer.lost.total} шт.")
        sharpe_ratio = results[0].analyzers.sharpe_ratio.get_analysis().get('sharperatio')
        print(f"Коэффициент Шарпа: {sharpe_ratio}")
        sqnAnalyzer = results[0].analyzers.sqn.get_analysis().get('sqn')
        print(f"Мера доходности с поправкой на риск: {sqnAnalyzer}")
       
        # Время выполнения
        total_end_time = time.perf_counter()
        elapsed_time = (total_end_time - start_time) / 60
        print(f"\nВремя выполнения: {elapsed_time:.4f} минут.")
        
        # Построение графика для одиночного теста
        cerebro.plot()


    else:
        print(f"{current_time} Проводим оптимизацию статегии.")

        # Оптимизация стратегии start_date = 2024-10_MovingAveragesOnDifferentTimeIntervalsStrategy
        cerebro.optstrategy(MovingAveragesOnDifferentTimeIntervalsStrategy, 
                        ma_period_5min=range(10, 61, 5),    # Диапазон для 5-минутной скользящей средней
                        ma_period_hourly=range(15, 61, 2),   # Диапазон для часовой скользящей средней
                        trailing_stop=[0.03])               # Разные проценты для трейлинг-стопа 0.03, 0.05, 0.07
        print(f"\nКоличество варинатов оптимизации: {(( (61-10)/10 * (61-15))/2 )}\n")

        # Добавляем анализаторы
        cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trade_analyzer')
        cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, riskfreerate=10) 
        cerebro.addanalyzer(btanalyzers.SQN, _name='sqn')

        # Запуск тестирования
        results = cerebro.run(maxcpus=1)  # Ограничение одним ядром для избежания многопроцессорности для оптимизации

        # Выводим результаты оптимизации
        par_list = [ [
                    # MovingAveragesOnDifferentTimeIntervalsStrategy
                    x[0].params.ma_period_5min, 
                	x[0].params.ma_period_hourly,
                    x[0].params.trailing_stop,

                	x[0].analyzers.trade_analyzer.get_analysis().pnl.net.total,
                	x[0].analyzers.returns.get_analysis()['rnorm100'], 
                	x[0].analyzers.drawdown.get_analysis()['max']['drawdown'],
                	x[0].analyzers.trade_analyzer.get_analysis().total.closed,
                	x[0].analyzers.trade_analyzer.get_analysis().won.total,
                	x[0].analyzers.trade_analyzer.get_analysis().lost.total,
                	x[0].analyzers.sharpe_ratio.get_analysis()['sharperatio'],
                	x[0].analyzers.sqn.get_analysis().get('sqn')
                ] for x in results]
        
        # MovingAveragesOnDifferentTimeIntervalsStrategy
        par_df = pd.DataFrame(par_list, columns = ['ma_period_5min', 'ma_period_hourly', 'trailing_stop', 'pnl net', 'return', 'drawdown', 'total closed', 'won total', 'lost total', 'sharpe', 'sqn'])

        # Формируем имя файла с текущей датой и временем
        filename = f"./results/{current_time}_optimization.csv"
        # Сохраняем DataFrame в CSV файл с динамическим именем
        par_df.to_csv(filename, index=False)
        print(f"\n\nРезультаты оптимизации:\n{par_df}")

        # Время выполнения
        total_end_time = time.perf_counter()
        elapsed_time = (total_end_time - start_time) / 60
        print(f"\nВремя выполнения: {elapsed_time:.4f} минут.")


    # Общее время выполнения
    total_end_time = time.perf_counter()
    elapsed_time = (total_end_time - start_time) / 60
    print(f"\nОбщее время выполнения: {elapsed_time:.4f} минут.")