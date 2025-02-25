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
sys.stdout.reconfigure(encoding='utf-8')

import backtrader as bt

# Стратегия скользящие средние на двух разных временных интервалах
class MovingAveragesOnDifferentTimeIntervalsStrategy(bt.Strategy):
    params = (
        ('ma_period_5min', 30),   # Период для скользящей средней на 5-минутках
        ('ma_period_hourly', 45), # Период для скользящей средней на часовом интервале
        ('trailing_stop', 0.03)   # Процент для трейлинг-стопа
    )

    def __init__(self):
        print(f"\nРасчет для параметров: {self.params.ma_period_5min} / {self.params.ma_period_hourly} / {self.params.trailing_stop}")

        # Создаем списки для хранения индикаторов по каждому инструменту
        self.ma_5min = {}
        self.ma_hourly = {}

        # Для каждого инструмента добавляем скользящие средние по разным интервалам
        for i, data in enumerate(self.datas):
            if i % 2 == 0:  # Четные индексы - 5-минутные данные
                ticker = data._name.replace('_5min', '')
                self.ma_5min[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.ma_period_5min)
            else:  # Нечетные индексы - часовые данные
                ticker = data._name.replace('_hourly', '')
                self.ma_hourly[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.ma_period_hourly)

        # Переменные для отслеживания максимальной цены после покупки по каждому инструменту
        self.buy_price = {}
        self.max_price = {}
        self.order = {}  # Словарь для отслеживания ордеров по каждому инструменту

    def next(self):
        # Для каждого инструмента проверяем условия покупки и продажи
        for i in range(0, len(self.datas), 2):  # Проходим по 5-минутным данным
            ticker = self.datas[i]._name.replace('_5min', '')
            data_5min = self.datas[i]
            data_hourly = self.datas[i + 1]

            # Проверяем, есть ли открытый ордер для этого инструмента
            if ticker in self.order and self.order[ticker]:
                continue  # Пропускаем, если есть открытый ордер

            # Проверяем условия покупки: 
            # цена на 5 мин таймфрейме выше скользящей средней на 5 мин + часовая цена тоже выше часовой скользящей средней
            if not self.getposition(data_5min):  # Открываем сделку только если нет открытой позиции
                if data_5min.close[0] > self.ma_5min[ticker][0] and data_hourly.close[0] > self.ma_hourly[ticker][0]:
                    self.order[ticker] = self.buy(data=data_5min)
                    self.buy_price[ticker] = data_5min.close[0]
                    self.max_price[ticker] = self.buy_price[ticker]

                    # Получаем текущий тикер и дату покупки
                    buy_date = data_5min.datetime.date(0)
                    buy_time = data_5min.datetime.time(0)
                    print(f"{buy_date} в {buy_time}: покупка за {self.buy_price[ticker]} для {ticker}")

            # Если уже есть открытая позиция
            elif self.getposition(data_5min):
                current_price = data_5min.close[0]

                # Обновляем максимальную цену, если текущая выше
                if current_price > self.max_price[ticker]:
                    self.max_price[ticker] = current_price

                # Рассчитываем уровень стоп-лосса
                stop_loss_level = self.max_price[ticker] * (1 - self.params.trailing_stop)

                # Проверяем условие для продажи по трейлинг-стопу
                if current_price < stop_loss_level:
                    self.order[ticker] = self.sell(data=data_5min)
                    sell_date = data_5min.datetime.date(0)
                    sell_time = data_5min.datetime.time(0)
                    print(f"{sell_date} в {sell_time}: продажа за {current_price} для {ticker}")

    # Обрабатываем уведомления по ордерам
    def notify_order(self, order):
        ticker = order.data._name.replace('_5min', '')

        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order[ticker] = None  # Очищаем ордер после завершения
