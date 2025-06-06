import logging  # Выводим лог на консоль и в файл
from datetime import datetime, timezone, timedelta, UTC
from time import time
import os.path

import pandas as pd

from TinkoffPy import TinkoffPy  # Работа с Tinkoff Invest API из Python
from TinkoffPy.grpc.marketdata_pb2 import GetCandlesRequest, GetCandlesResponse
from google.protobuf.json_format import MessageToDict


logger = logging.getLogger('TinkoffPy.Bars')  # Будем вести лог. Определяем здесь, т.к. возможен внешний вызов ф-ии
datapath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'Data', 'Tinkoff', '')  # Путь сохранения файла истории
delimiter = '\t'  # Разделитель значений в файле истории. По умолчанию табуляция
dt_format = '%d.%m.%Y %H:%M'  # Формат представления даты и времени в файле истории. По умолчанию русский формат


# noinspection PyShadowingNames
def load_candles_from_file(class_code, security_code, tf) -> pd.DataFrame:
    """Получение бар из файла

    :param str class_code: Код режима торгов
    :param str security_code: Код тикера
    :param str tf: Временной интервал https://ru.wikipedia.org/wiki/Таймфрейм
    """
    filename = f'{datapath}{class_code}.{security_code}_{tf}.txt'
    if os.path.isfile(filename):  # Если файл существует
        logger.info(f'Получение файла {filename}')
        file_bars = pd.read_csv(filename,  # Имя файла
                                sep=delimiter,  # Разделитель значений
                                usecols=['datetime', 'open', 'high', 'low', 'close', 'volume'],  # Для ускорения обработки задаем колонки, которые будут нужны для исследований
                                parse_dates=['datetime'],  # Колонку datetime разбираем как дату/время
                                dayfirst=True,  # В дате/времени сначала идет день, затем месяц и год
                                index_col='datetime')  # Индексом будет колонка datetime  # Дневки тикера
        file_bars['datetime'] = file_bars.index  # Колонка datetime нужна, чтобы не удалять одинаковые OHLCV на разное время
        logger.info(f'Первый бар    : {file_bars.index[0]:{dt_format}}')
        logger.info(f'Последний бар : {file_bars.index[-1]:{dt_format}}')
        logger.info(f'Кол-во бар    : {len(file_bars)}')
        return file_bars
    else:  # Если файл не существует
        logger.warning(f'Файл {filename} не найден')
        return pd.DataFrame()


