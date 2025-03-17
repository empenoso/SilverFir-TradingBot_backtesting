import sys
sys.stdout.reconfigure(encoding='utf-8')

import backtrader as bt
import numpy as np  # Используем numpy для векторных операций

# Оптимизированная стратегия со скользящими средними на разных временных интервалах
class MovingAveragesOnDifferentTimeIntervalsStrategy(bt.Strategy):
    params = (
        ('ma_period_5min', 30),   # Период для скользящей средней на 5-минутках
        ('ma_period_hourly', 45), # Период для скользящей средней на часовом интервале
        ('trailing_stop', 0.03)   # Процент для трейлинг-стопа
    )

    def __init__(self):
        print(f"\nОптимизация для параметров: {self.params.ma_period_5min} / {self.params.ma_period_hourly} / {self.params.trailing_stop}")

        # Предварительный расчет скользящих средних по всем данным для минимизации вычислений в цикле
        self.ma_5min = {}
        self.ma_hourly = {}

        # Используем векторные операции для всех инструментов
        for i, data in enumerate(self.datas):
            ticker = data._name.replace('_5min', '') if i % 2 == 0 else data._name.replace('_hourly', '')
            if i % 2 == 0:  # 5-минутные данные
                self.ma_5min[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.ma_period_5min)
            else:  # Часовые данные
                self.ma_hourly[ticker] = bt.indicators.SimpleMovingAverage(data.close, period=self.params.ma_period_hourly)

        # Инициализация словарей для отслеживания данных по каждому инструменту
        self.buy_price = {}
        self.max_price = {}
        self.order = {}

    def next(self):
        # Преобразуем цены и индикаторы в numpy массивы для ускорения обработки
        for i in range(0, len(self.datas), 2):  # Обрабатываем только 5-минутные данные
            ticker = self.datas[i]._name.replace('_5min', '')
            data_5min = self.datas[i]
            data_hourly = self.datas[i + 1]
            
            # Проверяем наличие ордера
            if ticker in self.order and self.order[ticker]:
                continue  # Пропускаем, если ордер существует

            # Условия покупки: обе цены выше своих скользящих средних
            if not self.getposition(data_5min):  # Нет открытой позиции
                if data_5min.close[0] > self.ma_5min[ticker][0] and data_hourly.close[0] > self.ma_hourly[ticker][0]:
                    self.order[ticker] = self.buy(data=data_5min)
                    self.buy_price[ticker] = data_5min.close[0]
                    self.max_price[ticker] = self.buy_price[ticker]

                    # Логирование покупки
                    buy_date = data_5min.datetime.date(0)
                    buy_time = data_5min.datetime.time(0)
                    print(f"{buy_date} в {buy_time}: покупка за {self.buy_price[ticker]} для {ticker}")

            # Если позиция уже открыта
            elif self.getposition(data_5min):
                current_price = data_5min.close[0]

                # Обновляем максимальную цену
                self.max_price[ticker] = np.maximum(self.max_price[ticker], current_price)

                # Уровень трейлинг-стопа
                stop_loss_level = self.max_price[ticker] * (1 - self.params.trailing_stop)

                # Проверка условий продажи
                if current_price < stop_loss_level:
                    self.order[ticker] = self.sell(data=data_5min)
                    sell_date = data_5min.datetime.date(0)
                    sell_time = data_5min.datetime.time(0)
                    print(f"{sell_date} в {sell_time}: продажа за {current_price} для {ticker}")

    # Обработка уведомлений по ордерам
    def notify_order(self, order):
        ticker = order.data._name.replace('_5min', '')

        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order[ticker] = None  # Сброс ордера после завершения
