# 5-6 идей для построения прибыльной торговой системы - Александр Резвяков
# https://smart-lab.ru/blog/1111228.php

# Подробнее о моих поисках торговых стратегий в статьях на Хабре и Смартлабе: 
# https://github.com/empenoso/SilverFir-TradingBot_backtesting

from backtesting import Strategy
import pandas as pd
import numpy as np
import random
from datetime import time

class RandomEntryStrategy(Strategy):
    # Параметры стратегии
    trail_percent = 0.003  # Процент трейлинг-стопа 3%
    entry_probability = 0.5  # Вероятность входа в рынок 50/50
    entry_time = "10:25"  # Время для входа в позицию
    exit_time = "23:40"  # Время для выхода из позиции

    def init(self):
        """
        Инициализация индикаторов и переменных
        """
        # Подготовка данных для дневных баров
        self.daily_data = self.resample_to_daily()
        
        # Создаем индикатор для отображения трейлинг-стопа на графике
        # Используем тот же тип данных, что и у Close, и заполняем нулями
        self.trailing_stops = self.I(lambda: np.full_like(self.data.Close, np.nan, dtype=float), 
                            overlay=True, name='Трейлинг-стоп')
        
        # Для отслеживания, активен ли трейлинг-стоп (для правильного отображения)
        self.is_trailing_stop_active = False
        
        # Для хранения цены входа и максимальной/минимальной цены закрытия
        self.entry_prices = {}  # Словарь для хранения цен входа по ID позиции
        self.max_close_prices = {}  # Максимальные цены закрытия для лонгов
        self.min_close_prices = {}  # Минимальные цены закрытия для шортов
        
        # Создаем время входа и выхода как объекты time
        self.entry_time_obj = pd.to_datetime(self.entry_time).time()
        self.exit_time_obj = pd.to_datetime(self.exit_time).time()

    def resample_to_daily(self):
        """
        Пересемплирование данных в дневные бары
        """
        # Создаем копию данных и устанавливаем индекс как дату
        daily_df = pd.DataFrame(index=self.data.index)
        daily_df['Open'] = self.data.Open
        daily_df['High'] = self.data.High
        daily_df['Low'] = self.data.Low
        daily_df['Close'] = self.data.Close
        
        # Группируем по дате и агрегируем
        daily_df = daily_df.groupby(daily_df.index.date).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        })
        
        # Конвертируем индекс обратно в datetime для удобства
        daily_df.index = pd.to_datetime(daily_df.index)
        
        return daily_df

    def next(self):
        """
        Основная логика торговли, выполняемая для каждого бара
        """
        current_time = self.data.index[-1].time()
        current_date = self.data.index[-1].date()
        
        # Обрабатываем текущие позиции (проверка трейлинг-стопов)
        if self.position.is_long:
            self.update_long_position()
        elif self.position.is_short:
            self.update_short_position()
        # Можно просто удалить этот блок или заменить на
        elif self.is_trailing_stop_active:
            self.trailing_stops[-1] = np.nan
            self.is_trailing_stop_active = False
        
        # Вход в позицию случайным образом в 10:00, если позиции нет
        if current_time == self.entry_time_obj and not self.position:
            # Проверяем условия для дневных баров
            try:
                current_date_idx = self.daily_data.index.get_indexer([pd.Timestamp(current_date)], method='pad')[0]
            
                # Проверяем, что у нас есть достаточно данных (минимум 3 дневных бара)
                if current_date_idx >= 2:
                    # Получаем последние 3 дневных бара
                    last_daily_bars = self.daily_data.iloc[current_date_idx-2:current_date_idx+1]
                    
                    # Проверяем условия для длинной позиции (два дня подряд повышающиеся минимумы и максимумы)
                    long_condition = (
                        last_daily_bars['Low'].iloc[0] < last_daily_bars['Low'].iloc[1] and
                        last_daily_bars['High'].iloc[0] < last_daily_bars['High'].iloc[1]
                    )
                    
                    # Проверяем условия для короткой позиции (два дня подряд понижающиеся минимумы и максимумы)
                    short_condition = (
                        last_daily_bars['Low'].iloc[0] > last_daily_bars['Low'].iloc[1] and
                        last_daily_bars['High'].iloc[0] > last_daily_bars['High'].iloc[1]
                    )
                    
                    # Используем случайность для входа
                    if random.random() < self.entry_probability:
                        if long_condition:
                            self.buy()
                            entry_price = self.data.Close[-1]
                            position_id = id(self.position)
                            self.entry_prices[position_id] = entry_price
                            self.max_close_prices[position_id] = entry_price
                            
                            # Устанавливаем начальный трейлинг-стоп для отображения на графике
                            trail_price = entry_price * (1 - self.trail_percent)
                            self.trailing_stops[-1] = trail_price
                            self.is_trailing_stop_active = True
                            
                            print(f"ПОКУПКА на {current_date}: Цена: {entry_price:.2f}, Стоп: {trail_price:.2f}")
                            
                        elif short_condition:
                            self.sell()
                            entry_price = self.data.Close[-1]
                            position_id = id(self.position)
                            self.entry_prices[position_id] = entry_price
                            self.min_close_prices[position_id] = entry_price
                            
                            # Устанавливаем начальный трейлинг-стоп для отображения на графике
                            trail_price = entry_price * (1 + self.trail_percent)
                            self.trailing_stops[-1] = trail_price
                            self.is_trailing_stop_active = True
                            
                            print(f"ПРОДАЖА на {current_date}: Цена: {entry_price:.2f}, Стоп: {trail_price:.2f}")
            except Exception as e:
                print(f"Ошибка при проверке условий входа: {e}")
        
        # Закрытие позиции в 20:40
        if current_time == self.exit_time_obj and self.position:
            exit_price = self.data.Close[-1]
            position_id = id(self.position)
            
            if self.position.is_long:
                entry_price = self.entry_prices.get(position_id, 0)
                max_close = self.max_close_prices.get(position_id, 0)
                profit_pct = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
                print(f"ЗАКРЫТИЕ ЛОНГА на {current_date} в {current_time}: Цена: {exit_price:.2f}, "
                      f"Вход: {entry_price:.2f}, Макс.закр.: {max_close:.2f}, P/L: {profit_pct:.2f}%")
            else:
                entry_price = self.entry_prices.get(position_id, 0)
                min_close = self.min_close_prices.get(position_id, 0)
                profit_pct = (entry_price - exit_price) / entry_price * 100 if entry_price > 0 else 0
                print(f"ЗАКРЫТИЕ ШОРТА на {current_date} в {current_time}: Цена: {exit_price:.2f}, "
                      f"Вход: {entry_price:.2f}, Мин.закр.: {min_close:.2f}, P/L: {profit_pct:.2f}%")
            
            # Закрываем позицию
            self.position.close()
            
            # Очищаем данные по позиции
            if position_id in self.entry_prices:
                del self.entry_prices[position_id]
            if position_id in self.max_close_prices:
                del self.max_close_prices[position_id]
            if position_id in self.min_close_prices:
                del self.min_close_prices[position_id]
            
            # Очищаем трейлинг-стоп на графике
            self.trailing_stops[-1] = np.nan
            self.is_trailing_stop_active = False
    
    def update_long_position(self):
        """
        Обновление трейлинг-стопа для длинной позиции
        """
        position_id = id(self.position)
        current_close = self.data.Close[-1]
        
        # Если это новая позиция, инициализируем ее данные
        if position_id not in self.entry_prices:
            self.entry_prices[position_id] = self.position.entry_price
            self.max_close_prices[position_id] = self.position.entry_price
        
        # Обновляем максимальную цену закрытия, если текущая цена выше
        if current_close > self.max_close_prices[position_id]:
            self.max_close_prices[position_id] = current_close
        
        # Получаем максимальную цену закрытия и цену входа
        max_close = self.max_close_prices[position_id]
        entry_price = self.entry_prices[position_id]
        
        # Вычисляем трейлинг-стоп как процент ниже максимальной цены закрытия
        trail_price = max_close * (1 - self.trail_percent)
        
        # Отображаем трейлинг-стоп на графике
        self.trailing_stops[-1] = trail_price
        self.is_trailing_stop_active = True
        
        # Проверяем условие для закрытия позиции (падение на 5% от максимальной цены)
        if current_close <= trail_price:
            profit_pct = (current_close - entry_price) / entry_price * 100
            
            print(f"ПРОДАЖА (трейлинг-стоп) на {self.data.index[-1].date()}: Цена: {current_close:.2f}, "
                  f"Стоп: {trail_price:.2f}, Вход: {entry_price:.2f}, Макс.закр.: {max_close:.2f}, "
                  f"P/L: {profit_pct:.2f}%")
            
            # Закрываем позицию
            self.position.close()
            
            # Очищаем данные по позиции
            del self.entry_prices[position_id]
            del self.max_close_prices[position_id]
            
            # Очищаем трейлинг-стоп на графике
            self.trailing_stops[-1] = np.nan
            self.is_trailing_stop_active = False
    
    def update_short_position(self):
        """
        Обновление трейлинг-стопа для короткой позиции
        """
        position_id = id(self.position)
        current_close = self.data.Close[-1]
        
        # Если это новая позиция, инициализируем ее данные
        if position_id not in self.entry_prices:
            self.entry_prices[position_id] = self.position.entry_price
            self.min_close_prices[position_id] = self.position.entry_price
        
        # Обновляем минимальную цену закрытия, если текущая цена ниже
        if current_close < self.min_close_prices[position_id]:
            self.min_close_prices[position_id] = current_close
        
        # Получаем минимальную цену закрытия и цену входа
        min_close = self.min_close_prices[position_id]
        entry_price = self.entry_prices[position_id]
        
        # Вычисляем трейлинг-стоп как процент выше минимальной цены закрытия
        trail_price = min_close * (1 + self.trail_percent)
        
        # Отображаем трейлинг-стоп на графике
        self.trailing_stops[-1] = trail_price
        self.is_trailing_stop_active = True
        
        # Проверяем условие для закрытия позиции (рост на 5% от минимальной цены)
        if current_close >= trail_price:
            profit_pct = (entry_price - current_close) / entry_price * 100
            
            print(f"ВЫКУП (трейлинг-стоп) на {self.data.index[-1].date()}: Цена: {current_close:.2f}, "
                  f"Стоп: {trail_price:.2f}, Вход: {entry_price:.2f}, Мин.закр.: {min_close:.2f}, "
                  f"P/L: {profit_pct:.2f}%")
            
            # Закрываем позицию
            self.position.close()
            
            # Очищаем данные по позиции
            del self.entry_prices[position_id]
            del self.min_close_prices[position_id]
            
            # Очищаем трейлинг-стоп на графике
            self.trailing_stops[-1] = np.nan
            self.is_trailing_stop_active = False