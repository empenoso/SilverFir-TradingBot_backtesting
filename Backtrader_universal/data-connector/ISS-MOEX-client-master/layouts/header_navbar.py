from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

BT_LOGO = '/assets/bt_logo.png'


def right_nav():
    return dbc.Row([
            dbc.Col([
                dbc.NavLink("Заметки на полях", id="notes", href="notes", n_clicks=0, style={"color": "white"}),
                dbc.Offcanvas(
                    html.P([
                        html.A("О скорости загрузки с MOEX. ", style={'font-weight': 'bold'}),
                        """Загрузка данных с Биржи реализована с помощью библиотеки asyncio.
                        12-ти летняя история котировки ликвидной Акции (например, АФК Система, AFSK) на минутном 
                        тайм-фрейме в зависимости от загрузки серверов Биржи занимает от 2 до 3-х часов. 
                        Соответственно, загрузка 1-го года исторических данных для тайм-фрейма 1 минута - 
                        это 10-15 минут.
                        """
                    ]),
                    id="notes_canvas",
                    placement="bottom",
                    title="Заметки.",
                    is_open=False,
                ),
            ]),
            dbc.Col([
                dbc.NavLink("О ресурсе", id="about", href="about", n_clicks=0, style={"color": "white"}),
                dbc.Offcanvas([
                    html.P([
                        """Ресурс предназначен для демонстрации инструмента загрузки исторических котировок
                         с информационного сервиса """, html.A("Мосбиржи", href="https://iss.moex.com/", target="_blank"),
                        """, необходимых для анализа и проверки стратегий на платформе """,
                        html.A("backtrader", href="https://www.backtrader.com/", target="_blank"), """, 
                        или аналогичных. """
                        """Отдельное спасибо """, html.A("@WLM1ke", href="https://github.com/WLM1ke", target="_blank"),
                        """ за библиотеку """, html.A("Asyncio MOEX ISS API", href="https://github.com/WLM1ke/aiomoex", target="_blank"),
                        """, функции которой легли в основу запросов к Бирже."""]),

                    html.A("Ваши пожелания и рационализаторские предложения присылайте на адрес "),
                    html.A("admin@backtrader.ru", href="admin@backtrader.ru"), ".",
                    html.P(""),
                    html.A("Документация по библиотеке Backtrader на русском", href="https://backtrader.ru/", target="_blank"),
                    html.P(""),
                    html.A("2023-12-31", className="d-flex justify-content-end", style={"color": "black"}),
                    ],
                    id="about_canvas",
                    placement="end",
                    title="О ресурсе",
                    is_open=False
                    ),
                ],
                width="auto"
            )
             ],
                className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
                align="center",
    )


def navbar():
    return dbc.Navbar([
                dbc.Row([
                        dbc.Col([
                            html.A(
                                html.Img(src=BT_LOGO, height="40px", style={'marginRight': '20px'}), href="https://backtrader.ru/", target="_blank"
                            ),
                            ]),
                        dbc.Col(
                            dbc.NavbarBrand(
                                html.Div([html.Div("Источники Данных для Backtrader. Экспорт котировок с Биржи MOEX",
                                         style={
                                             "text-overflow": "ellipsis",
                                             "white-space": "nowrap"}),
                                        ]),
                            )
                            ),
                        ]),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    right_nav(),
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),
        ],
        color="DarkGrey",
        dark=True,
        className="navbar navbar-dark bg-dark sticky-top",
    )