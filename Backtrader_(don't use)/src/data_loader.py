import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import os
import json

# Путь к директории с файлами данных
data_dir = "./data"

# Загрузка JSON с соответствиями uid и тикеров
def load_ticker_mapping(mapping_file):
    """Загружает и возвращает словарь сопоставлений uid и тикеров"""
    with open(mapping_file, 'r', encoding='utf-8') as file:
        mapping_data = json.load(file)
    return {item['uid']: item['ticker'] for item in mapping_data}

# Функция для загрузки данных по тикеру с двух таймфреймов
def load_data_for_ticker(ticker):
    """Загружает данные для указанного тикера с 5-минутным и часовым таймфреймами"""
    
    # Формирование имен файлов
    file_5min = os.path.join(data_dir, f"{ticker}_5min.csv")
    file_hourly = os.path.join(data_dir, f"{ticker}_1hour.csv")
    
    # Проверяем, существует ли файл для 5-минутного таймфрейма
    if not os.path.exists(file_5min):
        print(f"Файл {file_5min} не найден для 5-минутного таймфрейма. Пропускаем этот тикер.")
        return None, None  # Возвращаем None, чтобы пропустить тикер
    
    # Проверяем, существует ли файл для часового таймфрейма
    if not os.path.exists(file_hourly):
        print(f"Файл {file_hourly} не найден для часового таймфрейма. Пропускаем этот тикер.")
        return None, None  # Возвращаем None, чтобы пропустить тикер
    
    # Загрузка данных из CSV файлов
    data_5min = pd.read_csv(file_5min, sep=';', parse_dates=['timestamp'], index_col='timestamp')
    data_hourly = pd.read_csv(file_hourly, sep=';', parse_dates=['timestamp'], index_col='timestamp')
    
    return data_5min, data_hourly
