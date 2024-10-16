import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, dash_table, ctx, MATCH
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# project files
import functions


def load_portfolio_logs() -> tuple:
    """Loads portfolio logs into dataframes"""

    # portfolio development
    data_file = functions.get_absolute_path("Results/Portfolio/portfolio_states.csv")
    portfolio_log = pd.read_csv(data_file, sep=",")
    portfolio_log["date"].apply(lambda x: x.split(" ")[0])
    portfolio_log["portfolio_index"] = portfolio_log["total_value"] / portfolio_log["total_value"].to_list()[0]
    portfolio_log["cummulative_returns"] = (portfolio_log["return"]-1).cumsum()
    portfolio_log["moving_average"] = portfolio_log["portfolio_index"].rolling(window=50,min_periods=1).mean()
    portfolio_log["volatility"] = portfolio_log["portfolio_index"].rolling(window=50,min_periods=1).std().fillna(0)

    # Index for comparison
    data_file = functions.get_absolute_path(f"Results/Index/{data_provider}_index.csv")
    exchange_index = pd.read_csv(data_file, sep=",",names=["date","index"])

    # Create common dataframe
    portfolio_log["date"] = exchange_index["date"]
    portfolio_log["exchange_index"] = exchange_index["index"]

    #Returns are logged on a trade basis, and so the df has different length
    data_file = functions.get_absolute_path("Results/Portfolio/returns.csv")
    trade_returns = pd.read_csv(data_file, sep=",", names=["returns"])


    # Table with backtest results
    data_file = functions.get_absolute_path("Results/Portfolio/backtest_results_df.csv")
    bt_results = pd.read_csv(data_file, sep=",")

    return portfolio_log, trade_returns,bt_results
def load_strategy_logs() -> dict:
    """Loads strategy logs into dataframes"""

    strat_dict = {}
    for strategy in strategies:

        # strategy development
        data_file = functions.get_absolute_path(f"Results/Strategies/{strategy}_states.csv")
        portfolio_log = pd.read_csv(data_file, sep=",")
        portfolio_log["date"].apply(lambda x: x.split(" ")[0])
        portfolio_log["strategy_index"] = portfolio_log["total_value"] / portfolio_log["total_value"].to_list()[0]
        portfolio_log["cummulative_returns"] = (portfolio_log["return"]-1).cumsum()

        # Index for comparison
        data_file = functions.get_absolute_path(f"Results/Index/{data_provider}_index.csv")
        exchange_index = pd.read_csv(data_file, sep=",",names=["date","index"])

        # Create common dataframe
        portfolio_log["date"] = exchange_index["date"]
        portfolio_log["exchange_index"] = exchange_index["index"]

        # Returns are logged on a trade basis, and so the df has different length
        data_file = functions.get_absolute_path(f"Results/Strategies/{strategy}_returns.csv")
        trade_returns = pd.read_csv(data_file, sep=",", names=["returns"])

        # Holdings log
        data_file = functions.get_absolute_path(f"Results/Strategies/{strategy}_holdings_log.csv")
        holdings_log = pd.read_csv(data_file, sep=",", names=["Entry Date", "Exit Date", "Ticker"])

        # Table with backtest results
        data_file = functions.get_absolute_path(f"Results/Strategies/{strategy}_backtest_results_df.csv")
        bt_results = pd.read_csv(data_file, sep=",")

        strat_dict[strategy] = (portfolio_log,trade_returns, bt_results, holdings_log)

    return strat_dict