# noinspection PyShadowingNames
def get_candles_from_provider(tp_provider, class_code, security_code, tf, next_bar_open_utc=None) -> pd.DataFrame:
    """Получение бар из провайдера

    :param TinkoffPy tp_provider: Провайдер Tinkoff
    :param str class_code: Код режима торгов
    :param str security_code: Код тикера
    :param str tf: Временной интервал https://ru.wikipedia.org/wiki/Таймфрейм
    :param datetime next_bar_open_utc: Первый возможный бар по UTC
    """
    si = tp_provider.get_symbol_info(class_code, security_code)  # Информация о тикере
    time_frame, intraday = tp_provider.timeframe_to_tinkoff_timeframe(tf)  # Временной интервал Tinkoff, внутридневной интервал
    _, td = tp_provider.tinkoff_timeframe_to_timeframe(time_frame)  # Временной интервал для имени файла и максимальный период запроса
    logger.info(f'Получение истории {class_code}.{security_code} {tf} из Tinkoff')
    todate_utc = datetime.now(UTC)  # Будем получать бары до текущей даты и времени UTC
    new_bars_list = []  # Список новых бар
    while True:  # Будем получать бары пока не получим все
        request = GetCandlesRequest(instrument_id=si.figi, interval=time_frame)  # Запрос на получение бар
        from_ = getattr(request, 'from')  # т.к. from - ключевое слово в Python, то получаем атрибут from из атрибута интервала
        to_ = getattr(request, 'to')  # Аналогично будем работать с атрибутом to для единообразия
        from_.seconds = int(next_bar_open_utc.timestamp())  # Дата и время начала интервала UTC
        todate_min_utc = min(todate_utc, next_bar_open_utc + td)  # До какой даты можем делать запрос
        to_.seconds = int(todate_min_utc.timestamp())  # Дата и время окончания интервала UTC
        candles: GetCandlesResponse = tp_provider.call_function(tp_provider.stub_marketdata.GetCandles, request)  # Получаем ответ на запрос бар
        if not candles:  # Если бары не получены
            logger.error('Ошибка при получении истории: История не получена')
            return pd.DataFrame()  # то выходим, дальше не продолжаем
        candles_dict = MessageToDict(candles, always_print_fields_with_no_presence=True)  # Переводим в словарь из JSON
        if 'candles' not in candles_dict:  # Если бар нет в словаре
            logger.error(f'Ошибка при получении истории: {candles_dict}')
            return pd.DataFrame()  # то выходим, дальше не продолжаем
        new_bars_dict = candles_dict['candles']  # Переводим в словарь/список
        if len(new_bars_dict) > 0:  # Если пришли новые бары
            # Дату/время UTC получаем в формате ISO 8601. Пример: 2023-06-16T20:01:00Z
            # В статье https://stackoverflow.com/questions/127803/how-do-i-parse-an-iso-8601-formatted-date описывается проблема, что Z на конце нужно убирать
            first_bar_dt_utc = datetime.fromisoformat(new_bars_dict[0]['time'][:-1])  # Дата и время начала первого полученного бара в UTC
            first_bar_open_dt = tp_provider.utc_to_msk_datetime(first_bar_dt_utc) if intraday else \
                datetime(first_bar_dt_utc.year, first_bar_dt_utc.month, first_bar_dt_utc.day)  # Дату/время переводим из UTC в МСК
            last_bar_dt_utc = datetime.fromisoformat(new_bars_dict[-1]['time'][:-1])  # Дата и время начала последнего полученного бара в UTC
            last_bar_open_dt = tp_provider.utc_to_msk_datetime(last_bar_dt_utc) if intraday else \
                datetime(last_bar_dt_utc.year, last_bar_dt_utc.month, last_bar_dt_utc.day)  # Дату/время переводим из UTC в МСК
            logger.debug(f'Получены бары с {first_bar_open_dt} по {last_bar_open_dt}')
            for new_bar in new_bars_dict:  # Пробегаемся по всем полученным барам
                if not new_bar['isComplete']:  # Если добрались до незавершенного бара
                    break  # то это последний бар, больше бары обрабатывать не будем
                dt_utc = datetime.fromisoformat(new_bar['time'][:-1])  # Дата и время начала бара в UTC
                dt = tp_provider.utc_to_msk_datetime(dt_utc) if intraday else datetime(dt_utc.year, dt_utc.month, dt_utc.day)  # Дату/время переводим из UTC в МСК
                open_ = tp_provider.tinkoff_price_to_price(class_code, security_code, tp_provider.dict_quotation_to_float(new_bar['open']))
                high = tp_provider.tinkoff_price_to_price(class_code, security_code, tp_provider.dict_quotation_to_float(new_bar['high']))
                low = tp_provider.tinkoff_price_to_price(class_code, security_code, tp_provider.dict_quotation_to_float(new_bar['low']))
                close = tp_provider.tinkoff_price_to_price(class_code, security_code, tp_provider.dict_quotation_to_float(new_bar['close']))
                volume = int(new_bar['volume'])  # Объем в лотах
                new_bars_list.append({'datetime': dt, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})
        next_bar_open_utc = todate_min_utc + timedelta(minutes=1) if intraday else todate_min_utc + timedelta(days=1)  # Смещаем время на возможный следующий бар UTC
        if next_bar_open_utc > todate_utc:  # Если пройден весь интервал
            break  # то выходим из цикла получения бар
    if len(new_bars_list) == 0:  # Если новых записей нет
        logger.info('Новых записей нет')
        return pd.DataFrame()  # то выходим, дальше не продолжаем
    pd_bars = pd.DataFrame(new_bars_list)  # Список новых бар -> DataFrame
    pd_bars = pd_bars[['datetime', 'open', 'high', 'low', 'close', 'volume']]  # Отбираем нужные колонки. Дата и время нужна, чтобы не удалять одинаковые OHLCV на разное время
    pd_bars.index = pd_bars['datetime']  # Дата/время также будет индексом
    logger.info(f'Первый бар    : {pd_bars.index[0]:{dt_format}}')
    logger.info(f'Последний бар : {pd_bars.index[-1]:{dt_format}}')
    logger.info(f'Кол-во бар    : {len(pd_bars)}')
    return pd_bars


