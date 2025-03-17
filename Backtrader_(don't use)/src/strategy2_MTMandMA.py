import backtrader as bt
import datetime

# Стратегия на основе индикатора импульса и VWMA на двух временных интервалах
class MomentumVWMA(bt.Strategy):
    params = (
        ('momentum_period', 14),  # Период для индикатора импульса
        ('vwma_period', 20),      # Период для VWMA
        ('trailing_stop', 0.03),  # Процент для трейлинг-стопа
    )

    def __init__(self):
        print(f"\nРасчет для параметров: {self.params.momentum_period} / {self.params.vwma_period} / {self.params.trailing_stop}")
        
        # Создаем словари для хранения индикаторов по каждому инструменту
        self.momentum_hourly = {}
        self.vwma_5min = {}
        self.order = {}  # Отслеживание ордеров для каждого тикера

        # Добавляем индикаторы для каждого тикера
        for i, data in enumerate(self.datas):
            ticker = data._name.replace('_5min', '').replace('_hourly', '')
            if '_5min' in data._name:
                # VWMA на 5-минутных данных
                self.vwma_5min[ticker] = bt.indicators.WeightedMovingAverage(data.close, period=self.params.vwma_period)
            elif '_hourly' in data._name:
                # Импульс на часовых данных
                self.momentum_hourly[ticker] = bt.indicators.Momentum(data.close, period=self.params.momentum_period)

        # Переменные для отслеживания уровня стоп-лосса и максимальной цены после покупки
        self.buy_price = {}
        self.max_price = {}

    def next(self):
        # Проверяем условия покупки и продажи для каждого инструмента
        for i in range(0, len(self.datas), 2):
            ticker = self.datas[i]._name.replace('_5min', '')
            data_5min = self.datas[i]
            data_hourly = self.datas[i + 1]

            # Проверяем, есть ли открытая позиция для покупки
            if not self.getposition(data_5min) and self.order.get(ticker) is None:
                # Проверяем условия покупки: импульс > 0 на часовом графике и закрытие > VWMA на 5-минутном графике
                if self.momentum_hourly[ticker][0] > 0 and data_5min.close[0] > self.vwma_5min[ticker][0]:
                    self.order[ticker] = self.buy(data=data_5min)
                    self.buy_price[ticker] = data_5min.close[0]
                    self.max_price[ticker] = self.buy_price[ticker]
                    print(f"Покупка: {data_5min.datetime.date(0)} {data_5min.datetime.time(0)} за {self.buy_price[ticker]} для {ticker}")

            # Если уже есть открытая позиция
            elif self.getposition(data_5min) and self.order.get(ticker) is None:
                current_price = data_5min.close[0]

                # Обновляем максимальную цену, если текущая выше
                if current_price > self.max_price[ticker]:
                    self.max_price[ticker] = current_price

                # Рассчитываем уровень стоп-лосса
                stop_loss_level = self.max_price[ticker] * (1 - self.params.trailing_stop)

                # Условие продажи по трейлинг-стопу
                if current_price < stop_loss_level:
                    self.order[ticker] = self.sell(data=data_5min)
                    print(f"Продажа по трейлинг-стопу: {data_5min.datetime.date(0)} {data_5min.datetime.time(0)} за {current_price} для {ticker}")
                
                # # Условие продажи в конце торгового дня
                # elif data_5min.datetime.time(0) >= datetime.time(20, 45):
                #     self.order[ticker] = self.sell(data=data_5min)
                #     print(f"Продажа в конце дня: {data_5min.datetime.date(0)} {data_5min.datetime.time(0)} за {current_price} для {ticker}")

    # Обрабатываем уведомления по ордерам
    def notify_order(self, order):
        ticker = order.data._name.replace('_5min', '').replace('_hourly', '')
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order[ticker] = None  # Очищаем ордер после завершения
