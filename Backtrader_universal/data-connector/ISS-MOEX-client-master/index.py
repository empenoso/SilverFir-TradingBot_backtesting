from datetime import datetime, timedelta
import asyncio
from dash import Dash, dcc, html, Input, Output, callback, State, no_update, ctx
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate
from db_functions import get_security_attributes, get_start_df
from api_async_functions import get_history_intervals, get_candles_history
from datetime import datetime
import pandas as pd
import dash_bootstrap_components as dbc
from collections import OrderedDict

from layouts.header_navbar import navbar
from layouts.middle_column import finish_export_card, chevron_up_icon, chevron_down_icon, int_button
from layouts.footer import get_footer
from constants import MARKETS, OS_TYPE, TF
import re
# import aiodns
from app import app
import aiomoex
from dns_client import DNS_ISSClient

# Внимание! Для работы на хостинге нужно импортировать библиотеку /Resolver requires aiodns library/
# Для локальной установки потребуется еще модуль cryptography


aiomoex.client.ISSClient = DNS_ISSClient
server = app.server  # Если не добавить эту строку, то не заработает на хостинге.

# favicon = '/assets/favicon.ico'
link_icon = html.I(className="bi bi-link-45deg", style={"font-size": "0.8em", 'align': 'center'})

main_container = [
    navbar(),
    dmc.LoadingOverlay(
        dbc.Container([
            # html.Link(rel='shortcut icon', href=favicon),
            dbc.Row([
                dbc.Col([finish_export_card], style={'overflowY': 'auto', 'height': '80vh'}),
            ]
            )],
            id='main_container'
        )
    ),
    get_footer(),
]

app.layout = html.Div([
    html.Meta(name='robots', content='index, follow'),
    dmc.LoadingOverlay(id="loading"),
    html.Div([], id='content')
])


def make_option(shortname, secid, name, mask):
    """
    Формирует записи в списке инструментов, каждая в две строки.
    В первой - короткое наименование инструмента shortname и его secid в скобках.
    Во второй - полное название инструмента name.
    """
    return {
        "label":
            html.Div([
                dbc.Row(
                    html.Div([f"{shortname} ({secid})"], style={"margin-bottom": "-4px", 'height': 'auto'}),
                ),
                dbc.Row(
                    html.Div([f"{name}"], style={'font-size': '70%'})
                )
            ], style={"text-overflow": "ellipsis", "white-space": "nowrap"}
            ),
        "value": f"{secid}",
        "search": f"{mask}"
    }


def options_list(dff: pd.DataFrame) -> list:
    """Формирует список инструментов для выбора в ниспадающем dropdown 'Инструмент'. Вызывается при наборе символов
    в поле 'Инструмент' и изменении групп инструментов (очистка списка)"""
    return [make_option(*a) for a in list(zip(dff['shortname'], dff['secid'], dff['name'], dff.index.values))]


def intervals_collapse_fuller(data):
    """
    Функция формирует список доступных Интервалов и ТФ котировок по выбранному Инструменту в виде элемента dbc.Collapse
    На входе ответ биржи на get_history_intervals(secid, board, market, engine) =
    [{'begin': '2011-12-15 10:00:00', 'end': '2024-07-10 18:59:59', 'interval': 1, 'board_group_id': 57}, ...
    На выходе:
    Collapse(children=Div(children=[Div('1. Интервал: 15.12.2011 - 10.07.2024, тайм-фрейм: 1 мин.'), Div('2. Интервал: .
    """
    data = sorted(data, key=lambda x: list(TF.keys()).index(x['interval']))
    rows = []
    for i, data_row in enumerate(data, 1):
        begin_date = full_date_to_short(data_row['begin'])
        end_date = full_date_to_short(data_row['end'])
        duration = TF.get(data_row['interval'], str(data_row['interval']))
        row_text = f"{i}. Интервал: {begin_date} - {end_date}, тайм-фрейм: {duration}."
        rows.append(html.Div(row_text))
    if any(item.get('interval') == 1 for item in data):  # 1 мин есть в data! (RU14PRMB1006 - нет)
        text = (f'{len(rows) + 1}. Тайм-фреймы 5, 15 и 30 минут будут сформированы из тайм-фрейма 1 мин. на интервале, '
                f'где он доступен')
        rows.append(html.Div([text], style={"font-weight": "bold"}))  # RU0008436241
    int_collapse = dbc.Collapse(
        html.Div(rows, style={
            'font-weight': 'normal',
            'font-size': '12px'}),
        id="int_collapse",
        is_open=False,
    )
    return int_collapse


