# Ошибка, которую вы видите, возникает из-за несоответствия в том, как новые версии **pandas** обрабатывают метод `get_loc()`. 
# Ключевой аргумент `method='nearest'` больше не поддерживается в последних версиях **pandas**. Эта проблема связана с тем, 
# как библиотека **Backtesting.py** взаимодействует с новыми версиями **pandas**, в частности, при повторной выборке данных 
# для построения графиков.

### Возможные исправления:
# 1. **Обновите Backtesting.py**: проверьте, есть ли новая версия **Backtesting.py**, которая решает эту проблему, 
# поддерживая последние изменения API **pandas**. 

import pandas as pd
from backtesting import Backtest, Strategy

# Функция для вычисления скользящей средней
def SMA(values, window):
    """Возвращает скользящую среднюю для указанного окна"""
    return pd.Series(values).rolling(window=window).mean()

# Определение стратегии
class MovingAverageStrategy(Strategy):
    # Инициализация стратегии
    def init(self):
        # Расчет 5-минутной и часовой скользящих средних
        self.sma_5min = self.I(SMA, self.data.Close, 5)    # SMA для 5-минутных свечей
        self.sma_1hour = self.I(SMA, self.data.Close, 60)  # SMA для часовых свечей
        
        # Переменная для хранения максимальной цены после покупки для трейлинг стопа
        self.highest_price_since_buy = None

    # Определение условий покупки и продажи
    def next(self):
        # Условие покупки: цена закрытия выше 5-минутной и часовой скользящих средних
        if self.data.Close[-1] > self.sma_5min[-1] and self.data.Close[-1] > self.sma_1hour[-1]:
            self.buy()
            # Сброс максимальной цены после покупки
            self.highest_price_since_buy = self.data.Close[-1]
        
        # Трейлинг стоп лосс
        if self.position.is_long:
            # Обновление максимальной цены с момента покупки
            self.highest_price_since_buy = max(self.highest_price_since_buy, self.data.Close[-1])
            
            # Стоп лосс: если цена упала более чем на 2% от максимальной
            stop_loss_price = self.highest_price_since_buy * (1 - 0.02)
            
            # Закрытие позиции, если цена опустилась ниже уровня стоп-лосса
            if self.data.Close[-1] < stop_loss_price:
                self.position.close()
