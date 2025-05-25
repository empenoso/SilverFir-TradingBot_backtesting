from dash import html


def get_footer():
    footer = html.Div(
        [
            html.Div(
                "Москва - Целеево. 2023.",
                style={'flex': '1', 'text-align': 'left'}
            ),
            html.Div(
                [
                    html.A(
                        html.Img(src="/assets/envelope-regular.svg", style={'height': '30px', 'margin-right': '10px'}),
                        href="mailto:admin@backtrader.ru",
                        target="_blank"
                    ),
                    html.A(
                        html.Img(src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png", style={'height':'30px', 'margin-right': '10px'}),
                        href="https://github.com/Celeevo/ISS-MOEX-client",
                        target="_blank"
                    ),
                    html.A(
                        "Celeevo/ISS-MOEX-client",
                        href="https://github.com/Celeevo/ISS-MOEX-client",
                        target="_blank",
                        style={'text-decoration': 'none', 'color': 'black', 'vertical-align': 'middle'}
                    )
                ],
                style={'flex': '1', 'text-align': 'right'}
            ),
        ],
        className="footer",
        style={
            'display': 'flex',
            'justify-content': 'space-between',
            'align-items': 'center',
            'padding': '10px',
            'background-color': '#f8f9fa',
        }
    )
    return footer


