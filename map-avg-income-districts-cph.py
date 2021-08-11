#!/usr/bin/env python
# coding: utf-8

# Import modules
import json
import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Import geo data
districts_cph = json.load(open("data/geodata-districts-cph.json", "r", encoding='utf-8'))

# Create dictionary with district name and id
districts_id_map = {}
for feature in districts_cph["features"]:
    districts_id_map[feature["properties"]["navn"]] = feature["id"]

# Import income data
df_income = pd.read_csv('data/avg-income-districts-cph.csv', encoding = "ISO-8859-1", sep=';')

# Clean district rows
df_income['district'] = df_income['district'].str[11:]

# Change district name
df_income['district'].replace({"Vesterbro/Kongens Enghave": "Vesterbro-Kongens Enghave"}, inplace=True)

# Pivot data from wide to long format
df_income_long = (df_income.melt(id_vars = 'district',
                                 var_name = 'year',
                                 value_name = 'avg_income')) # https://towardsdatascience.com/reshape-pandas-dataframe-with-melt-in-python-tutorial-and-visualization-29ec1450bb02

# Convert the data type of the year column to numeric
df_income_long['year'] = df_income_long['year'].astype(int)

# Create 'id' column
df_income_long["id"] = df_income_long["district"].apply(lambda x: districts_id_map[x])

# Define values and text for the color bar
max_value_colorbar = round(df_income_long['avg_income'].max(), -4) + 10000
min_value_colorbar = round(df_income_long['avg_income'].min(), -4) - 10000

colorbar_values = list(range(min_value_colorbar, max_value_colorbar, 40000))

colorbar_text = list(map('{:,d}'.format, colorbar_values))

# Change the thousand separator to a dot
colorbar_text_dot = []

for string in colorbar_text:
    new_string = string.replace(",", ".")
    colorbar_text_dot.append(new_string)

# Create app

app = dash.Dash(__name__)

server = app.server

description = '''
The interactive map on this page shows data about the average income for persons above the age of 14 in each of the ten districts of Copenhagen.
Below you can choose which year data will be shown for. Data is from the City of Copenhagen Statbank.
'''

app.layout = html.Div(
    className="page",
    children=[
    html.Div(
        className="main-content",
        children=[

            html.H1("How the average income in the districts of Copenhagen has changed"),

            dcc.Markdown(description,
                className="text-description"),

            html.Label('Choose year:',
                      className="slider-label"),
            dcc.Slider(
                id='year-slider',
                min=df_income_long['year'].min(),
                max=df_income_long['year'].max(),
                value=df_income_long['year'].max(),
                marks={str(year): str(year) for year in df_income_long['year'].unique()},
                step=None,
                included=False,
                className="map-slider"
            ),

            dcc.Graph(
                id='map-copenhagen',
                config={
                'displayModeBar': False,
                'scrollZoom': False
            })
        ])
    ])

@app.callback(
    Output('map-copenhagen', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df_income_long[df_income_long.year == selected_year]

    fig = px.choropleth_mapbox(
    filtered_df,
    locations="id",
    geojson=districts_cph,
    color="avg_income",
    color_continuous_scale="YlGn",
    mapbox_style="carto-positron",
    center={"lat": 55.6760968, "lon": 12.5543311},
    zoom=10.9,
    height=800,
    labels={'avg_income':'Average income'},
    custom_data=["district", "year", "avg_income"],
    range_color=[min_value_colorbar, max_value_colorbar]
    )

    fig.update_layout(
    font=dict(family='Roboto', size=16),
    dragmode=False,
    paper_bgcolor="#fbfbfb",
    hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_family='Roboto'
    ),
    separators=",.",
    coloraxis_colorbar=dict(
        title='Average income',
        lenmode='fraction',
        len=0.5,
        tickvals=colorbar_values,
        ticktext=colorbar_text_dot
        ),
    margin=dict(l=0, r=0, t=0, b=0)
    )

    fig.update_traces(
    hovertemplate=("</br><b>%{customdata[0]}</b></br>" +
                "Year: %{customdata[1]}</br>" +
                "Avg. income: %{customdata[2]:,.d} dkr."))

    return fig


# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