def make_tf_list(intervals) -> list:
    """
    Манипуляции с тайм-фреймом. Возвращает отсортированный список словарей, содержащих все доступные ТФ
    (и их ключи из TF), включая 5, 15 и 30 мин., если есть ТФ = 1 мин.
    На входе:
    intervals = [{'begin': '2011-12-15 10:26:00', 'end': '2024-07-10 18:59:59', 'interval': 1, 'board_group_id': 57}, ...
    На выходе:
    options = [{'label': '1 мин', 'value': 1}, {'label': '5 мин', 'value': 5}, {'label': '10 мин', 'value': 10}, ... ]
    """
    if not intervals:
        return []
    tf_keys = [d['interval'] for d in intervals]
    if 1 in tf_keys:  # Если есть ТФ 1 мин, добавляем ТФ 5, 15, 30 мин
        tf_keys.extend([5, 15, 30])
    tf_dict = {tf: TF[tf] for tf in tf_keys}
    # Следующая операция обеспечивает сортировку ключей в tf_dict в том же порядке,
    # в каком они присутствуют в исходном словаре TF
    sorted_tf_dict = OrderedDict(sorted(tf_dict.items(), key=lambda x: list(TF.keys()).index(x[0])))
    options = [{'label': v, 'value': k} for k, v in sorted_tf_dict.items()]
    return options


def find_intervals_for_export_card_header(sec_args):
    secid, name, _, board, market, engine = sec_args
    print('Вызываю get_history_intervals ... ')
    status, res = asyncio.run(get_history_intervals(secid, board, market, engine))
    """
    status:
            b - получили доступные интервалы функцией get_board_candle_borders из модуля aiomoex 
            m - получили доступные интервалы функцией get_market_candle_borders из модуля aiomoex
            n - не получили доступные интервалы ни той, ни другой функцией
    res:
            соответственно ответ функций b, m, или None, если ответ не получен, например:
            [{'begin': '2011-12-15 10:26:00', 'end': '2024-07-10 18:59:59', 'interval': 1, 'board_group_id': 57}, ...
    возвращает:
            Полный Заголовок для центральной колонки, содержащий при положительном ответе (наличии истории на бирже)
            название инструмента, его id и ссылку на инструмент на moex, либо уведомление, что нет исторических данных.
    """
    if status == 'n':
        interval_info = html.Div(f"Для {secid} на MOEX нет исторических данных.",
                                 style={'color': 'red', 'font-size': '75%'})
        intervals_exist = {'intervals_exist': False}
        tf_list = []
    else:
        interval_info = html.Div([
            int_button,
            intervals_collapse_fuller(res)
        ])
        intervals_exist = {'intervals_exist': True}
        tf_list = make_tf_list(res)
    return (html.Div([
        html.Div(f"Экспорт котировок для: {name}", ),
        html.Div([f"SecId {secid}: ",
                  html.A([link_icon, " подробная информация об инструменте на MOEX."],
                         href=f"https://www.moex.com/ru/issue.aspx?board={board}&code={secid}",
                         target="_blank")],
                 style={'font-size': '75%'}),
        interval_info
    ]),
            intervals_exist,
            tf_list
    )


def dates_transform(dates):
    """ ['2023-12-13', '2024-01-13'] -> '131223_130124' """
    transformed_dates = [datetime.strptime(d, '%Y-%m-%d').strftime('%d%m%y') for d in dates] \
        if dates is not None else ['X', 'Y']
    return "_".join(transformed_dates)


def full_date_to_short(date) -> str:
    """'2011-12-15 10:00:00' -> '15.12.2011'"""
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')


# __________________________________________________________________________________________________
# Call-backs
# __________________________________________________________________________________________________

@app.callback(
    Output("loading", "children"),
    Output("content", "children"),
    Input("loading", "children"),

)
def update_content(children):
    return [], main_container


@app.callback(
    [Output("loading_message", "id"),
     Output("dropdown_sec", "value"),
     Output('dropdown_sec', 'options')],
    Input("market_filter", "value"),

)
def chips_values(selected_groups):
    """ Очистка sec id при смене Маркетов """
    # print(f'Мы меняем Рынки (или устанавливаем впервые)! {selected_groups = }')
    if not selected_groups:
        return "loading_message", None, []
    group_list = [item for group in selected_groups for item in MARKETS[group]]
    new_df = get_start_df(None, group_list)
    return "loading_message", None, options_list(new_df)