# noinspection PyShadowingNames
def save_candles_to_file(tp_provider, class_code, security_codes, tf='D1',
                         skip_first_date=False, skip_last_date=False, four_price_doji=False):
    """Получение новых бар из провайдера, объединение с имеющимися барами в файле (если есть), сохранение бар в файл

    :param TinkoffPy tp_provider: Провайдер Tinkoff
    :param str class_code: Код площадки
    :param tuple[str] security_codes: Коды тикеров в виде кортежа
    :param str tf: Временной интервал https://ru.wikipedia.org/wiki/Таймфрейм
    :param bool skip_first_date: Убрать бары на первую полученную дату
    :param bool skip_last_date: Убрать бары на последнюю полученную дату
    :param bool four_price_doji: Оставить бары с дожи 4-х цен
    """
    _, intraday = tp_provider.timeframe_to_tinkoff_timeframe(tf)  # Временной интервал Tinkoff, внутридневной интервал
    # tf, td = tp_provider.tinkoff_timeframe_to_timeframe(interval)  # Временной интервал для имени файла и максимальный период запроса
    # _, intraday = tp_provider.timeframe_to_tinkoff_timeframe(tf)  # Внутридневные бары
    for security_code in security_codes:  # Пробегаемся по всем тикерам
        try:  # Оборачиваем обработку каждого тикера в try-except
            si = tp_provider.get_symbol_info(class_code, security_code)  # Информация о тикере
            
            if si is None:  # Если информация о тикере не найдена
                logger.warning(f'Информация о тикере {class_code}.{security_code} не найдена, пропускаем')
                continue  # Переходим к следующему тикеру
            
            file_bars = load_candles_from_file(class_code, security_code, tf)  # Получаем бары из файла
            if file_bars.empty:  # Если файла нет
                next_bar_open_utc = datetime.fromtimestamp(si.first_1min_candle_date.seconds, timezone.utc) if intraday else \
                    datetime.fromtimestamp(si.first_1day_candle_date.seconds, timezone.utc)  # Первый минутный/дневной бар истории
            else:  # Если получили бары из файла
                last_date: datetime = file_bars.index[-1]  # Дата и время последнего бара по МСК
                next_bar_open_utc = tp_provider.msk_to_utc_datetime(last_date + timedelta(minutes=1), True) if intraday else \
                    last_date.replace(tzinfo=timezone.utc) + timedelta(days=1)  # Смещаем время на возможный следующий бар по UTC
            pd_bars = get_candles_from_provider(tp_provider, class_code, security_code, tf, next_bar_open_utc)  # Получаем бары из провайдера
            if pd_bars.empty:  # Если бары не получены
                logger.info('Новых бар нет')
                continue  # то переходим к следующему тикеру, дальше не продолжаем
            if file_bars.empty and skip_first_date:  # Если файла нет, и убираем бары на первую дату
                len_with_first_date = len(pd_bars)  # Кол-во бар до удаления на первую дату
                first_date = pd_bars.index[0].date()  # Первая дата
                pd_bars.drop(pd_bars[(pd_bars.index.date == first_date)].index, inplace=True)  # Удаляем их
                logger.warning(f'Удалено бар на первую дату {first_date}: {len_with_first_date - len(pd_bars)}')
            if skip_last_date:  # Если убираем бары на последнюю дату
                len_with_last_date = len(pd_bars)  # Кол-во бар до удаления на последнюю дату
                last_date = pd_bars.index[-1].date()  # Последняя дата
                pd_bars.drop(pd_bars[(pd_bars.index.date == last_date)].index, inplace=True)  # Удаляем их
                logger.warning(f'Удалено бар на последнюю дату {last_date}: {len_with_last_date - len(pd_bars)}')
            if not four_price_doji:  # Если удаляем дожи 4-х цен
                len_with_doji = len(pd_bars)  # Кол-во бар до удаления дожи
                pd_bars.drop(pd_bars[(pd_bars.high == pd_bars.low)].index, inplace=True)  # Удаляем их по условия High == Low
                logger.warning(f'Удалено дожи 4-х цен: {len_with_doji - len(pd_bars)}')
            if len(pd_bars) == 0:  # Если нечего объединять
                logger.info('Новых бар нет')
                continue  # то переходим к следующему тикеру, дальше не продолжаем
            if not file_bars.empty:  # Если файл существует
                pd_bars = pd.concat([file_bars, pd_bars])  # Объединяем файл с данными из Tinkoff
                pd_bars = pd_bars[~pd_bars.index.duplicated(keep='last')]  # Убираем дубликаты самым быстрым методом
                pd_bars.sort_index(inplace=True)  # Сортируем по индексу заново
            pd_bars = pd_bars[['open', 'high', 'low', 'close', 'volume']]  # Отбираем нужные колонки. Дата и время будет экспортирована как индекс
            filename = f'{datapath}{class_code}.{security_code}_{tf}.txt'
            logger.info('Сохранение файла')
            pd_bars.to_csv(filename, sep=delimiter, date_format=dt_format)
            logger.info(f'Первый бар    : {pd_bars.index[0]}')
            logger.info(f'Последний бар : {pd_bars.index[-1]}')
            logger.info(f'Кол-во бар    : {len(pd_bars)}')
            logger.info(f'В файл {filename} сохранено записей: {len(pd_bars)}')
            
        except Exception as e:  # Ловим любые ошибки при обработке тикера
            logger.error(f'Ошибка при обработке тикера {class_code}.{security_code}: {e}')
            continue  # Переходим к следующему тикеру


