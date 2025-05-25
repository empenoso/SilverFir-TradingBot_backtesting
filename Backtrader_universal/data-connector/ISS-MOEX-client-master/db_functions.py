import pandas as pd
from constants import ENGINE_STR, CONNECT_ARGS
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import text


def clear_table(table_name):
    try:
        with MySQLDatabase() as db:
            query = f"DELETE FROM {table_name};"
            result = db.execute(query)
            print(f"Поздравляю. Очищено {result.rowcount} строк в Таблице {table_name}.")
    except Exception as e:
        print(f"Error: {e}")


def load_table(table, df):
    """
    Это Update произвольных таблиц данными из полученного pandas dataframe, включая основные таблицы с MOEX:
    engines, markets, boards, boardgroups, durations, securitytypes, securitygroups, securitycollections.
    """
    # Формируем список столбцов таблицы
    columns = df.columns.tolist()
    column_placeholders = ', '.join([f":{col}" for col in columns])
    query_arq = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in columns])
    query = (f"INSERT INTO `{table}` "
             f"({', '.join([f'`{col}`' for col in columns])}) "
             f"VALUES ({column_placeholders}) "
             f"ON DUPLICATE KEY UPDATE {query_arq}")
    df_to_dict = df.to_dict(orient='records')
    # print(df_to_dict)

    try:
        with MySQLDatabase() as db:
            db.execute(query, df_to_dict)

    except Exception as e:
        print(f"Error: {e}")


def make_table_for_app(main_tbl, new_tbl):  # main_table_search в БД
    """
    Копирование основной таблицы с созданием новых полей и прореживанием существующих
    main_table -> main_table_search
     """
    try:
        with MySQLDatabase() as db:
            drop_table_query = f"DROP TABLE IF EXISTS {new_tbl};"  # Удаляем таблицу, если она уже существует
            create_table_query = f"""
                    CREATE TABLE {new_tbl} AS
                    SELECT
                        mt.id,
                        mt.secid,
                        mt.shortname,
                        mt.name,
                        mt.is_traded,
                        mt.`type`,
                        mt.`group`,
                        mt.primary_boardid,
                        m.trade_engine_name,
                        m.market_name,
                        CONCAT(mt.secid, mt.shortname, mt.name) AS mask
                    FROM
                        {main_tbl} mt
                    JOIN
                        boards b ON mt.primary_boardid = b.boardid
                    JOIN
                        markets m ON b.engine_id = m.trade_engine_id AND b.market_id = m.market_id
                    WHERE
                        mt.primary_boardid IS NOT NULL;
                """
            db.execute(drop_table_query)
            db.execute(create_table_query)
            print(f"Таблица {new_tbl} успешно создана из таблицы {main_tbl}.")
    except Exception as e:
        print(f"Error: {e}")


def load_all_sec(df):
    """
    Обновляем таблицу last_arrival новыми данными. Если все ок, тоже делаем с main_table.
    Если все ок, обновляем таблицу main_table_search, она нужна для поиска инструментов в окне приложения.
    """

    print(f"Вошли в процедуру обновления основной таблицы main_table, {datetime.now()}")
    print(f"Очищаем таблицу 'last_arrival'")
    clear_table('last_arrival')

    print(f"Заливаем в таблицу 'last_arrival' данные, полученные с Биржи, {datetime.now()}")
    load_table('last_arrival', df)

    print(f"Заливаем в таблицу 'main_table' данные, полученные с Биржи, {datetime.now()}")
    load_table('main_table', df)

    print(f"Очищаем таблицу 'main_table_search' {datetime.now()}")
    clear_table('main_table_search')

    print(f"Заполняем таблицу 'main_table_search', {datetime.now()}")
    make_table_for_app('main_table', 'main_table_search')

    print(f'Процесс обновления таблиц завершен, {datetime.now()}')