@app.callback(
    [Output("loading_message", "id", allow_duplicate=True),
     Output('dropdown_sec', 'options', allow_duplicate=True),
     Output('export_card_header', 'children'),
     Output('memory', 'data'),
     Output('store_intervals_exist', 'data'),
     Output('dd_durations', 'options'),
     Output('dd_durations', 'value')
     ],

    [Input('dropdown_sec', 'search_value'),
     Input('dropdown_sec', 'value')],
    [State("market_filter", "value")],
    prevent_initial_call=True,
)
def update_output(search_value, value, selected_groups):
    """Обработка выбора Инструмента в dd, фиксируем значение в value при выборе, записываем основные атрибуты
    Инструментов Store с id=memory и обновляем поля формы"""
    print(f"{datetime.now()}: Мы в DD выбора Инструмента! {search_value = }, {value = }")
    if search_value is None:
        print(f'ВЫХОД 0 - Загрузка-очистка формы')  # При загрузке, изменении в группах рынков и после очистки
        raise PreventUpdate

    if not selected_groups:
        print(f'ВЫХОД 1 - не выбраны группы Инструментов')
        return ("loading_message",
                no_update,  # [],
                html.Div("Не выбраны рынки для поиска инструмента", style={"color": "red", "font-weight": "bold"}),
                no_update,
                no_update,
                no_update,
                no_update
                )

    if search_value == '' and value is not None:  # Выбрали конкретный инструмент
        sec_attributes = get_security_attributes(value)
        secid, _, _, board, market, engine = sec_attributes.values()
        # secid, _, _, board, market, engine = sec_attributes
        print(f"ВЫХОД 2 - Инструмент выбран: {secid = }, {board = }, {market = }, {engine = }")
        export_card_header, intervals_exist, new_tf_list = find_intervals_for_export_card_header(sec_attributes.values())
        # export_card_header, intervals_exist, new_tf_list = find_intervals_for_export_card_header(sec_attributes)
        return ("loading_message",      # отображаем Loading ...
                no_update,              # список инструментов в поле выбора, не обновляем
                export_card_header,     # обновляем заголовок центральной колонки
                sec_attributes,         # запись выбранного инструмента в store мемори
                intervals_exist,        # запись наличия котировок на бирже
                new_tf_list,            # лист доступных ТФ
                24)                     # устанавливаем ТФ по умолчанию, день

    elif search_value == '' and value is None:
        print(f'ВЫХОД 3 - Очистка поля выбора Инструмента')  # Очистили dd_sec крестиком
        return ("loading_message",
                no_update,  # [],
                "Экспорт котировок",
                no_update,
                no_update,
                [],
                None)

    print(f'ВЫХОД 4 - Ввод символа в поле выбора Инструмента')  # "По набору символа в dd_sec
    group_list = [item for group in selected_groups for item in MARKETS[group]]
    filtered_df = get_start_df(re.escape(search_value), group_list)
    return ("loading_message",
            options_list(filtered_df),
            "Экспорт котировок",
            no_update,
            no_update,
            no_update,
            no_update)


@app.callback(
    [Output('input_contract_name', 'value', allow_duplicate=True),
     Output('input_file_name', 'value', allow_duplicate=True)],
    Input('memory', 'data'),
    State("date_range", "value"),
    prevent_initial_call=True,
    # allow_duplicate=False

)
# def update_inputs(memory_data, start_date, end_date):  # date_value
def update_inputs(memory_data, date):
    """При добавлении в Memory данных о выбранном инструменте, обновляем input_contract_name И input_file_name"""
    # print(f'{memory_data = }')
    if memory_data:
        return memory_data['secid'], f'{memory_data["secid"]}_{dates_transform(date)}'
    else:
        return no_update, no_update


@app.callback(
    Output("input_file_name", "value"),
    Input('date_range', 'value'),
    State("dropdown_sec", "value"),
    prevent_initial_call=True,
)
# def change_file_name_date(start_date, end_date, old_value):
def change_file_name_date(date, dd_sec_value):
    """Меняем Имя Файла при изменении Интервала дат"""
    if date is None or dd_sec_value is None:
        raise PreventUpdate
    return dd_sec_value + '_' + dates_transform(date)


