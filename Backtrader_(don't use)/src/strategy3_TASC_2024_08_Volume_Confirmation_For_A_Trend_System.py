import backtrader as bt
import pandas as pd

# --- Новая стратегия на основе Volume Confirmation For A Trend System ---
class VolumeConfirmationStrategy(bt.Strategy):
    params = (
        ('adx_period', 14),           # Период для ADX индикатора
        ('tti_fast', 13),             # Быстрая средняя для TTI
        ('tti_slow', 26),             # Медленная средняя для TTI
        ('tti_signal', 9),            # Сглаживающая линия TTI
        ('vpci_short', 5),            # Краткосрочная средняя для VPCI
        ('vpci_long', 25),            # Долгосрочная средняя для VPCI
        ('trailing_stop', 0.03),      # Процент для трейлинг-стопа
    )

    def __init__(self):
        # --- Расчет индикаторов ---
        self.adx = {}  # ADX индикатор для часовых данных
        self.tti = {}  # TTI индикатор
        self.tti_signal = {}  # Сигнальная линия для TTI
        self.vpci = {}  # Индикатор VPCI

        # --- Переменные для отслеживания позиций ---
        self.buy_price = {}  # Цена покупки для каждого инструмента
        self.max_price = {}  # Максимальная цена после покупки для трейлинг-стопа
        self.order = {}  # Словарь для отслеживания ордеров по каждому инструменту

        # --- Настройка индикаторов для каждого инструмента ---
        for i in range(1, len(self.datas), 2):  # Проходим только по часовым данным
            data_hourly = self.datas[i]
            ticker = data_hourly._name.replace('_hourly', '')

            # ADX индикатор
            self.adx[ticker] = bt.indicators.AverageDirectionalMovementIndex(data_hourly, period=self.params.adx_period)

            # TTI индикатор
            fast_vwma = bt.indicators.WeightedMovingAverage(data_hourly.close, period=self.params.tti_fast)
            slow_vwma = bt.indicators.WeightedMovingAverage(data_hourly.close, period=self.params.tti_slow)
            self.tti[ticker] = fast_vwma - slow_vwma
            self.tti_signal[ticker] = bt.indicators.SimpleMovingAverage(self.tti[ticker], period=self.params.tti_signal)

            # VPCI индикатор
            vpci_vwma_short = bt.indicators.WeightedMovingAverage(data_hourly.close, period=self.params.vpci_short)
            vpci_vwma_long = bt.indicators.WeightedMovingAverage(data_hourly.close, period=self.params.vpci_long)
            vol_ratio = bt.indicators.SimpleMovingAverage(data_hourly.volume, period=self.params.vpci_short) / \
                        bt.indicators.SimpleMovingAverage(data_hourly.volume, period=self.params.vpci_long)
            self.vpci[ticker] = (vpci_vwma_long - bt.indicators.SimpleMovingAverage(data_hourly.close, period=self.params.vpci_long)) * \
                                (vpci_vwma_short / bt.indicators.SimpleMovingAverage(data_hourly.close, period=self.params.vpci_short)) * vol_ratio

    def next(self):
        # Проходим по всем 5-минутным и часовым данным парами
        for i in range(0, len(self.datas), 2):
            data_5min = self.datas[i]  # 5-минутные данные
            data_hourly = self.datas[i + 1]  # Часовые данные
            ticker = data_hourly._name.replace('_hourly', '')

            # Проверка на наличие открытого ордера
            if ticker in self.order and self.order[ticker]:
                continue  # Пропуск, если есть открытый ордер

            # --- Условия для открытия позиции ---
            if not self.getposition(data_5min):  # Открытие позиции только если нет текущей
                if (self.adx[ticker][0] > 30 and self.tti[ticker][0] > self.tti_signal[ticker][0] and self.vpci[ticker][0] > 0):
                    self.order[ticker] = self.buy(data=data_5min)  # Покупка
                    self.buy_price[ticker] = data_5min.close[0]
                    self.max_price[ticker] = self.buy_price[ticker]  # Инициализация максимальной цены
                    print(f"{data_5min.datetime.date(0)}: Покупка для {ticker} по цене {self.buy_price[ticker]}")

            # --- Условия для закрытия позиции (Трейлинг-стоп) ---
            elif self.getposition(data_5min):
                current_price = data_5min.close[0]

                # Обновление максимальной цены, если текущая выше
                if current_price > self.max_price[ticker]:
                    self.max_price[ticker] = current_price

                # Уровень стоп-лосса по трейлинг-стопу
                stop_loss_level = self.max_price[ticker] * (1 - self.params.trailing_stop)

                # Закрытие позиции, если текущая цена опустилась ниже уровня стоп-лосса
                if current_price < stop_loss_level:
                    self.order[ticker] = self.sell(data=data_5min)
                    print(f"{data_5min.datetime.date(0)}: Продажа для {ticker} по цене {current_price} с трейлинг-стопом")

    def notify_order(self, order):
        ticker = order.data._name.replace('_5min', '')
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order[ticker] = None  # Сброс ордера после завершения
