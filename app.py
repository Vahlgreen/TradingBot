import pandas as pd
import os
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from dash import Dash, dcc, html, dash_table, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from PIL import Image

# project files
import functions
from parameters import data_provider

def load_logs() -> tuple:

    # Read logs
    # portfolio development
    data_file = functions.get_absolute_path("Results/portfolio_states.csv")
    portfolio_log = pd.read_csv(data_file, sep=",")
    portfolio_log["date"].apply(lambda x: x.split(" ")[0])
    portfolio_log["portfolio_index"] = portfolio_log["total_value"] / portfolio_log["total_value"].to_list()[0]
    portfolio_log["cummulative_returns"] = (portfolio_log["return"]-1).cumsum()

    # rolling statistics
    portfolio_log["moving_average"] = portfolio_log["portfolio_index"].rolling(window=50,min_periods=1).mean()
    portfolio_log["volatility"] = portfolio_log["portfolio_index"].rolling(window=50,min_periods=1).std().fillna(0)

    # Index for comparison
    data_file = functions.get_absolute_path(f"Results/Index/{data_provider}_index.csv")
    exchange_index = pd.read_csv(data_file, sep=",",names=["date","index"])

    # Create common dataframe
    portfolio_log["date"] = exchange_index["date"]
    portfolio_log["exchange_index"] = exchange_index["index"]

    #Returns are logged on a trade basis, and so the df has different length
    data_file = functions.get_absolute_path("Results/returns.csv")
    trade_returns = pd.read_csv(data_file, sep=",", names=["returns"])

    return portfolio_log, trade_returns