@app.callback(
    Output("get_button", "disabled"),
    [Input("store_intervals_exist", "data"),
     Input("input_file_name", "value"),
     Input("input_contract_name", "value"),
     Input('dd_durations', 'value'),
     Input('date_range', 'value')],
    prevent_initial_call=True,

)
def change_button_status(v1, v2, v3, v4, v5):
    """Проверяем и устанавливаем доступность кнопки 'Загрузить файл'"""
    intervals_existence = not v1['intervals_exist'] if v1 else False
    if intervals_existence or any(value is None or value == '' for value in [v2, v3, v4, v5]):
        return True
    else:
        return False


@app.callback(
    [Output("loading_message", "id", allow_duplicate=True),
     Output("download_df", "data"),
     Output("no_interval_store", "data", allow_duplicate=True)],
    Input('get_button', 'n_clicks'),
    [
        State('date_range', 'value'),
        State('dd_durations', 'value'),
        State("input_file_name", "value"),
        State("dd_file_type", "value"),
        State("input_contract_name", "value"),
        State("dd_date_format", "value"),
        State("dd_time_format", "value"),
        State("dd_field_separator", "value"),
        State("dd_digit_separator", "value"),
        State("dd_record_format", "value"),
        State("rb_candle", "value"),
        State("file_header_cl", "value"),
        State('memory', 'data')
    ],
    prevent_initial_call=True,
    # allow_duplicate=False
)
def push_the_button(n_clicks, date, tf, file_name, file_type, contact_name, date_format,
                    time_format, field_separator, digit_separator, record_format, rb_candle, file_header_cl,
                    memory_data) -> tuple:
    """При нажатии "Загрузить файл", обращаемся к MOEX за историей (get_candles_history), обрабатываем ее
    (внутри get_candles_history) и загружаем файл"""
    # args = locals()
    # print(f"Загрузить файл!: {', '.join([f'{arg_name} = {arg_value}' for arg_name, arg_value in args.items()])}")
    sec, _, _, board, market, engine = memory_data.values()
    user_sets = dict(
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
    print("Вызываю get_candles_history ...")
    df_for_load = asyncio.run(get_candles_history(sec, board, market, engine, date[0], date[1], user_sets, tf))
    if df_for_load is None:
        return "loading_message", None, 1  # 5 секунд будем показывать, что нет Данных

    file = f"{file_name}.{file_type}"
    header = True if file_header_cl == ['Yes'] else False
    return ("loading_message",
            dcc.send_data_frame(df_for_load.to_csv, filename=file, sep=field_separator, header=header, index=False),
            -1)


@app.callback(
    Output("auto-toast", "is_open"),
    Input("no_interval_store", "data"),
    prevent_initial_call=True,
)
def update_no_data(data):
    """На 5 секунд показываем надпись, что данных нет (toaster)."""
    if data == 1:
        return True


@app.callback(
    Output("date_range", "value"),
    Input('data_range_interval_timer', 'n_intervals'),
)
def update_date_range(n_intervals):
    """1 раз в час обновляем значение по умолчанию для date_range, не работает на хостинге"""
    new_range = [datetime.now().date() - timedelta(days=30), datetime.now().date()]
    # print(f'Тик-так таймер: {n_intervals} - {new_range}')
    return new_range


@app.callback(
    [Output("int_collapse", "is_open"),
     Output("int_button", "children")],
    [Input("int_button", "n_clicks")],
    [State("int_collapse", "is_open")],
    prevent_initial_call=True,
)
def toggle_collapse(n, is_open):
    """Смена названия кнопки для показа доступных Интервалов выбранного инструмента (collapse)
    при ее нажатии, и открытие списка collapse"""
    if n:
        return (not is_open,
                [chevron_down_icon, " Показать доступные интервалы исторических данных"] if is_open else
                [chevron_up_icon, " Скрыть доступные интервалы исторических данных"]
                )
    return is_open, [chevron_down_icon, " Показать доступные интервалы исторических данных"]


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    """Скрываем навигацию на маленьких экранах"""
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("notes_canvas", "is_open"),
    Input("notes", "n_clicks"),
    [State("notes_canvas", "is_open")],
)
def toggle_notes(n1, is_open):
    """Нажали Заметки на полях"""
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("about_canvas", "is_open"),
    Input("about", "n_clicks"),
    [State("about_canvas", "is_open")],
)
def toggle_about(n1, is_open):
    """Нажали О Ресурсе"""
    if n1:
        return not is_open
    return is_open


if __name__ == '__main__':
    if OS_TYPE == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # app.run_server(debug=True, host='127.0.4.177', port='51717')
    app.run_server(debug=True, host='127.0.0.1', port='8050')
