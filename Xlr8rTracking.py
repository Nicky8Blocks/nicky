import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from dash.dependencies import Input, Output
from pymongo import MongoClient
import numpy as numpy
import datetime

client = MongoClient("mongodb://apollo:apollo@ebchka02:27017")
db = client["shared_hist"]
collection = db['ApolloNewExpiryData']

# Get coin pairs full list from DB
ddb = client['thresholds']
collection2 = ddb['FuturesMonitor']
coin_list0 = pd.DataFrame((list(collection2.find())))
coin_list = ((coin_list0['Key']).unique())
extra_list = ['zzAll']
token_list = numpy.append(coin_list, extra_list)

# Get shared_history data from DB
def grab_log(symbols, value):
    df = pd.DataFrame(list(collection.find().sort('ValueUpdateTime', -1).limit(value)))
    column_names = ['Key',"AXlr8r",'Basis','Lean','ZBuyF','ZSellF','ZBuy','ZSell','ValueUpdateTime','Basis_LastUpdateTime','Lean_LastUpdateTime','_id']
    df = df.reindex(columns=column_names)
    pd.to_datetime(df["ValueUpdateTime"])
    df['ValueUpdateTime'] = df['ValueUpdateTime'] + pd.DateOffset(hours=8)
    df['ValueUpdateTime'] = df['ValueUpdateTime'].dt.round('1s')
    df = df.drop(axis=1,labels=["_id","Basis_LastUpdateTime","Lean_LastUpdateTime"])
    Raw_Key = df["Key"]
    df["Key"] = Raw_Key.str.strip("0")
    # Remove rows with all NaN values
    df = (df[(df.isnull().sum(axis=1))!=7])
    df = pd.DataFrame(df[df['Key'].isin(symbols)])
    return df


def create_dropdown(options):
    outputs = []
    options = list(options)
    options.sort()
    for option in options:
        outputs.append({'label': option, 'value': option})
    return outputs


app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1('Xlr8r Change Log', style={'fontSize':24 ,'text-align': 'center'}),
        dcc.Slider(
            id='get-how-many-mongo-data-slider',
            min=25,
            max=1000,
            step=25,
            value=50,
            marks={
                25: {'label':'25', 'style': {'color': '#7e7e9b'}},
                100: {'label':'100', 'style': {'color': '#7e7e9b'}},
                500: {'label':'500', 'style': {'color': '#7e7e9b'}},
                1000: {'label':'1000', 'style': {'color': '#7e7e9b'}},
    },
        ),
        html.Div(id='number-of-data-container', style={'text-align': 'right', 'color': 'grey', 'fontSize': 11},),

    dcc.Dropdown(
        id='Symbol',
        multi=True,
        value=token_list,
        options=create_dropdown(token_list),
        style={'fontSize': 12, 'margin-top':'0px', 'width': '100%', 'float': 'left'})
    ,
    html.Div(id='xlr8r-last-refresh-time-container',
             style={'text-align': 'right', 'color': 'grey', 'fontSize': 11}),
    dash_table.DataTable(
        id='table-filtering',
        data=grab_log(token_list, 50).to_dict('records'),
        columns=[{'id': col, 'name': col} for col in grab_log(token_list, 50).columns],
        filter_query=''
    ),
    dcc.Interval(
        id='interval-component',
        interval=120*1000,
        n_intervals=0
    )
])
])
@app.callback(
    Output('table-filtering', 'data'),
    Input('Symbol', 'value'),
    Input('get-how-many-mongo-data-slider', 'value'),
    Input('interval-component', 'n_intervals'))
def update_table(symbols, value, n):
    return grab_log(symbols, value).to_dict('records')

@app.callback(
    Output('xlr8r-last-refresh-time-container', 'children'),
    Input('interval-component','n_intervals')
)
def update_text(value):
    return ('Last auto-refresh time: ' + str(datetime.datetime.now().replace(microsecond=0)))

@app.callback(
    Output('number-of-data-container', 'children'),
    Input('get-how-many-mongo-data-slider', 'value')
)
def update_output(value):
    return 'showing last "{}" records'.format(value)

if __name__ == '__main__':
    app.run_server(debug=False)