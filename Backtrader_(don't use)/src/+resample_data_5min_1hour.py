import sys
sys.stdout.reconfigure(encoding='utf-8')
import calendar
from datetime import datetime
import pandas as pd
import os
import json
import time

# Начало времени
start_time = time.perf_counter()

# Путь к директории с файлами данных
data_dir = "./data/1min"

# Automatically construct the correct path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Загрузка JSON с соответствиями uid и тикеров
def load_ticker_mapping(mapping_file):
    """Загружает и возвращает словарь сопоставлений uid и тикеров"""
    with open(mapping_file, 'r', encoding='utf-8') as file:
        mapping_data = json.load(file)
    return {item['uid']: item['ticker'] for item in mapping_data}

# Функция для чтения данных из CSV файла
def load_data(file_name, ticker_mapping):
    """Загружает данные из CSV файла и преобразует uid в тикер"""
    file_path = os.path.join(data_dir, file_name)
    
    # Чтение данных с явным указанием имен колонок
    data = pd.read_csv(file_path, sep=';', header=None, 
                       names=['uid', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Empty'])
    
    # Преобразуем колонку timestamp в формат datetime
    try:
        data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')
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
    
    # Возвращаем только необходимые столбцы
    return data[['ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Функция для фильтрации данных по дате
def filter_by_date(data, start_date, end_date):
    """Фильтрует данные по указанному диапазону дат"""
    return data.loc[start_date:end_date]

# Функция для ресемплинга данных на новый таймфрейм
def resample_data(data, timeframe):
    """Ресемплинг данных до указанного таймфрейма"""
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }
    return data.resample(timeframe).apply(ohlc_dict).dropna()

# Функция для записи данных в CSV файл с добавлением новых данных
def save_data_by_timeframe(data, ticker, timeframe):
    """Сохраняет данные в файл для указанного тикера и таймфрейма, добавляя новые данные к уже существующим"""
    output_file = f"./data/{ticker}_{timeframe}.csv"
    
    # Добавляем столбец с тикером
    data['ticker'] = ticker
    
    # Сбрасываем индекс, чтобы timestamp стал колонкой, и тикер был первым
    data = data.reset_index()  # Теперь timestamp тоже колонка
    
    # Переупорядочиваем колонки так, чтобы тикер был первым
    columns_order = ['ticker', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    data = data[columns_order]  # Применяем новый порядок колонок
    
    # Проверяем, существует ли файл
    if os.path.exists(output_file):
        # Если файл существует, загружаем его и добавляем новые данные
        existing_data = pd.read_csv(output_file, sep=';', index_col=None, parse_dates=True)
        data = pd.concat([existing_data, data])
    
    # Сохраняем данные, не перезаписывая предыдущие
    data.to_csv(output_file, sep=';', index=False, encoding='utf-8')
    print(f"Сохранены данные для {ticker} с таймфреймом {timeframe} в {output_file}")

# Функция для чтения всех файлов в директории, фильтрации по дате и сохранения по таймфреймам
def process_data(ticker_mapping, start_date, end_date):
    """Загружает, фильтрует и сохраняет данные по таймфреймам"""
    
    # Получаем список всех файлов
    file_list = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
    total_files = len(file_list)
    
    # Проходим по каждому файлу и считаем процент выполнения
    for index, file_name in enumerate(file_list, start=1):
        # Чтение и обработка данных
        data = load_data(file_name, ticker_mapping)
        data_filtered = filter_by_date(data, start_date, end_date)
        
        # Проверка на пустой результат после фильтрации
        if data_filtered.empty:
            print(f"Данные для файла {file_name} не содержат записей в указанный период.")
            continue
        
        # Получаем тикер для текущего файла
        ticker = data_filtered['ticker'].iloc[0]
        
        # Ресемплинг на 5 минут и 1 час
        data_5min = resample_data(data_filtered, '5min')
        data_1hour = resample_data(data_filtered, '1h')
        
        # Сохранение данных в разные файлы, добавляя новые данные
        save_data_by_timeframe(data_5min, ticker, '5min')
        save_data_by_timeframe(data_1hour, ticker, '1hour')
        
        # Выводим процент выполнения
        completion_percentage = (index / total_files) * 100
        print(f"Обработано {index} из {total_files} файлов. Завершено {completion_percentage:.2f}%.")

# Пример использования
mapping_file = os.path.join(base_dir, 'data', '+mappings.json')
ticker_mapping = load_ticker_mapping(mapping_file)

start_date = '2024-10-01'
#end_date = '2024-09-24'

# Преобразуем строку в объект datetime
date_obj = datetime.strptime(start_date, '%Y-%m-%d')
# Определяем последний день месяца
last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
# Формируем end_date с последним днем месяца
end_date = date_obj.replace(day=last_day).strftime('%Y-%m-%d')

print(f"start_date = {start_date}")
print(f"end_date = {end_date}\n")

process_data(ticker_mapping, start_date, end_date)

# Время выполнения
total_end_time = time.perf_counter()
elapsed_time = (total_end_time - start_time) / 60
print(f"\nВремя выполнения: {elapsed_time:.4f} минут.")