def create_portfolio_figs(states: pd.DataFrame, trade_returns: pd.DataFrame, p_colors: dict) -> dict:
    """Creates portfolio figures for dashboard"""

    #################################################### Create main plot. Portfolio index vs s&p 500 ####################################################
    portfolio_vs_index_fig = go.Figure()

    portfolio_vs_index_fig.add_trace(
        go.Scatter(
            x=states["date"],
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
                "<extra></extra>"
        )
    )
    portfolio_vs_index_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["exchange_index"],
            name="S&P 500",
            line=dict(color="purple"),
            hoverinfo='skip'
        )
    )

    # Moving average
    portfolio_vs_index_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["moving_average"],
            name="Moving average",
            line=dict(color="grey"),
            hoverinfo='skip'
        )
    )

    # Min and Max during backtest
    max_val = states["portfolio_index"].max()
    max_val_index = states["portfolio_index"].to_list().index(max_val)
    max_val_x = states.iloc[max_val_index]["date"]

    min_val = states["portfolio_index"].min()
    min_val_index = states["portfolio_index"].to_list().index(min_val)
    min_val_x = states.iloc[min_val_index]["date"]

    portfolio_vs_index_fig.add_trace(
        go.Scatter(
            y=[max_val],
            x=[max_val_x],
            mode="markers",
            marker_symbol="triangle-down",
            marker_color="green",
            marker_size=13,
            name="Peak"
        )
    )

    portfolio_vs_index_fig.add_trace(
        go.Scatter(
            y=[min_val],
            x=[min_val_x],
            mode="markers",
            marker_symbol="triangle-up",
            marker_color="red",
            marker_size=13,
            name="Max drawdown"
        )
    )

    portfolio_vs_index_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
        legend_y=0.8
    )



    #################################################### Risk vs cumulative returns ####################################################

    # risk and cummulative returns
    risk_cum_return_fig = make_subplots(specs=[[{"secondary_y": True}]])

    risk_cum_return_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["cummulative_returns"],
            name="Cummulative returns"
        )
    )

    risk_cum_return_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["risk_tolerance"]*states["win_rate"],
            name="Effective risk",opacity = 0.75),
        secondary_y=True
    )

    risk_cum_return_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
        legend_y=0.8
    )


    #################################################### Funds and asset value ####################################################
    funds_and_asset_value_fig = go.Figure()
    funds_and_asset_value_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["funds"],
            name="Funds"
        )
    )

    funds_and_asset_value_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["asset_value"],
            name="Asset value"
        )
    )

    funds_and_asset_value_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
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
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
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
    hist_figure.update_layout(
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"]
    )


    #################################################### win rate and equity risk ####################################################
    wr_risk_funds_fig = go.Figure()#make_subplots(specs=[[{"secondary_y": True}]])
    wr_risk_funds_fig.add_trace(
        go.Scatter(
            x=states["date"],
            y=states["win_rate"],
            name="Win rate", opacity = 0.75
        )
    )

    wr_risk_funds_fig.add_trace(go.Scatter(x=states["date"],
                             y=states["risk_tolerance"],
                             name="Equity risk", opacity = 0.75))
    wr_risk_funds_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
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
        indices_comparison_fig.add_trace(
            go.Scatter(
                x=exchange_index["date"],
                y=exchange_index["index"],
                name=label
            )
        )

    indices_comparison_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor=p_colors["graph_bg"],
        paper_bgcolor=p_colors["paper_bg"],
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
def create_strategy_figs(logs: dict,p_colors: dict) -> dict:
    """Creates strategy figures for dashboard"""

    return_dict = {}
    for name ,strat_log in logs.items():
        states = strat_log[0]
        trade_returns = strat_log[1]
        # Table with backtest results
        data_file = functions.get_absolute_path(f"Results/Strategies/{name}_backtest_results_df.csv")
        bt_results = pd.read_csv(data_file, sep=",")

        #################################################### Portfolio index vs s&p 500 ####################################################
        strategy_vs_index_fig = go.Figure()

        strategy_vs_index_fig.add_trace(
            go.Scatter(
                x=states["date"],
                 y=states["strategy_index"],
                 name="Strategy index",
                 line=dict(color="blue"),
                 customdata=states[["strategy_index","total_value","asset_value", "funds","date"]],
                 hovertemplate=
                "portfolio index: <b>%{customdata[0]}</b><br>" +
                "total equity: <b>%{customdata[1]:$,.0f}</b><br>" +
                "asset value: <b>%{customdata[2]:$,.0f}</b><br>" +
                "funds: <b>%{customdata[3]:$,.0f}</b><br>" +
                "trades: <b>%{customdata[4]}</b><br>" +
                "<extra></extra>"
            )
        )
        strategy_vs_index_fig.add_trace(
            go.Scatter(
                x=states["date"],
                y=states["exchange_index"],
                name="S&P 500",
                line=dict(color="purple"),
                hoverinfo='skip'
            )
        )

        # Min and Max during backtest
        max_val = states["strategy_index"].max()
        max_val_index = states["strategy_index"].to_list().index(max_val)
        max_val_x = states.iloc[max_val_index]["date"]

        min_val = states["strategy_index"].min()
        min_val_index = states["strategy_index"].to_list().index(min_val)
        min_val_x = states.iloc[min_val_index]["date"]

        strategy_vs_index_fig.add_trace(
            go.Scatter(
                y=[max_val],
                x=[max_val_x],
                mode="markers",
                marker_symbol="triangle-down",
                marker_color="green",
                marker_size=13,
                name="Peak"
            )
        )

        strategy_vs_index_fig.add_trace(
            go.Scatter(
                y=[min_val],
                x=[min_val_x],
                mode="markers",
                marker_symbol="triangle-up",
                marker_color="red",
                marker_size=13,
                name="Max drawdown"
            )
        )

        strategy_vs_index_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=p_colors["graph_bg"],
            paper_bgcolor=p_colors["paper_bg"],
            legend_y=0.8
        )

        #################################################### Funds and asset value ####################################################
        funds_and_asset_value_fig = go.Figure()
        funds_and_asset_value_fig.add_trace(
            go.Scatter(
                x=states["date"],
                y=states["funds"],
                name="Funds"
            )
        )
        funds_and_asset_value_fig.add_trace(
            go.Scatter(
                x=states["date"],
                y=states["asset_value"],
                name="Asset value"
            )
        )
        funds_and_asset_value_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=p_colors["graph_bg"],
            paper_bgcolor=p_colors["paper_bg"],
            legend_y=0.8
        )

        #################################################### Number of positions ####################################################
        positions_fig = go.Figure()
        positions_fig.add_trace(
            go.Scatter(
                x=states["date"],
                y=states["positions"],
                name="Positions"
            )
        )
        positions_fig.add_trace(
            go.Scatter(
                x=states["date"],
                y=states["trades"].diff(1),
                name="Trades"
            )
        )
        positions_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=p_colors["graph_bg"],
            paper_bgcolor=p_colors["paper_bg"],
            legend_y=0.8
        )

        #################################################### Histogram of returns ####################################################
        hist_figure = px.histogram(trade_returns, x="returns", nbins=round(trade_returns.shape[0] / 1.5))
        hist_figure.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            legend_y=0.8
        )
        hist_figure.update_layout({'xaxis': {'title': ''},'yaxis': {'title': ''}})
        hist_figure.update_layout(
            plot_bgcolor=p_colors["graph_bg"],
            paper_bgcolor=p_colors["paper_bg"]
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
            indices_comparison_fig.add_trace(
                go.Scatter(
                    x=exchange_index["date"],
                    y=exchange_index["index"],
                    name=label
                )
            )

        indices_comparison_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=p_colors["graph_bg"],
            paper_bgcolor=p_colors["paper_bg"],
            legend_y=0.8
        )


        return_dict[name] = {
            "portfolio_vs_index_fig": strategy_vs_index_fig,
            "hist_figure": hist_figure,
            "funds_and_asset_value_fig": funds_and_asset_value_fig,
            "positions_fig": positions_fig,
            "indices_fig": indices_comparison_fig,
            "backtest_df": bt_results
        }
    return return_dict
