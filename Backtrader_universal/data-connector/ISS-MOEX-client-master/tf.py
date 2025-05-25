import itertools
import pandas as pd
from datetime import datetime, timedelta


'''
1. Для формирования ТФ 5,15 и 30 минут используем 1 мин ТФ. 
2. В выгрузку попадает День, в котором есть хотя бы одна Свеча с VOL не равным 0.
3. РЕШИЛ делать без заполнения пустых интервалов. А дальше посмотрим.
'''


def fill_missing_time(data):
    """
    Заполняем диапазон внутри дня в соответствии с расписанием.

    :param data: Исходный набор баров одного дня, список словарей:
     [{'open': 21.17, 'close': 21.17, 'high': 21.17, 'low': 21.17, 'value': 120669, 'volume': 5700, 'begin': '2024- ...
    :return: Дополненный пустыми барами исходный набор согласно расписания, список словарей
    """
    result = []
    start_hour = str(datetime.strptime(data[0]['begin'], '%Y-%m-%d %H:%M:%S').replace(minute=0, second=0))
    expected_time = datetime.strptime(start_hour, '%Y-%m-%d %H:%M:%S')

    for entry in data:
        actual_time = datetime.strptime(entry['begin'], '%Y-%m-%d %H:%M:%S')
        while expected_time < actual_time:
            result.append({
                'open': -1, 'close': -1, 'high': -1, 'low': -1, 'volume': 0, 'value': 0,
                'begin': expected_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end': (expected_time + timedelta(seconds=59)).strftime('%Y-%m-%d %H:%M:%S'),
                'minutes_value': expected_time.minute
            })
            expected_time += timedelta(minutes=1)

        result.append(entry)
        expected_time += timedelta(minutes=1)

    return result


def convert_to_higher_timeframe(minute_data, N):
    result = []

    for i in range(0, len(minute_data), N):
        chunk = minute_data[i:i + N]
        non_empty_chunk = [entry for entry in chunk if entry['open'] != -1]
        if non_empty_chunk:
            new_entry = {
                'open': non_empty_chunk[0]['open'],
                'close': non_empty_chunk[-1]['close'],
                'high': max(entry['high'] for entry in non_empty_chunk),
                'low': min(entry['low'] for entry in non_empty_chunk),
                'volume': sum(entry['volume'] for entry in non_empty_chunk),
                'value': sum(entry['value'] for entry in non_empty_chunk),
                'begin': chunk[0]['begin'],
                'end': chunk[-1]['end']
            }
            result.append(new_entry)
    return result


def change_tf(data, N, engine):
    '''
    РЕШИЛ делать без заполнения пустых интервалов. Мне они не нужны. А дальше посмотрим.
    '''
    result = []

    for item in data:
        # item - это строки минутного ТФ в виде словарей:
        # {'open': 22.495, 'close': 22.495, 'high': 22.495, 'low': 22.495, 'value': 186708.5, 'volume': 8300,
        # 'begin': '2024-07-10 09:59:00', 'end': '2024-07-10 09:59:59'}
        # дополняем каждый такой словарь значением минуты начала минутного бара:
        item['minutes_value'] = int(item['begin'].split(':')[1])
    # группируем в словарь по дням: {'2024-07-10': [{'open': 21.17, 'close': 21.17, 'high': 21.17, 'low': 21.17, ...
    grouped_data = {key: list(group) for key, group in itertools.groupby(data, key=lambda x: x['begin'][:10])}
    refilled_data_list = [fill_missing_time(group) for group in grouped_data.values()]

    for minute_data in refilled_data_list:
        # Вызываем функцию convert_to_higher_timeframe для каждого дня
        daily_result = convert_to_higher_timeframe(minute_data, N)
        # Добавляем результат агрегации в общий список
        result.extend(daily_result)
    return result
