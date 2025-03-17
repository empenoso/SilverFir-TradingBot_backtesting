import sys
sys.stdout.reconfigure(encoding='utf-8')

import backtrader as bt

# Стратегия на основе индикатора импульса на двух временных интервалах
class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_period', 14),  # Период для индикатора импульса
        ('trailing_stop', 0.03)   # Процент для трейлинг-стопа
    )

    def __init__(self):
        print(f"\nРасчет для параметров: {self.params.momentum_period} / {self.params.trailing_stop}")

        # Создаем списки для хранения индикаторов по каждому инструменту
        self.momentum_5min = {}
        self.momentum_hourly = {}

        # Для каждого инструмента добавляем индикаторы импульса на разных интервалах
        for i, data in enumerate(self.datas):
            if i % 2 == 0:  # Четные индексы - 5-минутные данные
                ticker = data._name.replace('_5min', '')
                self.momentum_5min[ticker] = bt.indicators.Momentum(data.close, period=self.params.momentum_period)
            else:  # Нечетные индексы - часовые данные
                ticker = data._name.replace('_hourly', '')
                self.momentum_hourly[ticker] = bt.indicators.Momentum(data.close, period=self.params.momentum_period)

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
            # импульс на обоих таймфреймах положителен
            if not self.getposition(data_5min):  # Открываем сделку только если нет открытой позиции
                if self.momentum_5min[ticker][0] > 0 and self.momentum_hourly[ticker][0] > 0:
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
