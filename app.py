import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.graph_objs as go

from pyjstat import pyjstat
import pandas as pd
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],)

url = "http://api.worldbank.org/v2/country/all?format=json&per_page=600"
req = requests.get(url)
countries_df = pd.DataFrame.from_dict(
    pd.json_normalize(req.json()[1], record_prefix="_")
)
countries_df.columns = [c.replace(".", "_") for c in countries_df.columns]
countries_options = [
    {"label": row.name, "value": row.id} for row in countries_df.itertuples()
]
country_dict = dict(zip(countries_df.id, countries_df.name))

url = "http://api.worldbank.org/v2/topics/all?format=json&per_page=18000"
req = requests.get(url)
topics_df = pd.DataFrame.from_dict(
    pd.json_normalize(req.json()[1], record_prefix="_")
)
topics_df.columns = [c.replace(".", "_") for c in topics_df.columns]
topics_options = [
    {"label": row.value, "value": row.id} for row in topics_df.itertuples()
]

url = "http://api.worldbank.org/v2/indicator/all?format=json&per_page=18000&source_id=2"
req = requests.get(url)
indicator_df = pd.DataFrame.from_dict(
    pd.json_normalize(req.json()[1], record_prefix="_")
)
indicator_df.columns = [c.replace(".", "_") for c in indicator_df.columns]
indicator_df = indicator_df.query("source_id == '2'")
indicator_options = [
    {"label": row.name, "value": row.id} for row in indicator_df.itertuples()
]

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Countries & Regions"),
                dcc.Dropdown(
                    id="country_selection",
                    options=countries_options,
                    multi=True,
                    value=["SWE", "CHN", "USA"],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Topic"),
                dcc.Dropdown(
                    id="topic_selection",
                    options=topics_options,
                    multi=True,
                    value=["3"],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Indicator"),
                dcc.Dropdown(
                    id="indicator_selection",
                    options=indicator_options,
                    multi=False,
                    value="NY.GDP.MKTP.KD.ZG",
                ),
            ]
        ),
    ],
    body=True,
)
app.layout = dbc.Container(
    [
        html.H1("World Bank Data Dashboard", style={"textAlign": "center"}),
        html.H3(
            "Data source: https://www.worldbank.org/",
            style={"textAlign": "center"},
        ),
        html.Hr(),
        dbc.Row(
            [dbc.Col(controls, md=4), dbc.Col(dcc.Graph(id="chart"), md=8),],
            align="center",
        ),
    ],
    fluid=True,
)

# Callback to update chart
@app.callback(
    dash.dependencies.Output("chart", "figure"),
    [
        dash.dependencies.Input("country_selection", "value"),
        dash.dependencies.Input("topic_selection", "value"),
        dash.dependencies.Input("indicator_selection", "value"),
    ],
)
def update_graph(country_selection, topic_selection, indicator_selection):
    country_str = ";".join(c.lower() for c in country_selection)
    url = f"http://api.worldbank.org/v2/country/{country_str}/indicator/{indicator_selection}?format=jsonstat"
    dataset = pyjstat.Dataset.read(url)
    print(url)
    df = dataset.write("dataframe")
    plots = []
    for c in df.Country.unique():
        c_df = df.query(f"Country == '{c}'")
        cplot = go.Scatter(x=c_df.Year, y=c_df.value, name=c)
        plots.append(cplot)
    layout = go.Layout(
        # title="Average strokes gained per shot in category",
        xaxis=dict(
            title="year",
            titlefont=dict(
                family="Courier New, monospace", size=18, color="#7f7f7f"
            ),
        ),
        yaxis=dict(
            title=c_df.Series.unique()[0],
            titlefont=dict(
                family="Courier New, monospace", size=18, color="#7f7f7f"
            ),
        ),
        autosize=True,
    )
    return {"data": plots, "layout": layout}


@app.callback(
    dash.dependencies.Output("indicator_selection", "options"),
    [dash.dependencies.Input("topic_selection", "value"),],
)
def update_indicator_options(topic_selection):
    def check_topics(topics):
        return any(topic["id"] in topic_selection for topic in topics)

    filtered_indicators = indicator_df[
        indicator_df["topics"].apply(check_topics)
    ]
    indicator_options = [
        {"label": row.name, "value": row.id}
        for row in filtered_indicators.itertuples()
    ]

    return indicator_options


if __name__ == "__main__":
    app.run_server(debug=True)

