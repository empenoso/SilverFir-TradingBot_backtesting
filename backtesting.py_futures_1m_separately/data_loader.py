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

# Функция для загрузки данных по тикеру с минутным таймфреймом
def load_data_for_ticker(ticker):
    """Загружает данные для указанного тикера с минутным таймфреймом"""
    
    # Формирование имени файла для минутного таймфрейма
    file_minute = os.path.join(data_dir, f"{ticker}_1min.csv")
    
    # Проверяем, существует ли файл для минутного таймфрейма
    if not os.path.exists(file_minute):
        print(f"Файл {file_minute} не найден для минутного таймфрейма. Пропускаем этот тикер.")
        return None  # Возвращаем None, чтобы пропустить тикер
    
    # Загрузка данных из CSV файла
    data_minute = pd.read_csv(file_minute, sep=';', parse_dates=['timestamp'], index_col='timestamp')
    
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
