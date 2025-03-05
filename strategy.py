# определение торговой стратегии

from backtesting import Strategy
from backtesting.lib import crossover
import talib
import pandas as pd
import numpy as np
from backtesting.lib import resample_apply

class LongOnlyPMAMultiTimeframeATRTrailingStop(Strategy):

    # Описание стратегии
    print("📝 Описание торговой стратегии:")
    print("1️⃣ Вход в длинную позицию, когда:")
    print("   ✓ Недельная цена закрытия выше 50-недельной проекционной скользящей средней (PMA)")
    print("   ✓ Дневная цена закрытия выше 50-дневной проекционной скользящей средней (PMA)")
    print("   ✓ 10-дневная проекционная скользящая средняя выше 50-дневной")
    print("2️⃣ Первоначальный стоп-лосс устанавливается на 10% ниже цены входа")
    print("3️⃣ Выход из позиции осуществляется по скользящему стопу на основе ATR.\n")

    # Параметры для дневного таймфрейма
    d_ma_short = 10
    d_ma_long = 50
    
    # Параметры для недельного таймфрейма
    w_ma_long = 50
    
    # Параметр стоп-лосса (первоначальный)
    stop_loss_pct = 0.1

    # Параметр ATR для скользящего стопа
    atr_period = 14  # Период ATR
    atr_multiplier = 2 # Множитель ATR для скользящего стопа
    
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
        
        def calc_atr(high, low, close, period=14):
            """Расчет ATR с использованием TA-Lib"""
            return talib.ATR(high, low, close, timeperiod=period)
            
        # def calc_pma_prediction(pma, slope, length):
        #     """Предсказание на основе PMA для еще большего уменьшения запаздывания"""
        #     # Predict = PMA + 0.5*(Slope - Slope[2])*Length
        #     predict = np.full_like(pma, np.nan, dtype=float)
        #     for i in range(2, len(pma)):
        #         predict[i] = pma[i] + (slope[i] - slope[i-2]) * length / 2
        #     return predict
        
        # Дневные индикаторы PMA 
        # Рассчитываем компоненты для d_ma10
        d_sma10 = self.I(lambda x: calc_sma(x, self.d_ma_short), self.data.Close, name=f'SMA{self.d_ma_short}', plot=False)
        d_slope10 = self.I(lambda x: calc_slope(x, self.d_ma_short), self.data.Close, name=f'Slope{self.d_ma_short}', plot=False)
        self.d_pma10 = self.I(lambda: d_sma10 + d_slope10 * self.d_ma_short / 2, name=f'PMA{self.d_ma_short}', overlay=True, color='green') # 🟢 Зеленая PMA10

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
        
        # Индикатор ATR для скользящего стопа, отображаем в отдельном окне
        self.atr = self.I(calc_atr, self.data.High, self.data.Low, self.data.Close, period=self.atr_period, name=f'ATR({self.atr_period})', overlay=False) # 📉 ATR в отдельном окне

        # Переменная для хранения скользящего стопа
        self.trailing_stop = None
        # Переменная для хранения максимальной цены с момента открытия позиции
        self.highest_price_since_entry = None
      
    def next(self):
        # Получаем текущие значения дневного таймфрейма
        current_price = self.data.Close[-1]
        current_d_pma10 = self.d_pma10[-1]
        current_d_pma50 = self.d_pma50[-1]
        current_atr = self.atr[-1] # Текущее значение ATR
        current_date = self.data.index[-1]
        
        # Получаем текущие значения недельного таймфрейма
        current_w_pma50 = self.w_pma50[-1]
        current_w_close = self.w_close[-1]
        
        # Проверяем на NaN (в начале истории может не быть данных)
        if (pd.isna(current_w_pma50) or pd.isna(current_w_close) or
            pd.isna(current_d_pma10) or pd.isna(current_d_pma50) or pd.isna(current_atr)): # ⚠️ Проверяем ATR на NaN
            return


        # Условия для недельного таймфрейма (подтверждение тренда)
        w_close_above_pma50 = current_w_close > current_w_pma50  # Недельная цена выше PMA-50
        
        # Условия для дневного таймфрейма (сигнал входа)
        d_price_above_pma50 = current_price > current_d_pma50  # Цена выше 50-дневной PMA
        d_pma10_above_pma50 = current_d_pma10 > current_d_pma50  # 10-дневная PMA выше 50-дневной PMA
        
        # Проверяем все условия для входа - только если нет активной позиции
        if not self.position and (w_close_above_pma50 and d_price_above_pma50 and d_pma10_above_pma50):
            # Устанавливаем первоначальный стоп-лосс
            stop_loss = current_price * (1 - self.stop_loss_pct)
            
            print(f"\n🟢 ПОКУПКА ({current_date.strftime('%Y-%m-%d')})")
            print(f"   Цена: {current_price:.2f} руб.")
            print(f"   Стоп-лосс: {stop_loss:.2f} руб. (риск: {self.stop_loss_pct*100:.1f}%)")
            print(f"   Условия входа (недельный таймфрейм):")
            print(f"      ✓ Недельная цена {current_w_close:.2f} > Недельная PMA50 {current_w_pma50:.2f}")
            print(f"   Условия входа (дневной таймфрейм):")
            print(f"      ✓ Цена {current_price:.2f} > PMA50 {current_d_pma50:.2f}")
            print(f"      ✓ PMA10 {current_d_pma10:.2f} > PMA50 {current_d_pma50:.2f}")
            
            # Входим в позицию
            self.buy(sl=stop_loss)

            # Инициализируем скользящий стоп и максимальную цену после входа в позицию
            self.trailing_stop = current_price - self.atr_multiplier * current_atr # 📐 Начальный скользящий стоп ниже цены входа
            self.highest_price_since_entry = current_price # 🚀 Максимальная цена на момент входа
        
        # Логика скользящего стопа, если позиция уже открыта
        elif self.position:
            # Обновляем максимальную цену с момента входа
            self.highest_price_since_entry = max(self.highest_price_since_entry, current_price) # 📈 Обновляем максимум цены

            # Рассчитываем новый уровень скользящего стопа
            new_trailing_stop = self.highest_price_since_entry - self.atr_multiplier * current_atr # 📐 Новый уровень скользящего стопа

            # Поднимаем скользящий стоп, только если новый уровень выше текущего
            if new_trailing_stop > self.trailing_stop:
                self.trailing_stop = new_trailing_stop # ⬆️ Поднимаем стоп-лосс

            # Проверяем условие выхода по скользящему стопу
            if current_price <= self.trailing_stop: # 📉 Цена достигла скользящего стопа
                print(f"\n🔴 ПРОДАЖА ПО СКОЛЬЗЯЩЕМУ СТОПУ ({current_date.strftime('%Y-%m-%d')})") # 🛑 Продажа по стопу
                print(f"   Цена выхода: {current_price:.2f} руб.") # 💰 Цена выхода
                print(f"   Скользящий стоп: {self.trailing_stop:.2f} руб.") # 📉 Уровень стопа
                print(f"   Причина выхода: Цена {current_price:.2f} <= Скользящий стоп {self.trailing_stop:.2f} (ATR({self.atr_period})*{self.atr_multiplier})") # ⚠️ Причина выхода

                # Закрываем позицию по скользящему стопу
                self.position.close()