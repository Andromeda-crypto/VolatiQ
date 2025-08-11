import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import base64
import io
import requests

# App setup with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Default features
FEATURE_OPTIONS = [
    {'label': 'Log Return', 'value': 'log_return'},
    {'label': 'Rolling Volatility', 'value': 'volatility'},
    {'label': 'MA 5', 'value': 'ma_5'},
    {'label': 'MA 10', 'value': 'ma_10'},
    {'label': 'RSI', 'value': 'rsi'},
]

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1('VolatiQ: Market Volatility Forecast'), width=12)
    ], className='mb-2 mt-2'),
    dbc.Row([
        dbc.Col(html.P('Forecast short-term market volatility with advanced ML. Upload your data, select features, and visualize predictions.'), width=12)
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dbc.Label('Prediction Horizon (days)'),
            dcc.Dropdown(
                id='horizon-dropdown',
                options=[{'label': f'{d} days', 'value': d} for d in [1, 5, 10, 21]],
                value=5,
                clearable=False
            ),
        ], md=3),
        dbc.Col([
            dbc.Label('Select Features'),
            dcc.Dropdown(
                id='feature-dropdown',
                options=FEATURE_OPTIONS,
                value=[f['value'] for f in FEATURE_OPTIONS],
                multi=True
            ),
        ], md=5),
        dbc.Col([
            dbc.Label('Upload CSV Data'),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                style={
                    'width': '100%', 'height': '38px', 'lineHeight': '38px',
                    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                    'textAlign': 'center', 'margin-bottom': '10px'
                },
                multiple=False
            ),
        ], md=4),
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dbc.Button('Run Prediction', id='predict-btn', color='primary', className='me-2'),
            dcc.Loading(id='loading', type='circle', children=html.Div(id='loading-output'))
        ], width=2),
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            html.Div(id='output-table'),
            dcc.Graph(id='volatility-graph'),
        ], width=12)
    ]),
], fluid=True)

@app.callback(
    [Output('output-table', 'children'), Output('volatility-graph', 'figure'), Output('loading-output', 'children')],
    [Input('predict-btn', 'n_clicks')],
    [State('upload-data', 'contents'), State('horizon-dropdown', 'value'), State('feature-dropdown', 'value')]
)
def update_output(n_clicks, contents, horizon, features):
    if not n_clicks:
        return '', go.Figure(), ''
    if contents is None:
        return dbc.Alert('Please upload a CSV file.', color='warning'), go.Figure(), ''
    # Parse uploaded CSV
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return dbc.Alert(f'Error reading CSV: {e}', color='danger'), go.Figure(), ''
    # Check if selected features exist
    missing = [f for f in features if f not in df.columns]
    if missing:
        return dbc.Alert(f'Missing features in uploaded data: {missing}', color='danger'), go.Figure(), ''
    # Prepare data for API
    X = df[features].values.tolist()
    try:
        response = requests.post('http://localhost:5000/predict', json={'features': X})
        if response.status_code == 200:
            preds = response.json()['predictions']
            df['Predicted Volatility'] = preds
            table = dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
            )
            fig = go.Figure([
                go.Scatter(x=df.index, y=df['Predicted Volatility'], mode='lines+markers', name='Predicted Volatility')
            ])
            fig.update_layout(title='Predicted Volatility', xaxis_title='Index', yaxis_title='Volatility')
            return table, fig, ''
        else:
            return dbc.Alert(f'API Error: {response.text}', color='danger'), go.Figure(), ''
    except Exception as e:
        return dbc.Alert(f'Error contacting API: {e}', color='danger'), go.Figure(), ''

if __name__ == '__main__':
    app.run_server(debug=True)