def create_figures(states: pd.DataFrame, trade_returns: pd.DataFrame, plot_color: dict) -> dict:


    #################################################### Create main plot. Portfolio index vs s&p 500 ####################################################
    portfolio_vs_index_fig = go.Figure()

    portfolio_vs_index_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["portfolio_index"],
                             name="Portfolio index",
                             line=dict(color="blue"),
                             customdata=states[["portfolio_index","total_value","asset_value", "funds","trades","positions","date"]],
                             hovertemplate=
                            "portfolio index: <b>%{customdata[0]}</b><br>" +
                            "total equity: <b>%{customdata[1]:$,.0f}</b><br>" +
                            "asset value: <b>%{customdata[2]:$,.0f}</b><br>" +
                            "funds: <b>%{customdata[3]:$,.0f}</b><br>" +
                            "trades: <b>%{customdata[4]}</b><br>" +
                            "positions: <b>%{customdata[5]}</b><br>" +
                            "date: <b>%{customdata[6]}</b><br>" +
                            "<extra></extra>"))
    portfolio_vs_index_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["exchange_index"],
                             name="S&P 500",
                             line=dict(color="purple"),
                             hoverinfo='skip'))

    # moving average
    portfolio_vs_index_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["moving_average"],
                             name="Moving average",
                             line=dict(color="grey"),
                             hoverinfo='skip'))
    max_val = [states["portfolio_index"].max()]*len(states)
    min_val = [states["portfolio_index"].min()]*len(states)
    portfolio_vs_index_fig.add_trace(go.Scatter(y=max_val,x=states["date"], line_width=1.5, line_dash = "dash",line_color="green", name="peak"))
    portfolio_vs_index_fig.add_trace(go.Scatter(y=min_val,x=states["date"], line_width=1.5, line_dash="dash", line_color="red", name="Max drawdown"))
    portfolio_vs_index_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )

    # confidence interval
    # portfolio_vs_index_fig.add_traces([go.Scatter(x=states["date"],
    #                            y=states["movingAverage"] - states["volatility"],
    #                            showlegend = False,
    #                            line_color = 'rgba(0,0,0,0)',
    #                            hoverinfo='skip'),
    #                go.Scatter(x=states["date"],
    #                           y=states["movingAverage"] + states["volatility"],
    #                           name = 'Volatility',
    #                           line_color='rgba(0,0,0,0)',
    #                           fill='tonexty', fillcolor = 'rgba(255, 0, 0, 0.2)',
    #                           hoverinfo='skip')])



    #################################################### Risk vs cumulative returns ####################################################

    # risk and cummulative returns
    risk_cum_return_fig = make_subplots(specs=[[{"secondary_y": True}]])
    risk_cum_return_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["cummulative_returns"],
                             name="Cummulative returns"))
    risk_cum_return_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["risk"]*states["win_rate"],
                             name="Effective risk",opacity = 0.75),secondary_y=True)
    #risk_cum_return_fig.write_html(functions.get_absolute_path("Results/Plots/cum_returns_and_risk.html"))
    risk_cum_return_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )


    #################################################### Funds and asset value ####################################################
    funds_and_asset_value_fig = go.Figure()
    funds_and_asset_value_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["funds"],
                             name="Funds"))
    funds_and_asset_value_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["asset_value"],
                             name="Asset value"))
    funds_and_asset_value_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )

    #################################################### Number of positions ####################################################
    positions_fig = go.Figure()
    positions_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["positions"],
                             name="Positions"))
    positions_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["trades"].diff(1),
                             name="Trades"))
    positions_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )

    #################################################### Histogram of returns ####################################################
    hist_figure = px.histogram(trade_returns, x="returns", nbins=round(trade_returns.shape[0] / 1.5))
    #hist_figure.write_html(functions.get_absolute_path("Results/Plots/Returns.html"))
    hist_figure.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend_y=0.8
    )
    hist_figure.update_layout({'xaxis': {'title': ''},'yaxis': {'title': ''}})
    hist_figure.update_layout(plot_bgcolor=plot_color["graph_bg"], paper_bgcolor=plot_color["paper_bg"])


    #################################################### win rate and equity risk ####################################################
    wr_risk_funds_fig = go.Figure()#make_subplots(specs=[[{"secondary_y": True}]])
    wr_risk_funds_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["win_rate"],
                             name="Win rate", opacity = 0.75))
    wr_risk_funds_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["risk"],
                             name="Equity risk", opacity = 0.75))
    wr_risk_funds_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )
    #################################################### Compiled indicies fig ####################################################
    path = functions.get_absolute_path("Resources/Data/BacktestData/")
    dir_list = os.listdir(path)
    files_list = [name for name in dir_list if "index" in name.split("_")[1]]

    indices_comparison_fig = go.Figure()

    for file in files_list:
        label = f"{file.split('_')[0]}"
        exchange_index = pd.read_csv(path+file, sep=",")
        exchange_index["index"] = exchange_index["index"]/exchange_index["index"].iloc[0]
        indices_comparison_fig.add_trace(go.Scatter(x=exchange_index["date"],
                                 y=exchange_index["index"],
                                 name=label))

    indices_comparison_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )

    return_dict = {
        "portfolio_vs_index_fig": portfolio_vs_index_fig,
        "risk_cum_return_fig": risk_cum_return_fig,
        "hist_figure": hist_figure,
        "funds_and_asset_value_fig": funds_and_asset_value_fig,
        "positions_fig": positions_fig,
        "wr_risk_funds_fig": wr_risk_funds_fig,
        "indices_fig": indices_comparison_fig
    }

    return return_dict
def create_ticker_data():
    path = functions.get_absolute_path(f"Resources/Data/BacktestData/{data_provider}_historical_data.csv")
    data = pd.read_csv(path,sep=",").groupby("Ticker")
    return data,list(data.groups.keys())


app_color = {"page_bg": "#dedfe0"}
plot_color = {"graph_bg": "#c4d7f2","paper_bg":"#dedfe0","graph_line": "#C0BCBC"}

portfolio_states, trade_log = load_logs()
ticker_data,tickers = create_ticker_data()
figs = create_figures(portfolio_states, trade_log,plot_color)

