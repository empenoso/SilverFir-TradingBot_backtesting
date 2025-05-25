import pandas as pd
from pandas import DataFrame
import aiomoex
from constants import PERS
from tf import change_tf
import aiohttp
import os


async def get_history_intervals(sec_id, board, market, engine):
    """
    Предполагается, что после выбора пользователем инструмента приложение сделает запрос get_security_attributes
    и запомнит полученные данные (возвращается словарь вида):
    {'secid': 'SiH3', 'primary_boardid': 'RFUD', 'market_name': 'forts', 'trade_engine_name': 'futures'}
    И затем вызовет эту функцию, указав полученные ранее значения в виде аргументов. И также сохранит для
    отображения доступных интервалов с историческими данными полученный ответ.
    Интервалы для разных инструментов можно получить с помощью 2-х функций:
    - get_board_candle_borders: с указанием secid, board, market, engine
    - get_market_candle_borders: с указанием secid, market, engine
    При этом есть 3 варианта:
    - Интервалы доступны только при запросе через get_board_candle_borders
    - Интервалы доступны только при запросе через get_market_candle_borders
    - Интервалы доступны только при запросе по обеим функциям.
    Поэтому запрашиваем сначала через get_board_candle_borders. Если Интервалы не получены - вызываем
    get_market_candle_borders.

    :param sec_id:
    :param board:
    :param market:
    :param engine:
    :return: кортеж, первый элемент: b, m или n (str). Если данные по Интервалам есть на market - отдаем их.
            Если нет - запрашиваем board.
        b - получили интервалы функцией get_board_candle_borders
        m - получили интервалы функцией get_market_candle_borders
        n - не получили интервалы ни той, ни другой функцией
        Второй элемент кортежа - интервалы (список словарей):
         [{'begin': '2021-03-17 14:56:00', 'end': '2023-03-16 13:59:00', 'interval': 1},
         {'begin': '2021-01-01 00:00:00', 'end': '2023-01-01 00:00:00', 'interval': 4}, ...]
         или None, если интервалы не найдены.
    """
    async with aiohttp.ClientSession() as session:
        data = await aiomoex.get_market_candle_borders(session, security=sec_id, market=market, engine=engine)
        if data:
            print(f'Для {sec_id} Интервалы есть на market')
            return 'm', data

        data = await aiomoex.get_board_candle_borders(session, security=sec_id, board=board,
                                                      market=market, engine=engine)
        if data:
            print(f'Для {sec_id} Интервалы есть ТОЛЬКО на board')
            return 'b', data

        print(f'Для {sec_id} нет Интервалов на Бирже')
        return 'n', None


async def get_candles_history(sec_id, board, market, engine, start, end, user_sets: dict, tf):
    """
    Получение исторических данных OHLC.
    res = get_candles_history(secid, board, market, engine, start_date, end_date, user_settings, durations)
    user_settings = dict(
        file_name=file_name,
        file_type=file_type,
        contract_name=contact_name,
        date_format=date_format,
        time_format=time_format,
        candle_start=rb_candle,
        fields_sep=field_separator,
        digits_sep=digit_separator,
        row_format=record_format,
        header=file_header_cl,
    )
    Вход: (sec, start_date, end_date, durations, file_type, file_name, contact_name, date_format, time_format,
                    field_separator, digit_separator, record_format, rb_candle, file_header_cl)
    Пример:
    Вход: sec = 'AFKS', 2023-12-14, 2024-01-14, 1, file_type ='AFKS_141223_140124', file_name = 'AFKS',
    contact_name ='csv', date_format = '%d/%m/%y', time_format = '%H:%M', field_separator = ';',
    digit_separator = 'нет', record_format = 'TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL',
    rb_candle = 'begin', file_header_cl = ['Yes']

    :param sec_id:
    :param board:
    :param market:
    :param engine:
    :param start:
    :param end:
    :param user_sets: Список выбранных пользователем настроек файла истории
    :param tf: ТФ, или Интервал в терминологии MOEX
    :return: Список интервалов, None - если нет.
    """
    print(f'Вход get_candles_history. {sec_id = }, {tf = }')
    if tf in (5, 15, 30):
        resample_tf_value = tf
        tf = 1
    else:
        resample_tf_value = None

    async with aiohttp.ClientSession() as session:
        data = await aiomoex.get_market_candles(session, sec_id, interval=tf, start=start, end=end, market=market,
                                                engine=engine)
        if data:
            print('История с маркета сформирована')
        else:
            data = await aiomoex.get_board_candles(session, sec_id, interval=tf, start=start, end=end, board=board,
                                                   market=market, engine=engine)
            if data:
                print('История с борда сформирована')
            else:
                print('История не найдена на бирже')
                return None

        if resample_tf_value:
            tf = resample_tf_value
            data = change_tf(data, tf, engine)
        res = make_file(data, tf, user_sets, market)  # формируем файл с историей
        return res


