from datetime import datetime, timedelta, date
from dash import Dash, dcc, html, Input, Output, callback, no_update
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from constants import TF, DATE_FORMAT, TIME_FORMAT, FIELD_SEPARATOR, DIGIT_SEPARATOR, RECORD_FORMAT, MOEX_WARNING

"""Иконки"""
download_icon = html.I(className="bi bi-cloud-download", style={"font-size": "1em", "color": "white"})
chevron_down_icon = html.I(className="bi bi-chevron-down", style={"font-size": "1em"})
chevron_up_icon = html.I(className="bi bi-chevron-up", style={"font-size": "1em"})

"""Стиль для Элементов формы"""
overflow_style = {"overflow": "hidden", "text-overflow": "ellipsis", "white-space": "nowrap"}

""""Видимые Элементы формы"""

"""Фильтр групп Инструментов"""
chip_market_groups = dmc.ChipGroup([
    dmc.Chip(x, value=x, variant="outline")
    for x in ["Акции", "Облигации", "Фьючерсы", "Опционы", "Индексы", "Прочее"]],
    id="market_filter", value=["Акции", "Облигации", "Фьючерсы"],
    multiple=True, style={"margin-top": "4px"})

"""Выбор Инструмента"""
dd_sec = dcc.Dropdown([], value=None, id='dropdown_sec', style={'height': '38px'})

"""Прозрачная кнопка для отображения доступных по выбранному инструменту Интервалов и ТФ"""
int_button = dbc.Button(
    [chevron_down_icon, " Показать доступные интервалы исторических данных"], color="link", id="int_button", n_clicks=0,
    style={
        "padding": "0",
        "font-size": "60%",
        "line-height": "12px",
        "margin-bottom": "0px",
        "box-shadow": "none"
    })

"""Псевдо-модальное окно для отображения отсутствия данных на moex по выбранному Инструменту на выбранном интервале"""
no_intervals_toaster = dbc.Toast(
    [html.P(html.B("Для выбранного Интервала Дат (или Тайм-фрейма) на Бирже нет данных."), className="mb-0")],
    id="auto-toast",
    header="Ошибка",
    icon="danger",
    dismissable=True,
    duration=5000,
    is_open=False,
    style={
        "position": "fixed",
        "top": "50%",  # Центрирование по вертикали
        "left": "50%",  # Центрирование по горизонтали
        "transform": "translate(-50%, -50%)",  # Сдвигаем элемент на 50% его ширины и высоты назад
        "width": 350,
    }
)
"""Выбор интервала для загрузки котировок"""
date_picker_range = dmc.DateRangePicker(
    id="date_range",
    value=[datetime.now().date() - timedelta(days=31), datetime.now().date()],
    # maxDate=datetime.now().date(),
    clearable=False,
    allowSingleDateInRange=True,
    amountOfMonths=2,
    inputFormat="DD MMMM YYYY",
    style={"width": 330, "white-space": "nowrap"},
)
"""Тайм-фрейм"""
dd_duration = dcc.Dropdown([], id='dd_durations', clearable=False)

"""Имя файла с котировками"""
file_name_input = dcc.Input(id="input_file_name", type="text", placeholder="Имя файла",
                               style={"width": "100%", "height": "35px"})

"""Имя Инструмента в выгрузке"""
contract_name_input = dcc.Input(id="input_contract_name", type="text", placeholder="Имя контракта",
                                   style={"width": "100%", "height": "35px"})

"""Тип файла выгрузки - txt или csv"""
dd_file_type = html.Div([
    dmc.SegmentedControl(
        id="dd_file_type", value="csv",
        data=[{"value": "csv", "label": "csv"}, {"value": "txt", "label": "txt"}, ],
        size="xs", style={"width": "60%", "height": "35px"}
    )])

"""Формат даты, времени, разделитель полей и цифр"""
dd_date_format = dcc.Dropdown(DATE_FORMAT, value='%d/%m/%y', id='dd_date_format', clearable=False)
dd_time_format = dcc.Dropdown(TIME_FORMAT, value='%H:%M', id='dd_time_format', clearable=False)
dd_field_sep = dcc.Dropdown(FIELD_SEPARATOR, value=',', id='dd_field_separator', clearable=False)
dd_digit_sep = dcc.Dropdown(DIGIT_SEPARATOR, value='нет', id='dd_digit_separator', clearable=False)