def create_ticker_data()-> tuple:
    """Returns the entire dataset from the chosen dataprovider"""

    path = functions.get_absolute_path(f"Resources/Data/BacktestData/{data_provider}_historical_data.csv")
    data = pd.read_csv(path,sep=",").groupby("Ticker")
    return data,list(data.groups.keys())



from parameters import backtest_parameters

data_provider = backtest_parameters["data_provider"]
strategies = backtest_parameters["strategies"]
start_date = backtest_parameters["start_date"]



# Colors
app_color = {"page_bg": "#dedfe0"}
plot_color = {"graph_bg": "#c4d7f2","paper_bg":"#dedfe0","graph_line": "#C0BCBC"}

# Portfolio figures
portfolio_states, trade_log, backtest_results = load_portfolio_logs()
portfolio_figs = create_portfolio_figs(portfolio_states, trade_log, plot_color)

# Dataset from chosen data provider
ticker_data,tickers = create_ticker_data()

# Strategy figures
strategy_logs = load_strategy_logs()
strategy_figs = create_strategy_figs(strategy_logs, plot_color)

# Layout variables
stats_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Distribution of returns"),
            dcc.Graph(figure=portfolio_figs["hist_figure"])
        ],style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"})

    ])
risk_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Cumulative returns and effective risk"),
            dcc.Graph(figure=portfolio_figs["risk_cum_return_fig"]),
        ],style={"margin-left":"10%","padding-top":"5%","margin-right":"2%"}),
    html.Div(
        [
            html.H4("Decomposed risk"),
            dcc.Graph(figure=portfolio_figs["wr_risk_funds_fig"]),
        ], style={"margin-top": "5%","margin-left":"10%","margin-right":"5%"})

])
explore_layout = html.Div(children=[

    html.Div(
        [
            html.H4("Indicies from different providers"),
            dcc.Graph(figure=portfolio_figs["indices_fig"]),
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
            [html.H2(f"Portolio performance overview"), html.Hr()]
        , style={"margin-left": "10%", "margin-right": "10%", "padding-top": "5%"}),
        html.Div([
            dash_table.DataTable(backtest_results.to_dict('records'),[{"name": i, "id": i} for i in backtest_results.columns],
                                 style_data={
                                     'color': 'black',
                                     'backgroundColor': 'white'
                                 },
                                 style_data_conditional=[
                                     {
                                         'if': {'row_index': 'odd'},
                                         'backgroundColor': 'rgb(220, 220, 220)',
                                     }
                                 ],
                                 style_header={
                                     'backgroundColor': 'rgb(210, 210, 210)',
                                     'color': 'black',
                                     'fontWeight': 'bold'
                                 },
                                 style_cell={
                                     'width': '{}%'.format(len(backtest_results.columns)),
                                     'textOverflow': 'ellipsis',
                                     'overflow': 'hidden',
                                     'text-align': 'center'
                                 }
                                 )
        ],style={"margin-left":"30%","margin-right":"30%","padding-top":"5%"}),
        html.Div(
        [
                    html.H4("Portfolio index vs S&P 500"),
                    dcc.Graph(figure=portfolio_figs["portfolio_vs_index_fig"]),
                 ], style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"}),
            html.Div(
                [
                    html.H4("Funds and asset value"),
                    dcc.Graph(figure=portfolio_figs["funds_and_asset_value_fig"]),
                ], style={"margin-top": "5%","margin-left":"10%","margin-right":"10%"}),
            html.Div(
                [
                    html.H4("Number of open positions and completed trades"),
                    dcc.Graph(figure=portfolio_figs["positions_fig"]),
                ], style={"margin-top": "5%","margin-left":"10%","margin-right":"10%"}),
    ])
strategies_layout = html.Div(children=[
        html.Div(children=[
            html.Div(
                [html.H2(f"{name}"),html.Hr()]
            ,style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"}),
            html.Div(
                dash_table.DataTable(strategy_figs[name]["backtest_df"].to_dict('records'),
                                     [{"name": i, "id": i} for i in strategy_figs[name]["backtest_df"].columns],
                                     style_data={
                                         'color': 'black',
                                         'backgroundColor': 'white'
                                     },
                                     style_data_conditional=[
                                         {
                                             'if': {'row_index': 'odd'},
                                             'backgroundColor': 'rgb(220, 220, 220)',
                                         }
                                     ],
                                     style_header={
                                         'backgroundColor': 'rgb(210, 210, 210)',
                                         'color': 'black',
                                         'fontWeight': 'bold'
                                     },
                                     style_cell={
                                         'width': '{}%'.format(len(strategy_figs[name]["backtest_df"].columns)),
                                         'textOverflow': 'ellipsis',
                                         'overflow': 'hidden',
                                         'text-align': 'center'
                                     }),style={"margin-left":"30%","margin-right":"30%","padding-top":"5%"}),

            html.Div([
                html.H4("Strategy vs S&P 500 index"),
                dcc.Graph(figure=strategy_figs[name]["portfolio_vs_index_fig"]),
             ], style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"})
        ,
        html.Div([
            html.H4("Explore holding periods."),
            html.Div([
                dcc.Dropdown(value="Choose a stock.",
                             options=pd.unique(strategy_logs[name][3]["Ticker"]),
                             searchable=True,
                             placeholder="Select ticker",
                             multi=False,
                             id={"type": "dynamic-holdings-dropdown", "index": i, "name": f"{name}"}
                )
            ], style={"width": "25%", "margin_bottom": "20%"})
        ], style={"margin-left": "10%", "padding-top": "5%"}),
        html.Div(children=[
            html.H4("Holding periods"),
            dcc.Graph(figure={}, id={"type": "dynamic-holdings-figs", "index": i, "name": f"{name}"})
        ], style={"margin-left":"10%","margin-right":"10%","padding-top":"5%"})

        ])

    for i, name in enumerate(strategies)])

# Navigation bar
navbar = html.Div(style={'margin':'0','padding': '0'},children=[
    dbc.NavbarSimple(children=[
        dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
        dbc.NavItem(dbc.NavLink("Strategies", href="/strategies")),
        dbc.NavItem(dbc.NavLink("Risk management", href="/risk_management")),
        dbc.NavItem(dbc.NavLink("Statistical analysis", href="/stats")),
        dbc.NavItem(dbc.NavLink("Explore", href="/explore"))
    ],brand="Backtest Dashboard",dark=True,color="dark")
])

# Initialize dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True)
app.title = 'Backtest results'
app.layout = html.Div(children = [
    dcc.Location(id="url", refresh=False), navbar,
    html.Div(id="page-content",style={'margin':'0','padding': '0','background-color': app_color["page_bg"]})
])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """Navigation bar callback"""

    if pathname == "/":
        return dashboard_layout
    elif pathname == "/strategies":
        return strategies_layout
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
    """Explorative figure callback"""

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

@app.callback(
    Output({'type': 'dynamic-holdings-figs', 'index': MATCH, "name": MATCH}, 'figure'),
    Input({'type': 'dynamic-holdings-dropdown', 'index': MATCH, "name": MATCH}, 'value')

)
def holding_period_fig(dd_value):
    if ctx.triggered_id is not None:
        id = ctx.triggered_id
        strat = id["name"]

        ticker_holdings = strategy_logs[strat][3][strategy_logs[strat][3]["Ticker"] == dd_value]
        x_start = ticker_holdings["Entry Date"]
        x_end = ticker_holdings["Exit Date"]

        fig = go.Figure()
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=plot_color["graph_bg"],
            paper_bgcolor=plot_color["paper_bg"],
            legend_y=0.8
        )

        df = ticker_data.get_group(dd_value)

        # Index of the first trade day of the backtest
        start_index = df["Date"].to_list().index(start_date)

        fig.add_trace(go.Scatter(x=df.iloc[start_index:]["Date"],y=df.iloc[start_index:]["Open"],name=dd_value))

        fig.add_trace(
            go.Scatter(
                x=x_start,
                y=df[df["Date"].isin(x_start)]["Open"].to_list(),
                mode='markers', marker=dict(size=8, color='green'), name="Bought"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_end,
                y=df[df["Date"].isin(x_end)]["Open"].to_list(),
                mode='markers', marker=dict( size=8, color='red'), name="Sold"
            ))
        return fig
    else:
        fig = go.Figure()

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor=plot_color["graph_bg"],
            paper_bgcolor=plot_color["paper_bg"],
            legend_y=0.8
        )
        return fig
if __name__ == '__main__':
    app.run_server(host="localhost", debug=True, use_reloader=False)