def make_file(data, tf, us: dict, market):
    """
    Формирование итогового файла.
    User_settings:
    0 - имя файла (будет формироваться сайтом)
    1 - тип файла: csv или txt
    2 - имя контракта (для заполнения TICKER в первой колонке файла, будет формироваться сайтом)
    3 - формат даты:
        'ггггммдд'
        'ггммдд'
        'ддммгг'
        'дд/мм/гг'
        'мм/дд/гг'
    4 - формат времени:
        'ччммсс'
        'ччмм'
        'чч:мм:сс'
        'чч:мм'
    5 - Выдавать время, московское: True/False
    6 - Выдавать время, начала/окончания свечи: True/False
    7 - разделитель полей:
        "запятая (,)"
        "точка (.)"
        "точка с запятой (;)"
        "табуляция (>>)"
        "пробел ( )"
    8 -  разделитель разрядов:
        "нет"
        "точка (.)"
        "запятая (,)"
        "пробел (&nbsp)"
        "кавычка (')"
    9 - формат записи в файл:
        "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL"
        "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE"
        "TICKER, PER, DATE, TIME, CLOSE, VOL"
        "TICKER, PER, DATE, TIME, CLOSE"
        "DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL"
    10 - добавить заголовок файла: True/False
    11 - заполнять периоды без сделок: True/False

    :param us: словарь см. выше
    :param data: даннные с биржи
    :param tf: тайм-фрейм
    :param market: если это Индекс (`group` IN ('stock_index', 'currency_indices')),
    то вместо volume выводим в файл value
    :return: возвращаем df для отправки пользователю через dcc.send_data_frame
    """
    df: DataFrame = pd.DataFrame(data)
    if market == 'index':
        if 'volume' in df.columns:
            df.drop(columns=['volume'], inplace=True)
        df.rename(columns={'open': 'OPEN', 'close': 'CLOSE', 'high': 'HIGH', 'low': 'LOW', 'value': 'VOLUME'},
                  inplace=True)  # VOLUME = value, ибо Индексы имеют только value
    else:
        if 'value' in df.columns:
            df.drop(columns=['value'], inplace=True)
        df.rename(columns={'open': 'OPEN', 'close': 'CLOSE', 'high': 'HIGH', 'low': 'LOW', 'volume': 'VOLUME'},
                  inplace=True)  # VOLUME = volume
    df = df[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'begin', 'end']]

    # 0 и 1 - имя файла и тип
    csv_file_path = f"Users_Files/{us['file_name']}.{us['file_type']}"
    directory = os.path.dirname(csv_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 2 - имя контракта (для заполнения TICKER в первой колонке файла, будет формироваться сайтом)
    ticker = us['contract_name']

    # 3 - формат даты:
    date_format = us['date_format']
    time_format = us['time_format']

    # 6 - Выдавать время, начала/окончания свечи: True/False
    template = us['candle_start']
    df[template] = pd.to_datetime(df[template])
    df.insert(0, 'DATE', df[template].dt.strftime(date_format))
    df.insert(1, 'TIME', df[template].dt.strftime(time_format))
    df.drop(columns=['begin', 'end'], inplace=True)

    # 7 - разделитель полей
    fsep = us['fields_sep']

    # 8 - разделитель разрядов:
    if us['digits_sep'] != "нет":
        dsep = us['digits_sep']
        df[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']] = (
            df[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']].map(lambda x: '{:,.3f}'.format(x).replace(',', dsep)))

    # 9 - формат записи в файл:
    match us['row_format']:
        case "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL":
            df.insert(0, 'TICKER', ticker)
            df.insert(1, 'PER', PERS[tf])

        case "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE":
            df.insert(0, 'TICKER', ticker)
            df.insert(1, 'PER', PERS[tf])
            df.drop(columns=['VOLUME'], inplace=True)

        case "TICKER, PER, DATE, TIME, CLOSE, VOL":
            df.insert(0, 'TICKER', ticker)
            df.insert(1, 'PER', PERS[tf])
            df.drop(columns=['OPEN', 'HIGH', 'LOW'], inplace=True)

        case "TICKER, PER, DATE, TIME, CLOSE":
            df.insert(0, 'TICKER', ticker)
            df.insert(1, 'PER', PERS[tf])
            df.drop(columns=['OPEN', 'HIGH', 'LOW', 'VOLUME'], inplace=True)

        case "DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL":
            pass  # because nothing to do, all works already done!)

        case _:
            pass

    #     10 - добавить заголовок файла: True/False
    header = True if us['header'] == ['Yes'] else False
    df.to_csv(csv_file_path, sep=fsep, index=False, header=header)
    return df