port_index = figs["portfolio_vs_index_fig"]
risk_cum_return_fig = figs["risk_cum_return_fig"]
hist_fig = figs["hist_figure"]
funds_and_asset_value_fig = figs["funds_and_asset_value_fig"]
positions_fig = figs["positions_fig"]
wr_risk_funds_fig = figs["wr_risk_funds_fig"]
indices_fig = figs["indices_fig"]




stats_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Distribution of returns"),
            dcc.Graph(figure=hist_fig)
        ],style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"})

    ])
risk_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Cumulative returns and effective risk"),
            dcc.Graph(figure=risk_cum_return_fig),
        ],style={"margin-left":"10%","padding-top":"5%","margin-right":"2%"}),
    html.Div(
        [
            html.H4("Decomposed risk"),
            dcc.Graph(figure=wr_risk_funds_fig),
        ], style={"margin-top": "5%","margin-left":"10%","margin-right":"5%"})

])
explore_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Indicies from different providers"),
            dcc.Graph(figure=indices_fig),
        ], style={"margin-left":"10%", "margin-right": "10%","padding-top":"5%"}),

    html.Div([
        html.H4("Explore stock data. Select multiple tickers."),
        html.Div([
            dcc.Dropdown(
                tickers,
                searchable=True, placeholder="Select ticker", multi=True, id="ticker_dropdown"
                )
            ],style={"width": "25%","margin_bottom":"20%"})
        ],style={"margin-left":"10%","padding-top":"5%"}),

    html.Div([
        html.H4("Historical price data"),
        dcc.Graph(figure={}, id="historical_price_data")
    ], style={"margin-left":"10%", "margin-right": "10%"})


])
dashboard_layout = html.Div(children=[
        html.Div(
        [
                    html.H4("Portfolio index vs S&P 500"),
                    dcc.Graph(figure=port_index),
                 ], style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"}),
            html.Div(
                [
                    html.H4("Funds and asset value"),
                    dcc.Graph(figure=funds_and_asset_value_fig),
                ], style={"margin-top": "5%","margin-left":"10%","margin-right":"10%"}),
            html.Div(
                [
                    html.H4("Number of open positions and completed trades"),
                    dcc.Graph(figure=positions_fig),
                ], style={"margin-top": "5%","margin-left":"10%","margin-right":"10%"}),
    ])

navbar = html.Div(style={'margin':'0','padding': '0'},children=[
    dbc.NavbarSimple(children=[
        dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
        dbc.NavItem(dbc.NavLink("Risk management", href="/risk_management")),
        dbc.NavItem(dbc.NavLink("Statistical analysis", href="/stats")),
        dbc.NavItem(dbc.NavLink("Explore", href="/explore"))
    ],brand="Backtest Dashboard",dark=True,color="dark")
])

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True)
app.title = 'Backtest results'
app.layout = html.Div(children = [
    dcc.Location(id="url", refresh=False), navbar,
    html.Div(id="page-content",style={'margin':'0','padding': '0','background-color': app_color["page_bg"]})
])


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return dashboard_layout
    elif pathname == "/stats":
        return stats_layout
    elif pathname == "/risk_management":
        return risk_layout
    elif pathname == "/explore":
        return explore_layout
    else:
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognized..."),
            ]
        )

@app.callback(Output("historical_price_data", "figure"), Input("ticker_dropdown", "value"))
def update_ticker_graph(dd_value):
    fig = go.Figure()
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=plot_color["graph_bg"],
        paper_bgcolor=plot_color["paper_bg"],
        legend_y=0.8
    )
    if dd_value is not None:
        for ticker in dd_value:
            df = ticker_data.get_group(ticker)
            fig.add_trace(go.Scatter(x=df["Date"],y=df["Open"],name=ticker))

    return fig
if __name__ == '__main__':
    app.run_server(host="localhost", debug=True, use_reloader=False)