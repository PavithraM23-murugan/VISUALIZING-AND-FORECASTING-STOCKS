import traceback
import dash
import requests
from dash import dcc
from dash import html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
# model
from model import prediction
api_key = 'Alpha key'
av = TimeSeries(key=api_key)

def get_stock_price_fig(df):

    fig = px.line(df,
                  x="Date",
                  y=["Close", "Open"],
                  title="Closing and Openning Price vs Date")

    return fig


def get_more(df):
    df['EWA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df,
                     x="Date",
                     y="EWA_20",
                     title="Exponential Moving Average vs Date")
    fig.update_traces(mode='lines+markers')
    return fig



app = dash.Dash(__name__)

# Specify the URL of your external CSS file as a list
external_css_urls = ["styles.css"]

# Link the external CSS file(s) to the app using the external_stylesheets parameter
app = dash.Dash(__name__, external_stylesheets=external_css_urls)

# To get descriptiom

def get_company_info(stock_code, api_key):
    base_url = 'https://www.alphavantage.co/query'
    function = 'OVERVIEW'
    params = {
        'function': function,
        'symbol': stock_code,
        'apikey': api_key
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if 'Symbol' in data:
            return data
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Replace 'YOUR_API_KEY' with your Alpha Vantage API key
api_key = 'E5G3MUB5E0WQT9JN'

server = app.server
# html layout of site

app.layout = html.Div(
    [
        html.Div(
            [    
                html.Div([
                    html.P("Input stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers",
                                   type="text",
                                   placeholder="Stock Symbol"),
                        
                        html.Button("Submit", id='submit'),
                    ],
                             className="form")
                ],
                
                         className="input-place"),
                html.Div([
                    dcc.DatePickerRange(id='my-date-picker-range',
                                        min_date_allowed=dt(1995, 8, 5),
                                        max_date_allowed=dt.now(),
                                        initial_visible_month=dt.now(),
                                        end_date=dt.now().date()),
                ],
                         className="date"),
                html.Div([
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators",
                                className="indicators-btn",
                                id="indicators"),
                    dcc.Input(id="n_days",
                              type="text",
                              placeholder="Number Of Days"),
                    html.Button(
                        "Forecast", className="forecast-btn", id="forecast")
                ],
                         className="buttons"),
                # here
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                    html.Div(id='company-info-output'),
                # html.Div(id="description", className="decription_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content")
            ],
            className="content"),
    ],
    className="container")

#description
@app.callback(
    Output("company-info-output", "children"),
Input("submit", "n_clicks"),
Input('dropdown_tickers', 'value'),
)


def update_company_info(n_clicks, stock_code):
    if n_clicks is None:
        return []

    company_info = get_company_info(stock_code, api_key)

    if company_info:
        return [
            html.Label("Company Name:"),
            dcc.Input(value=company_info['Name'], readOnly=True),
            
            html.Label("Description:"),
            dcc.Textarea(value=company_info['Description'], readOnly=True, style={'width': '100%'}),
        ]
    else:
        return [html.P("Company information not available for the given symbol.")]


#
@app.callback([
    Output("graphs-content", "children"),
], [
    Input("stock", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n == None:
        return [""]
        #raise PreventUpdate
    if val == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(val, str(start_date), str(end_date))
        else:
            df = yf.download(val)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]


# callback for indicators
@app.callback([Output("main-content", "children")], [
    Input("indicators", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])
def indicators(n, start_date, end_date, val):
    if n == None:
        return [""]
    if val == None:
        return [""]

    if start_date == None:
        df_more = yf.download(val)
    else:
        df_more = yf.download(val, str(start_date), str(end_date))

    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]


# callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n == None:
        return [""]
    if val == None:
        raise PreventUpdate
    fig = prediction(val, int(n_days) + 1)
    return [dcc.Graph(figure=fig)]


if __name__ == '__main__':
    app.run_server(debug=True)
