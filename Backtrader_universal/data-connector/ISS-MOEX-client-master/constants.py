from collections import OrderedDict
import platform
from config import Config
from sqlalchemy.engine.url import URL

# print(platform.system())
if platform.system() == "Windows":
    OS_TYPE = "Windows"
    host = 'localhost'
    user = Config.login
    password = Config.password
    database = 'moex_db'
    unix_socket = ""
    CONNECT_ARGS = {}
elif platform.system() == "Darwin":
    """
    Macos. После установки mysql инициализировать db в панели управления. 
    """
    OS_TYPE = "MacOS"
    host = 'localhost'
    user = Config.login
    password = Config.password
    database = 'moex_db'
    unix_socket = '/tmp/mysql.sock'
    CONNECT_ARGS = {'unix_socket': unix_socket}
else:
    OS_TYPE = "Other OS"
    host = '91.201.52.115'
    user = Config.unix_user
    password = Config.unix_pass
    database = 'c85994_moex_backtrader_ru'
    unix_socket = "/run/mysqld/mysqld.sock"
    CONNECT_ARGS = {'unix_socket': unix_socket}

ENGINE_STR = URL.create(
    drivername="mysql+pymysql",
    username=user,
    password=password,
    host=host,
    database=database
)


# securitygroups
MARKETS = {
    "Акции": ['stock_shares', 'stock_foreign_shares'],
    "Облигации": ['stock_bonds', 'stock_eurobond'],
    "Фьючерсы": ['futures_forts'],
    "Опционы": ['futures_options'],
    "Индексы": ['stock_index', 'currency_indices'],
    "Прочее": ['currency_selt', 'stock_dr', 'stock_ppif', 'stock_etf', 'currency_metal', 'stock_qnv', 'stock_gcc',
               'stock_deposit', 'currency_futures', 'stock_mortgage', 'commodity_futures',
               'stock_credits', 'agro_commodities', 'stock_repo_basket']
}

TF = OrderedDict({
    # '': 'тики',
    1: '1 мин',
    5: '5 мин', # NO
    10: '10 мин',
    15: '15 мин', # NO
    30: '30 мин', # NO
    60: '1 час',
    24: '1 день',
    7: '1 неделя',
    31: '1 месяц',
    4: '1 квартал'
})

PERS = OrderedDict({
    '': '0',
    1: '1',
    5: '5', # NO
    10: '10',
    15: '15', # NO
    30: '30', # NO
    60: '60',
    24: 'D',
    7: 'W',
    31: 'M',
    4: 'Q'
})


DATE_FORMAT = {
    '%Y%m%d': 'ггггммдд',
    '%y%m%d': 'ггммдд',
    '%d%m%y': 'ддммгг',
    '%d/%m/%y': 'дд/мм/гг',
    '%m/%d/%y': 'мм/дд/гг'
}

TIME_FORMAT = {
    '%H%M%S': 'ччммсс',
    '%H%M': 'ччмм',
    '%H:%M:%S': 'чч:мм:сс',
    '%H:%M': 'чч:мм'
}

FIELD_SEPARATOR = {
    ',': "запятая (,)",
    '.': "точка (.)",
    ';': "точка с запятой (;)",
    '\t': "табуляция (Tab)",
    ' ': "пробел ( )"
}

DIGIT_SEPARATOR = {
    "нет": "нет",
    ',': "запятая (,)",
    '.': "точка (.)",
    ' ': "пробел ( )",
    "'": "кавычка (')"
}

RECORD_FORMAT = [
        "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL",
        "TICKER, PER, DATE, TIME, OPEN, HIGH, LOW, CLOSE",
        "TICKER, PER, DATE, TIME, CLOSE, VOL",
        "TICKER, PER, DATE, TIME, CLOSE",
        "DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL",
        # "TICKER, PER, DATE, TIME, LAST, VOL",
        # "TICKER, DATE, TIME, LAST, VOL",
        # "TICKER, DATE, TIME, LAST",
        # "DATE, TIME, LAST, VOL",
        # "DATE, TIME, LAST",
        # "DATE, TIME, LAST, VOL, ID",
        # "DATE, TIME, LAST, VOL, ID, OPER"
]

MOEX_WARNING = """Данные по индексам и инструментам Московской Биржи предоставлены ПАО Московская Биржа. 
Перераспространение информации только с разрешения Московской Биржи. Пользователи имеют право использовать, хранить и 
обрабатывать биржевую информацию, но не могут без письменного согласия Московской Биржи осуществлять её дальнейшую 
передачу в любом виде и любыми средствами, включая электронные, механические, фотокопировальные, записывающие или 
другие, её трансляцию, в том числе средствами телевизионного и радиовещания, её демонстрацию на интернет-сайтах, а 
также её использование в игровых, тренажерных и иных системах, предусматривающих демонстрацию и/или передачу биржевой 
информации, и для расчёта производной информации, предназначенной для дальнейшего публичного распространения."""

ALL_CATALOGS = ['engines', 'markets', 'boards', 'boardgroups', 'durations', 'securitytypes', 'securitygroups', 'securitycollections']