def get_security_attributes(sec_id):
    """
    Возвращает словарь вида:
    {'secid': 'SiH3', 'primary_boardid': 'RFUD', 'market_name': 'forts', 'trade_engine_name': 'futures'}
    """
    query = f"""
    SELECT
        secid, name, shortname, primary_boardid, market_name, trade_engine_name
    FROM
        main_table_search
    WHERE
        secid = '{sec_id}';
    """

    try:
        with MySQLDatabase() as db:
            # result = db.execute(query).fetchone()
            result = db.execute(query)
            row = result.fetchone()
            if row is None:
                print(f"No data found for sec_id: {sec_id}")
                return None
            columns = result.keys()
            return dict(zip(columns, row))
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_start_df(ss: str, market_groups: list) -> pd.DataFrame:
    """
    Выборка значений для DD
    :param ss: строка поиска, если что-то набрано в DD
    :param market_groups: набор групп инструментов из формы, например:
    market_groups = ['stock_shares', 'stock_foreign_shares', 'stock_bonds', 'stock_eurobond', 'futures_forts']
    :return: Df для заполнения DD
    """
    mg = f"('{market_groups[0]}')" if len(market_groups) == 1 else f"{tuple(market_groups)}"
    columns_to_select = ['secid', 'shortname', '`name`', '`group`', 'mask']
    columns = ', '.join(columns_to_select)
    if not ss:
        query = f"SELECT {columns} FROM main_table_search WHERE `group` IN {mg} ORDER BY is_traded desc, id LIMIT 50;"
    else:
        query = (f"SELECT {columns} FROM main_table_search WHERE `group` IN {mg} AND mask LIKE '%%{ss}%%' "
                 f"ORDER BY is_traded desc, id LIMIT 50;")

    with MySQLDatabase() as db:
        df = pd.read_sql(query, db.connection, index_col='mask')

    return df


class MySQLDatabase:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = create_engine(ENGINE_STR, connect_args=CONNECT_ARGS)
        except Exception as e:
            print(f"Error during connection: {e}")
            self.connection = None

    def disconnect(self):
        if self.connection:
            self.connection.dispose()
            self.connection = None

    def fetch_all(self, query):
        if self.connection is None:
            raise ValueError("Engine is not connected")
        try:
            with self.connection.connect() as conn:
                result = conn.execute(text(query))
                return result.fetchall()
        except Exception as e:
            print(f"Error: {e}")
            return None

    def execute(self, query, params=None):
        if self.connection is None:
            raise ValueError("Engine is not connected")
        try:
            with self.connection.begin() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                conn.commit()
                return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def __enter__(self):   # автоматически вызывает подключение и отключение от базы данных.
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


# test = get_start_df('SiH', ['stock_shares', 'stock_foreign_shares', 'stock_bonds', 'stock_eurobond', 'futures_forts'])
# test = get_security_attributes('SiL3')
# test = get_security_attributes('SiM3')
# print(test)

# clear_table('main_table_search')
# make_table_for_app('main_table', "main_table_search")

# Тестовый df для имитации ответа биржи из функции get_all_securities()

# df = pd.DataFrame({
#     'id': [421883997, 421883998, 421883999, 421884000, 421884001],
#     'secid': ['RN38500BQ3', 'RN38501BQ3', 'RN38502BQ3', 'RN38503BQ3', 'RN38504BQ3'],
#     'shortname': ['ROSN-6.23M170523PA38500', 'ROSN-6.23M170523PA38501', 'ROSN-6.23M170523PA38502',
#                   'ROSN-6.23M170523PA38503', 'ROSN-6.23M170523PA38504'],
#     'regnumber': [None, None, None, None, None],
#     'name': ['Марж. амер. Put 38500 с исп. 17 мая на фьюч. контр. ROSN-6.23',
#              'Марж. амер. Put 38501 с исп. 17 мая на фьюч. контр. ROSN-6.23',
#              'Марж. амер. Put 38502 с исп. 17 мая на фьюч. контр. ROSN-6.23',
#              'Марж. амер. Put 38503 с исп. 17 мая на фьюч. контр. ROSN-6.23',
#              'Марж. амер. Put 38504 с исп. 17 мая на фьюч. контр. ROSN-6.23'],
#     'isin': [None, None, None, None, None],
#     'is_traded': [0.0, 0.0, 0.0, 0.0, 0.0],
#     'emitent_id': [None, None, None, None, None],
#     'emitent_title': [None, None, None, None, None],
#     'emitent_inn': [None, None, None, None, None],
#     'emitent_okpo': [None, None, None, None, None],
#     'gosreg': [None, None, None, None, None],
#     'type': ['option', 'option', 'option', 'option', 'option'],
#     'group': ['futures_options', 'futures_options', 'futures_options', 'futures_options', 'futures_options'],
#     'primary_boardid': ['ROPD', 'ROPD', 'ROPD', 'ROPD', 'ROPD'],
#     'marketprice_boardid': [None, None, None, None, None]
# })

# load_table('last_arrival_copy', df)
# clear_table('last_arrival')
