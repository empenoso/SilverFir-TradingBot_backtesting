# модуль который выбирает только нужный интервал котировок при загрузке минуток с Т-Инвест АПИ

# Подробнее о моих поисках торговых стратегий в статьях на Хабре и Смартлабе: 
# https://github.com/empenoso/SilverFir-TradingBot_backtesting

import sys
sys.stdout.reconfigure(encoding='utf-8')
import calendar
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import time
import pytz  # Добавляем библиотеку для работы с часовыми поясами

# Начало времени
start_time = time.perf_counter()

# # Automatically construct the correct path
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Определяем базовый путь проекта
base_dir = "d:\\SynologyDrive\\rabota\\2018_investments\\SilverFir-TradingBot_backtesting\\backtesting.py_futures_1m_separately"

# Путь к директории с файлами данных
data_dir = os.path.join(base_dir, "data", "1min")

# Загрузка JSON с соответствиями uid и тикеров
def load_ticker_mapping(mapping_file):
    """Загружает и возвращает словарь сопоставлений uid и тикеров"""
    print(f"Загрузка маппингов из: {mapping_file}")
    try:
        with open(mapping_file, 'r', encoding='utf-8') as file:
            mapping_data = json.load(file)
        return {item['uid']: item['ticker'] for item in mapping_data}
    except FileNotFoundError:
        print(f"Файл маппингов не найден: {mapping_file}")
        raise
    except json.JSONDecodeError:
        print(f"Ошибка формата JSON в файле маппингов: {mapping_file}")
        raise

# Функция для чтения данных из CSV файла
def load_data(file_name, ticker_mapping):
    """Загружает данные из CSV файла и заменяет uid на тикер"""
    file_path = os.path.join(data_dir, file_name)
    
    # Чтение данных с указанием имен колонок
    data = pd.read_csv(file_path, sep=';', header=None, 
                       names=['uid', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Empty'])
    
    # Преобразуем колонку timestamp в формат datetime
    try:
        # Предполагаем, что входные данные в UTC (Z означает UTC)
        data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')
        
        # Преобразуем время из UTC в UTC+3 (московское время)
        moscow_tz = pytz.timezone('Europe/Moscow')
        data['timestamp'] = data['timestamp'].dt.tz_localize('UTC').dt.tz_convert(moscow_tz).dt.tz_localize(None)
        
    except ValueError as e:
        print(f"Ошибка в парсинге даты: {e}")
    
    # Устанавливаем колонку timestamp как индекс
    data.set_index('timestamp', inplace=True)
    
    # Преобразование данных в числовой формат (кроме uid)
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    data[cols] = data[cols].apply(pd.to_numeric, errors='coerce')
    
    # Заменяем uid на тикер
    uid = data['uid'].iloc[0]
    if uid in ticker_mapping:
        data['ticker'] = ticker_mapping[uid]
    else:
        print(f"UID {uid} не найден в сопоставлении.")
        return None  # Возвращаем None, если uid не найден
    
    # Возвращаем только необходимые столбцы
    return data[['ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Функция для фильтрации данных по дате с отладочной информацией
def filter_by_date(data, start_date, end_date):
    """Фильтрует данные по указанному диапазону дат"""
    print(f"Фильтрация данных с {start_date} по {end_date}")
    print(f"Доступные даты в данных: {data.index.min()} - {data.index.max()}")
    
    # Проверка корректности индекса
    if not pd.api.types.is_datetime64_any_dtype(data.index):
        raise ValueError("Индекс данных не является типом datetime.")
    
    # Фильтрация
    filtered_data = data.loc[start_date:end_date]
    print(f"Число записей после фильтрации: {len(filtered_data)}")
    return filtered_data

# Функция для записи данных в CSV файл
def save_filtered_data(data, ticker):
    """Сохраняет отфильтрованные данные в файл"""
    output_file = os.path.join(base_dir, "data", f"{ticker}_1min.csv")

    # Проверяем, существует ли уже файл, чтобы не дублировать заголовок
    file_exists = os.path.isfile(output_file)
    
    # Сбрасываем индекс для записи
    data = data.reset_index()
    
    # Переупорядочиваем колонки так, чтобы тикер был первым
    columns_order = ['ticker', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    data = data[columns_order]
    
    # Открываем файл в режиме append ('a') и записываем данные без заголовка, если файл уже существует
    data.to_csv(output_file, sep=';', index=False, encoding='utf-8', mode='a', header=not file_exists)
    
    print(f"Добавлены данные для {ticker} в {output_file}")

# Функция для обработки всех файлов
def process_data(ticker_mapping, start_date, end_date):
    """Загружает, фильтрует и сохраняет данные"""
    # Проверяем существование директории
    if not os.path.exists(data_dir):
        print(f"Директория с минутными данными не найдена: {data_dir}")
        return
    
    file_list = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
    if not file_list:
        print(f"В директории {data_dir} не найдено CSV файлов")
        return
        
    total_files = len(file_list)
    print(f"Найдено {total_files} файлов для обработки")
    
    for index, file_name in enumerate(file_list, start=1):
        print(f"Обработка файла: {file_name}")
        # Чтение данных
        try:
            data = load_data(file_name, ticker_mapping)
            if data is None:
                print(f"Пропускаем файл {file_name}: не удалось сопоставить UID")
                continue
        except Exception as e:
            print(f"Ошибка при загрузке файла {file_name}: {e}")
            continue
        
        # Фильтрация данных по дате
        try:
            data_filtered = filter_by_date(data, start_date, end_date)
            if data_filtered.empty:
                print(f"Данные для файла {file_name} не содержат записей в указанный период.")
                continue
        except Exception as e:
            print(f"Ошибка при фильтрации данных файла {file_name}: {e}")
            continue
        
        # Получение тикера
        ticker = data_filtered['ticker'].iloc[0]
        
        # Сохранение данных
        try:
            save_filtered_data(data_filtered, ticker)
        except Exception as e:
            print(f"Ошибка при сохранении данных файла {file_name}: {e}")
            continue
        
        # Вывод прогресса
        completion_percentage = (index / total_files) * 100
        print(f"Обработано {index} из {total_files} файлов. Завершено {completion_percentage:.2f}%.")

# Основная функция
def main():
    try:
        # Путь к файлу маппингов
        mapping_file = os.path.join(base_dir, 'data', '+mappings.json')
        print(f"Файл маппингов: {mapping_file}")
        
        # Проверяем существование файла маппингов
        if not os.path.exists(mapping_file):
            print(f"Файл маппингов не найден: {mapping_file}")
            return
            
        ticker_mapping = load_ticker_mapping(mapping_file)

        start_date = '2025-03-10'
        end_date = '2025-03-20'

        print(f"start_date = {start_date}")
        print(f"end_date = {end_date}\n")

        # Процесс обработки с дополнительными проверками
        process_data(ticker_mapping, start_date, end_date)

    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        # Время выполнения
        total_end_time = time.perf_counter()
        elapsed_time = (total_end_time - start_time) / 60
        print(f"\nВремя выполнения: {elapsed_time:.4f} минут.")

# Запуск основной функции
if __name__ == "__main__":
    main()