"""Выбор набора полей котировок для выгрузки"""
dd_record_format = dcc.Dropdown(RECORD_FORMAT, value="DATE, TIME, OPEN, HIGH, LOW, CLOSE, VOL",
                                   id='dd_record_format', clearable=False)

"""Выбор времени для баров"""
radio_candle_start = dcc.RadioItems([
    {'label': '  Начала свечи', 'value': 'begin'}, {'label': '  Окончания свечи', 'value': 'end'}],
    'begin', inline=True, id='rb_candle', labelStyle={'margin-right': '20px', 'margin-left': '10px'})

"""Заголовок в файл"""
check_header = dcc.Checklist([{'label': '  Добавить заголовок файла', 'value': "Yes"}],
                                ["Yes"], id='file_header_cl', labelStyle={'margin-left': '3px'})

"""Кнопка загрузки"""
button_get = dbc.Button([download_icon, " Загрузить файл"], id="get_button", className="mb-2", disabled=True)

data_range_timer = dcc.Interval(id='data_range_interval_timer',  # для обновления date_range
                                   interval=60 * 60 * 1000,  # в миллисекундах (1000 = 1 секунда)
                                   # interval=5*1000, # в миллисекундах (1000 = 1 секунда)
                                   n_intervals=0,  # начальное значение для n_intervals
                                   )

"""Предупреждение moex"""
moex_warning = dmc.Spoiler(
    showLabel="Показать больше",
    hideLabel="Скрыть",
    maxHeight=50,
    children=[html.A(MOEX_WARNING)],
)
"""Это нижняя часть окна, под выбором инструмента"""
export_card = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("Интервал:"),
                date_picker_range
            ])),
            dbc.Col(html.Div([
                html.Div("Тайм-фрейм:"),
                dd_duration
            ]))],
            style={"margin-top": "-16px"}
        ),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(["Имя файла:"], style=overflow_style),
                file_name_input,
            ]),
            ),
            dbc.Col(html.Div([
                html.Div(["Имя контракта:"], style=overflow_style),
                contract_name_input,
            ]),
            ),
            dbc.Col(html.Div([
                html.Div(["Тип файла:"], style=overflow_style),
                dd_file_type,
            ]),
            )
        ],
            style={"margin-top": "5px"}
        ),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(["Формат даты:"], style=overflow_style),
                dd_date_format,
            ])),
            dbc.Col(html.Div([
                html.Div(["Формат времени:"], style=overflow_style),
                dd_time_format,
            ]))
        ],
            style={"margin-top": "5px"}
        ),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(["Разделитель полей:"], style=overflow_style),
                dd_field_sep,
            ])),
            dbc.Col(html.Div([
                html.Div(["Разделитель разрядов:"], style=overflow_style),
                dd_digit_sep,
            ]))
        ],
            style={"margin-top": "5px"}
        ),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(["Формат записи в файл:"], style=overflow_style),
                dd_record_format,
            ])),
        ],
            style={"margin-top": "5px"}
        ),
        dbc.Row([
            dbc.Col(html.Div(["Выдавать время:"], style=overflow_style), width=3),
            dbc.Col(html.Div([radio_candle_start]), width=9),
        ],
            style={"margin-top": "5px"}
        ),
        dbc.Row(html.Div([check_header]), style={"margin-top": "5px"}),
        dbc.Row([
            dbc.Col([
                button_get,
                dcc.Download(id="download_df")],
                width="auto",
            ),
            dbc.Col([
                no_intervals_toaster,
                # Таймер для периодического обновления интервала дата (месяц назад от сегодня)
                # не работает на хостинге - линукс засыпает или что-то блочит видимо:
                data_range_timer,
                dcc.Store(id='no_interval_store')])
        ],
            style={
                "margin-top": "5px",
                "margin-bottom": "-10px"}
        ),
    ], id='export_card_body'),
    style={"margin-top": "7px"}
)

"""Полная карточка центральной колонки главной страницы"""
finish_export_card = dbc.Card([
    dbc.CardHeader([
        dbc.Row(html.Div(["Экспорт котировок"], id='export_card_header',
                         style={"font-weight": "bold", 'font-size': '150%'})),
        dcc.Store(id='store_intervals_exist')
    ]),
    dbc.CardBody([
        dcc.Store(id='memory', storage_type='local'),
        html.Div("Где ищем инструмент? Выбери Рынок:"),
        chip_market_groups,
        html.Div(id='loading_message', className='output-example-loading'),
        dd_sec,
        export_card,
        moex_warning
    ],
        style={"margin-top": "-16px"}
    )
])