if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    start_time = time()  # Время начала запуска скрипта
    tp_provider = TinkoffPy()  # Подключаемся ко всем торговым счетам

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщения
                        datefmt='%d.%m.%Y %H:%M:%S',  # Формат даты
                        level=logging.DEBUG,  # Уровень логируемых событий NOTSET/DEBUG/INFO/WARNING/ERROR/CRITICAL
                        handlers=[logging.FileHandler('Bars.log', encoding='utf-8'), logging.StreamHandler()])  # Лог записываем в файл и выводим на консоль
    logging.Formatter.converter = lambda *args: datetime.now(tz=tp_provider.tz_msk).timetuple()  # В логе время указываем по МСК

    class_code = 'TQBR'  # Акции ММВБ
    security_codes = ('SBER', 'GAZP')  # Для тестов
    security_codes = ('ABIO', 'ABRD', 'AFKS', 'AFLT', 'AGRO', 'AKRN', 'ALRS', 'AMEZ', 'APRI', 'APTK', 'AQUA', 'ARSA', 'ASSB', 'ASTR', 'AVAN', 'BANE', 'BANEP', 'BELU', 'BISVP', 'BLNG', 'BRZL', 'BSPB', 'BSPBP', 'CARM', 'CBOM', 'CHGZ', 'CHKZ', 'CHMF', 'CHMK', 'CNRU', 'CNTL', 'CNTLP', 'DATA', 'DELI', 'DIAS', 'DIOD', 'DVEC', 'DZRD', 'DZRDP', 'EELT', 'ELFV', 'ELMT', 'ENPG', 'ETLN', 'EUTR', 'FEES', 'FESH', 'FIXP', 'FLOT', 'GAZA', 'GAZAP', 'GAZC', 'GAZP', 'GAZS', 'GAZT', 'GCHE', 'GECO', 'GEMA', 'GEMC', 'GMKN', 'GTRK', 'HEAD', 'HIMCP', 'HNFG', 'HYDR', 'IGST', 'IGSTP', 'INGR', 'IRAO', 'IRKT', 'IVAT', 'JNOS', 'JNOSP', 'KAZT', 'KAZTP', 'KBSB', 'KCHE', 'KCHEP', 'KGKC', 'KGKCP', 'KLSB', 'KLVZ', 'KMAZ', 'KMEZ', 'KOGK', 'KRKN', 'KRKNP', 'KRKOP', 'KROT', 'KROTP', 'KRSB', 'KRSBP', 'KUZB', 'KZOS', 'KZOSP', 'LEAS', 'LENT', 'LIFE', 'LKOH', 'LMBZ', 'LNZL', 'LNZLP', 'LPSB', 'LSNG', 'LSNGP', 'LSRG', 'LVHK', 'MAGE', 'MAGEP', 'MAGN', 'MBNK', 'MDMG', 'MFGS', 'MFGSP', 'MGKL', 'MGNT', 'MGNZ', 'MGTS', 'MGTSP', 'MISB', 'MISBP', 'MOEX', 'MRKC', 'MRKK', 'MRKP', 'MRKS', 'MRKU', 'MRKV', 'MRKY', 'MRKZ', 'MRSB', 'MSNG', 'MSRS', 'MSTT', 'MTLR', 'MTLRP', 'MTSS', 'MVID', 'NAUK', 'NFAZ', 'NKHP', 'NKNC', 'NKNCP', 'NKSH', 'NLMK', 'NMTP', 'NNSB', 'NNSBP', 'NSVZ', 'NVTK', 'OGKB', 'OKEY', 'OMZZP', 'OZON', 'OZPH', 'PAZA', 'PHOR', 'PIKK', 'PLZL', 'PMSB', 'PMSBP', 'POSI', 'PRFN', 'PRMB', 'PRMD', 'QIWI', 'RAGR', 'RASP', 'RBCM', 'RDRB', 'RENI', 'RGSS', 'RKKE', 'RNFT', 'ROLO', 'ROSN', 'ROST', 'RTGZ', 'RTKM', 'RTKMP', 'RTSB', 'RTSBP', 'RUAL', 'RUSI', 'RZSB', 'SAGO', 'SAGOP', 'SARE', 'SAREP', 'SBER', 'SBERP', 'SELG', 'SFIN', 'SGZH', 'SIBN', 'SLEN', 'SMLT', 'SNGS', 'SNGSP', 'SOFL', 'SPBE', 'STSB', 'STSBP', 'SVAV', 'SVCB', 'SVET', 'SVETP', 'T', 'TASB', 'TASBP', 'TATN', 'TATNP', 'TGKA', 'TGKB', 'TGKBP', 'TGKN', 'TNSE', 'TORS', 'TORSP', 'TRMK', 'TRNFP', 'TTLK', 'TUZA', 'UGLD', 'UKUZ', 'UNAC', 'UNKL', 'UPRO', 'URKZ', 'USBN', 'UTAR', 'UWGN', 'VEON-RX', 'VGSB', 'VGSBP', 'VJGZ', 'VJGZP', 'VKCO', 'VLHZ', 'VRSB', 'VRSBP', 'VSEH', 'VSMO', 'VSYD', 'VSYDP', 'VTBR', 'WTCM', 'WTCMP', 'WUSH', 'X5', 'YAKG', 'YDEX', 'YKEN', 'YKENP', 'YRSB', 'YRSBP', 'ZAYM', 'ZILL', 'ZVEZ')    
    
    # class_code = 'SPBFUT'  # Фьючерсы
    # security_codes = ('SiM5', 'RIM5')  # Формат фьючерса: <Тикер><Месяц экспирации><Последняя цифра года> Месяц экспирации: 3-H, 6-M, 9-U, 12-Z
    # security_codes = ('USDRUBF', 'EURRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF', 'SBERF', 'GAZPF')  # Вечные фьючерсы ММВБ

    skip_last_date = True  # Если получаем данные внутри сессии, то не берем бары за дату незавершенной сессии
    # skip_last_date = False  # Если получаем данные, когда рынок не работает, то берем все бары
    save_candles_to_file(tp_provider, class_code, security_codes, 'D1', skip_last_date=skip_last_date, four_price_doji=True)  # Дневные бары
    # save_candles_to_file(tp_provider, class_code, security_codes, 'M60', skip_last_date=skip_last_date)  # Часовые бары
    # save_candles_to_file(tp_provider, class_code, security_codes, 'M15', skip_last_date=skip_last_date)  # 15-и минутные бары
    # save_candles_to_file(tp_provider, class_code, security_codes, 'M5', skip_last_date=skip_last_date)  # 5-и минутные бары
    # save_candles_to_file(tp_provider, class_code, security_codes, 'M1', skip_last_date=skip_last_date, four_price_doji=True)  # Минутные бары

    tp_provider.close_channel()  # Закрываем канал перед выходом

    logger.info(f'Скрипт выполнен за {(time() - start_time):.2f} с')