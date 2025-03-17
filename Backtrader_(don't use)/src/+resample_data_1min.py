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
    """Загружает данные из CSV файла и заменяет uid на тикер"""
    file_path = os.path.join(data_dir, file_name)
    
    # Чтение данных с указанием имен колонок
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
        return None  # Возвращаем None, если uid не найден
    
    # Возвращаем только необходимые столбцы
    return data[['ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Функция для фильтрации данных по дате
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
    output_file = f"./data/{ticker}_1min.csv"
    
    # Сбрасываем индекс для записи
    data = data.reset_index()
    
    # Переупорядочиваем колонки так, чтобы тикер был первым
    columns_order = ['ticker', 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    data = data[columns_order]
    
    # Сохраняем данные в файл
    data.to_csv(output_file, sep=';', index=False, encoding='utf-8')
    print(f"Сохранены данные для {ticker} в {output_file}")

# Функция для обработки всех файлов
def process_data(ticker_mapping, start_date, end_date):
    """Загружает, фильтрует и сохраняет данные"""
    file_list = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
    total_files = len(file_list)
    
    for index, file_name in enumerate(file_list, start=1):
        # Чтение данных
        data = load_data(file_name, ticker_mapping)
        if data is None:
            continue
        
        # Фильтрация данных по дате
        data_filtered = filter_by_date(data, start_date, end_date)
        if data_filtered.empty:
            print(f"Данные для файла {file_name} не содержат записей в указанный период.")
            continue
        
        # Получение тикера
        ticker = data_filtered['ticker'].iloc[0]
        
        # Сохранение данных
        save_filtered_data(data_filtered, ticker)
        
        # Вывод прогресса
        completion_percentage = (index / total_files) * 100
        print(f"Обработано {index} из {total_files} файлов. Завершено {completion_percentage:.2f}%.")

# Пример использования
mapping_file = os.path.join(base_dir, 'data', '+mappings.json')
ticker_mapping = load_ticker_mapping(mapping_file)

start_date = '2024-08-01'
end_date = '2024-11-01'

# # Преобразуем строку в объект datetime
# date_obj = datetime.strptime(start_date, '%Y-%m-%d')
# # Определяем последний день месяца
# last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
# # Формируем end_date с последним днем месяца
# end_date = date_obj.replace(day=last_day).strftime('%Y-%m-%d')

print(f"start_date = {start_date}")
print(f"end_date = {end_date}\n")

# Процесс обработки с дополнительными проверками
process_data(ticker_mapping, start_date, end_date)


# Время выполнения
total_end_time = time.perf_counter()
elapsed_time = (total_end_time - start_time) / 60
print(f"\nВремя выполнения: {elapsed_time:.4f} минут.")
