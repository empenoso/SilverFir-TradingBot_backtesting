from backtesting import Strategy
from backtesting.lib import crossover
import talib
import pandas as pd
import numpy as np
from backtesting.lib import resample_apply

class LongOnlyPMAMultiTimeframeTrailingStop(Strategy):

    # Описание стратегии
    print("📝 Описание торговой стратегии:")
    print("1️⃣ Вход в длинную позицию, когда:")
    print("   ✓ Недельная цена закрытия выше 50-недельной проекционной скользящей средней (PMA)")
    print("   ✓ Дневная цена закрытия выше 50-дневной проекционной скользящей средней (PMA)")
    print("   ✓ 20-дневная проекционная скользящая средняя выше 50-дневной")
    print("3️⃣ Выход из позиции осуществляется по скользящему стопу в 5% от максимальной цены закрытия.\n")

    # Параметры для дневного таймфрейма
    d_ma_short = 20
    d_ma_long = 50
    
    # Параметры для недельного таймфрейма
    w_ma_long = 50
    
    # Параметр для скользящего стопа
    trail_percent = 0.05  # 5% трейлинг-стоп
    
    def init(self):
        # Функции PMA, перенесенные из класса PMA
        def calc_sma(data, length):
            """Простая скользящая средняя"""
            return pd.Series(data).rolling(length).mean().values
        
        def calc_slope(data, length):
            """Расчет наклона линейной регрессии"""
            def linear_regression_slope(samples):
                # Используем polyfit для расчета наклона (полином 1й степени)
                if len(samples) < 2:
                    return 0
                m, b = np.polyfit(np.arange(len(samples)), np.array(samples), 1)
                return m
                
            result = np.full_like(data, np.nan, dtype=float)
            for i in range(length-1, len(data)):
                samples = data[i-length+1:i+1]
                result[i] = linear_regression_slope(samples)
            return result
        
        # Дневные индикаторы PMA 
        # Рассчитываем компоненты для d_ma20
        d_sma20 = self.I(lambda x: calc_sma(x, self.d_ma_short), self.data.Close, name=f'SMA{self.d_ma_short}', plot=False)
        d_slope20 = self.I(lambda x: calc_slope(x, self.d_ma_short), self.data.Close, name=f'Slope{self.d_ma_short}', plot=False)
        self.d_pma20 = self.I(lambda: d_sma20 + d_slope20 * self.d_ma_short / 2, name=f'PMA{self.d_ma_short}', overlay=True, color='green') # 🟢 Зеленая PMA20

        # Рассчитываем компоненты для d_ma50
        d_sma50 = self.I(lambda x: calc_sma(x, self.d_ma_long), self.data.Close, name=f'SMA{self.d_ma_long}', plot=False)
        d_slope50 = self.I(lambda x: calc_slope(x, self.d_ma_long), self.data.Close, name=f'Slope{self.d_ma_long}', plot=False)
        self.d_pma50 = self.I(lambda: d_sma50 + d_slope50 * self.d_ma_long / 2, name=f'PMA{self.d_ma_long}', overlay=True, color='blue') # 🔵 Синяя PMA50

        # Недельные индикаторы - используем resample_apply для ресемплинга дневных данных в недельные
        # 'W-SUN' означает недельный бар, который заканчивается в воскресенье
        
        # Функция для вычисления PMA в недельном таймфрейме
        def weekly_pma(x, length):
            # Преобразуем в Series для расчетов
            x_series = pd.Series(x)
            # Получаем SMA и Slope
            sma = x_series.rolling(length).mean().values
            
            # Расчет наклона через временное окно
            slope = np.full_like(sma, np.nan, dtype=float)
            for i in range(length-1, len(x)):
                if i < length:
                    continue
                samples = x[i-length+1:i+1]
                # Линейная регрессия для получения наклона
                if len(samples) >= 2:
                    m, b = np.polyfit(np.arange(len(samples)), np.array(samples), 1)
                    slope[i] = m
            
            # Расчет PMA
            pma = sma + slope * length / 2
            return pma
        
        # Недельная PMA-50
        self.w_pma50 = resample_apply('W-SUN', weekly_pma, self.data.Close, self.w_ma_long, name=f'Weekly PMA{self.w_ma_long}', plot=True)
        
        # Для получения недельной цены закрытия, используем ту же функцию с периодом 1
        self.w_close = resample_apply('W-SUN', lambda x, _: pd.Series(x).rolling(1).mean(), self.data.Close, 1, name=f'Weekly Close', plot=True, color='black')
        
        # Создаем индикатор для отображения уровня трейлинг стопа на графике
        self.trailing_stops = self.I(lambda: np.full_like(self.data.Close, np.nan), 
                                   overlay=True, name='Трейлинг-стоп', color='red')
        
        # Для хранения цены входа и максимальной цены закрытия
        self.entry_prices = {}  # Словарь для хранения цен входа по ID позиции
        self.max_close_prices = {}  # Словарь для хранения максимальных цен закрытия
      
    def next(self):
        # Получаем текущие значения дневного таймфрейма
        current_price = self.data.Close[-1]
        current_d_pma20 = self.d_pma20[-1]
        current_d_pma50 = self.d_pma50[-1]
        current_date = self.data.index[-1]
        
        # Получаем текущие значения недельного таймфрейма
        current_w_pma50 = self.w_pma50[-1]
        current_w_close = self.w_close[-1]
        
        # Проверяем на NaN (в начале истории может не быть данных)
        if (pd.isna(current_w_pma50) or pd.isna(current_w_close) or
            pd.isna(current_d_pma20) or pd.isna(current_d_pma50)):
            return

        # Условия для недельного таймфрейма (подтверждение тренда)
        w_close_above_pma50 = current_w_close > current_w_pma50  # Недельная цена выше PMA-50
        
        # Условия для дневного таймфрейма (сигнал входа)
        d_price_above_pma50 = current_price > current_d_pma50  # Цена выше 50-дневной PMA
        d_pma20_above_pma50 = current_d_pma20 > current_d_pma50  # 20-дневная PMA выше 50-дневной PMA
        
        # Для открытых позиций обновляем трейлинг-стоп
        if self.position.is_long:
            position_id = id(self.position)
            
            # Если это новая позиция, сохраняем цену входа и инициализируем максимальную цену закрытия
            if position_id not in self.entry_prices:
                self.entry_prices[position_id] = current_price
                self.max_close_prices[position_id] = current_price
            
            entry_price = self.entry_prices[position_id]
            
            # Обновляем максимальную цену закрытия, если текущая цена закрытия выше
            if current_price > self.max_close_prices[position_id]:
                self.max_close_prices[position_id] = current_price
            
            max_close = self.max_close_prices[position_id]
            
            # Вычисляем трейлинг-стоп как % ниже максимальной цены закрытия
            trail_price = max_close * (1 - self.trail_percent)
            
            # Отображаем трейлинг-стоп на графике
            self.trailing_stops[-1] = trail_price
            
            # Проверяем условие продажи: если текущая цена закрытия опустилась ниже трейлинг-стопа
            if current_price <= trail_price:
                # Вычисляем результат сделки
                profit_pct = (current_price - entry_price) / entry_price * 100
                
                # Выводим информацию о продаже
                print(f"\n🔴 ПРОДАЖА ПО СКОЛЬЗЯЩЕМУ СТОПУ ({current_date.strftime('%Y-%m-%d')})")
                print(f"   Цена входа: {entry_price:.2f} руб.")
                print(f"   Цена выхода: {current_price:.2f} руб.")
                print(f"   Макс. цена закрытия: {max_close:.2f} руб.")
                print(f"   Результат: {profit_pct:.2f}%")
                print(f"   Скользящий стоп: {trail_price:.2f} руб. ({self.trail_percent*100:.1f}% от максимума)")
                print(f"   Причина выхода: Цена закрытия {current_price:.2f} <= Скользящий стоп {trail_price:.2f}")
                
                # Закрываем позицию
                self.position.close()
                
                # Удаляем записи о позиции
                if position_id in self.entry_prices:
                    del self.entry_prices[position_id]
                if position_id in self.max_close_prices:
                    del self.max_close_prices[position_id]
                
                # Очищаем значение трейлинг-стопа после закрытия позиции
                self.trailing_stops[-1] = np.nan
            
        # Проверяем все условия для входа - только если нет активной позиции
        elif not self.position.is_long and (w_close_above_pma50 and d_price_above_pma50 and d_pma20_above_pma50):
            
            print(f"\n🟢 ПОКУПКА ({current_date.strftime('%Y-%m-%d')})")
            print(f"   Цена: {current_price:.2f} руб.")
            print(f"   Условия входа (недельный таймфрейм):")
            print(f"      ✓ Недельная цена {current_w_close:.2f} > Недельная PMA50 {current_w_pma50:.2f}")
            print(f"   Условия входа (дневной таймфрейм):")
            print(f"      ✓ Цена {current_price:.2f} > PMA50 {current_d_pma50:.2f}")
            print(f"      ✓ PMA10 {current_d_pma20:.2f} > PMA50 {current_d_pma50:.2f}")
            
            # Входим в позицию с первоначальным стоп-лоссом
            self.buy()
            
            # Устанавливаем начальный трейлинг-стоп на графике
            self.trailing_stops[-1] = current_price * (1 - self.trail_percent)