# Модуль загрузки данных из CSV файла в формат backtesting.py
# Подробнее о моих поисках торговых стратегий в статьях на Хабре и Смартлабе: 
# https://github.com/empenoso/SilverFir-TradingBot_backtesting
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import os
import json
import numpy as np

# Путь к директории с файлами данных
data_dir = "./data"

# Загрузка JSON с соответствиями uid и тикеров
def load_ticker_mapping(mapping_file):
    """Загружает и возвращает словарь сопоставлений uid и тикеров"""
    with open(mapping_file, 'r', encoding='utf-8') as file:
        mapping_data = json.load(file)
    return {item['uid']: item['ticker'] for item in mapping_data}

# Функция для загрузки данных по тикеру с минутным таймфреймом
def load_data_for_ticker(ticker):
    """Загружает данные для указанного тикера с 5-минутным таймфреймом"""
    
    # Формирование имени файла для 5-минутного таймфрейма
    file_minute = os.path.join(data_dir, f"{ticker}_5min.csv")
    
    # Проверяем, существует ли файл для 5-минутного таймфрейма
    if not os.path.exists(file_minute):
        print(f"Файл {file_minute} не найден для 5-минутного таймфрейма. Пропускаем этот тикер.")
        return None  # Возвращаем None, чтобы пропустить тикер
    
    # Загрузка данных из CSV файла
    data_minute = pd.read_csv(file_minute, sep=';', parse_dates=['timestamp'], 
                              index_col='timestamp')
    
    # Диагностика NaN значений до обработки
    nan_count = data_minute.isna().sum()
    print(f"Количество NaN значений в каждой колонке до обработки:\n{nan_count}")
    print(f"Общее количество строк с NaN: {data_minute.isna().any(axis=1).sum()} из {len(data_minute)}")
    
    # Удаляем строки, где все значения OHLC отсутствуют или Volume = 0
    # Это удалит строки, где нет торгов (как в вашем примере)
    data_minute = data_minute.dropna(subset=['Open', 'High', 'Low', 'Close'], how='all')
    
    # Удаляем строки с нулевым объемом (дополнительно)
    data_minute = data_minute[data_minute['Volume'] != 0]
    
    # Проверяем, остались ли строки с частичными NaN значениями 
    # (например, если в какой-то строке отсутствует только 'High')
    partial_nan = data_minute.isna().any(axis=1).sum()
    
    if partial_nan > 0:
        print(f"Обнаружено {partial_nan} строк с частичными NaN значениями.")
        # Для таких строк используем интерполяцию для заполнения пропусков
        data_minute = data_minute.interpolate(method='time')
        
        # Заполняем оставшиеся NaN (начало и конец, где интерполяция не работает)
        data_minute = data_minute.fillna(method='ffill').fillna(method='bfill')
    
    # Диагностика после обработки
    print(f"После обработки осталось {len(data_minute)} строк данных")
    print(f"Количество NaN значений после обработки: {data_minute.isna().sum().sum()}")
    
    return data_minute

# Пример использования
if __name__ == "__main__":
    ticker = "SiH5"  # Пример тикера
    
    # Загрузка данных для тикера
    data = load_data_for_ticker(ticker)
    
    # Если данные были успешно загружены
    if data is not None:
        print(f"Данные для тикера {ticker} загружены успешно!")
        print(data.head())  # Выводим первые 5 строк данных
    else:
        print(f"Не удалось загрузить данные для тикера {ticker}.")