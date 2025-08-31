import dash
from dash import html, dcc, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import base64
import io
import requests
import os
import sys
from datetime import datetime
import logging

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Dash will automatically load any CSS in the 'assets' folder in the same directory as this file.
# Place custom styles in dashboard/assets/custom.css
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="VolatiQ Dashboard",
    update_title=None,
    suppress_callback_exceptions=True
)

# Logo placeholder (replace src with your logo if available)
logo = html.Img(src='https://upload.wikimedia.org/wikipedia/commons/6/6b/Bitmap_Icon_Logo.png', height='48px', style={'marginRight': '16px'})

# Default features
FEATURE_OPTIONS = [
    {'label': 'Log Return', 'value': 'log_return'},
    {'label': 'Rolling Volatility', 'value': 'volatility'},
    {'label': 'MA 5', 'value': 'ma_5'},
    {'label': 'MA 10', 'value': 'ma_10'},
    {'label': 'RSI', 'value': 'rsi'},
]

app.layout = html.Div([
    dcc.Store(id='theme-store', data='light-mode'),
    dcc.Store(id='table-data-store'),
    dcc.Store(id='last-pred-features'),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    logo,
                    html.H1('VolatiQ', style={'display': 'inline', 'fontWeight': 'bold', 'fontSize': '2.5rem', 'verticalAlign': 'middle'}),
                    dbc.Switch(
                        id='theme-toggle',
                        label='Dark Mode',
                        value=False,
                        style={'marginLeft': 'auto', 'marginRight': '0', 'marginTop': '8px', 'marginBottom': '8px', 'fontWeight': '600', 'fontSize': '1.1rem'}
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px', 'gap': '1.5rem'}),
                html.H5('Market Volatility Intelligence Platform', style={'color': '#6c757d', 'marginBottom': '0.5rem'}),
            ], width=12)
        ], className='mt-4 mb-2'),
        dbc.Row([
            dbc.Col(html.P('Forecast short-term market volatility with advanced ML. Upload your data, select features, and visualize predictions.', style={'fontSize': '1.1rem'}), width=12)
        ], className='mb-3'),
        html.Hr(style={'margin': '0.5rem 0 1.5rem 0', 'borderColor': '#e9ecef'}),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Prediction Horizon (days)', id='horizon-label', style={'fontWeight': '500'}),
                                dcc.Dropdown(
                                    id='horizon-dropdown',
                                    options=[{'label': f'{d} days', 'value': d} for d in [1, 5, 10, 21]],
                                    value=5,
                                    clearable=False,
                                    style={'marginBottom': '8px'}
                                ),
                                dbc.Tooltip('How many days ahead to forecast volatility.', target='horizon-label'),
                            ], md=3),
                            dbc.Col([
                                dbc.Label('Select Features', id='feature-label', style={'fontWeight': '500'}),
                                dcc.Dropdown(
                                    id='feature-dropdown',
                                    options=FEATURE_OPTIONS,
                                    value=[f['value'] for f in FEATURE_OPTIONS],
                                    multi=True,
                                    style={'marginBottom': '8px'}
                                ),
                                dbc.Tooltip('Choose which features to use for prediction.', target='feature-label'),
                            ], md=5),
                            dbc.Col([
                                dbc.Label('Upload CSV Data', id='upload-label', style={'fontWeight': '500'}),
                                dcc.Upload(
                                    id='upload-data',
                                    children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                                    style={
                                        'width': '100%', 'height': '38px', 'lineHeight': '38px',
                                        'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                                        'textAlign': 'center', 'margin-bottom': '10px', 'background': '#f1f3f6'
                                    },
                                    multiple=False
                                ),
                                dbc.Tooltip('Upload a CSV file with your market data.', target='upload-label'),
                            ], md=4),
                        ], className='mb-2'),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button('Run Prediction', id='predict-btn', color='primary', className='me-2', style={'fontWeight': '600', 'fontSize': '1.1rem', 'padding': '8px 24px'}),
                                dcc.Loading(id='loading', type='circle', children=html.Div(id='loading-output'))
                            ], width=12, className='d-flex justify-content-end')
                        ]),
                    ])
                ], style={'boxShadow': '0 2px 12px rgba(0,0,0,0.06)', 'borderRadius': '16px', 'background': '#fff', 'marginBottom': '2rem'})
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.Hr(style={'margin': '2rem 0 1rem 0', 'borderColor': '#e9ecef'}),
                html.Div(id='output-table', style={'marginBottom': '2rem'}),
                dcc.Graph(id='volatility-graph', config={'displayModeBar': False}, style={'borderRadius': '12px', 'boxShadow': '0 1px 8px rgba(0,0,0,0.04)', 'background': '#fff'}),
                html.Div(id='shap-explanation', style={'marginTop': '2rem'}),
            ], width=12)
        ]),
        html.Footer([
            html.Hr(style={'margin': '2rem 0 1rem 0', 'borderColor': '#e9ecef'}),
            html.Div('© 2024 VolatiQ. All rights reserved.', style={'color': '#adb5bd', 'fontSize': '0.95rem', 'textAlign': 'center', 'marginBottom': '1rem'})
        ])
    ], fluid=True)
], id='main-div', className='light-mode', style={'minHeight': '100vh', 'transition': 'background 0.5s, color 0.5s'})

@app.callback(
    Output('main-div', 'className'),
    Output('theme-store', 'data'),
    Input('theme-toggle', 'value'),
    State('theme-store', 'data')
)
def toggle_theme(is_dark, current):
    if is_dark:
        return 'dark-mode', 'dark-mode'
    return 'light-mode', 'light-mode'

@app.callback(
    [Output('output-table', 'children'), Output('volatility-graph', 'figure'), Output('loading-output', 'children'), Output('table-data-store', 'data'), Output('last-pred-features', 'data')],
    [Input('predict-btn', 'n_clicks')],
    [State('upload-data', 'contents'), State('horizon-dropdown', 'value'), State('feature-dropdown', 'value')]
)
def update_output(n_clicks, contents, horizon, features):
    if not n_clicks:
        return '', go.Figure(), '', None, None
    if contents is None:
        return dbc.Alert('Please upload a CSV file.', color='warning'), go.Figure(), '', None, None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return dbc.Alert(f'Error reading CSV: {e}', color='danger'), go.Figure(), '', None, None
    missing = [f for f in features if f not in df.columns]
    if missing:
        return dbc.Alert(f'Missing features in uploaded data: {missing}', color='danger'), go.Figure(), '', None, None
    X = df[features].values.tolist()
    try:
        logger.info(f"Making prediction request with {len(X)} samples")
        response = requests.post(f'{config.API_URL}/predict', json={'features': X}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            preds = result['predictions']
            df['Predicted Volatility'] = preds
            
            # Log prediction metrics
            processing_time = result.get('processing_time_seconds', 'N/A')
            logger.info(f"Prediction successful: {len(preds)} predictions in {processing_time}s")
            # Add Explain buttons
            explain_buttons = [
                dbc.Button('Explain', id={'type': 'explain-btn', 'index': i}, color='info', size='sm', style={'margin': '0 4px'})
                for i in range(len(df))
            ]
            table = dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns] + [{'name': 'Explain', 'id': 'Explain'}],
                page_size=10,
                style_table={'overflowX': 'auto', 'borderRadius': '12px', 'boxShadow': '0 1px 8px rgba(0,0,0,0.04)'},
                style_cell={'textAlign': 'left', 'fontFamily': 'Inter, Segoe UI, Arial, sans-serif', 'fontSize': '1.05rem', 'padding': '8px'},
                style_header={'backgroundColor': '#f1f3f6', 'fontWeight': 'bold'},
                row_deletable=False,
                editable=False,
                # Add Explain buttons to the table
                data_previous=df.head(10).to_dict('records'),
            )
            # Store table data and features for SHAP
            return (
                html.Div([
                    table,
                    html.Div([
                        dbc.Button('Explain', id={'type': 'explain-btn', 'index': i}, color='info', size='sm', style={'margin': '0 4px'})
                        for i in range(min(10, len(df)))
                    ], style={'marginTop': '8px'})
                ]),
                go.Figure([
                    go.Scatter(x=df.index, y=df['Predicted Volatility'], mode='lines+markers', name='Predicted Volatility', line=dict(color='#007bff'))
                ]).update_layout(
                    title='Predicted Volatility',
                    xaxis_title='Index',
                    yaxis_title='Volatility',
                    plot_bgcolor='#fff',
                    paper_bgcolor='#fff',
                    font=dict(family='Inter, Segoe UI, Arial, sans-serif', size=15),
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode='x unified',
                    height=420,
                ),
                '',
                df.head(10).to_dict('records'),
                X[:10]
            )
        else:
            error_msg = f'API Error ({response.status_code}): {response.text}'
            logger.error(error_msg)
            return dbc.Alert(error_msg, color='danger'), go.Figure(), '', None, None
    except requests.exceptions.Timeout:
        error_msg = 'API request timeout - please try again'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger'), go.Figure(), '', None, None
    except requests.exceptions.ConnectionError:
        error_msg = f'Cannot connect to API at {config.API_URL}'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger'), go.Figure(), '', None, None
        
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger'), go.Figure(), '', None, None

@app.callback(
    Output('shap-explanation', 'children'),
    Input({'type': 'explain-btn', 'index': dash.ALL}, 'n_clicks'),
    State('table-data-store', 'data'),
    State('last-pred-features', 'data'),
    prevent_initial_call=True
)
def show_shap_explanation(n_clicks_list, table_data, features_data):
    if not n_clicks_list or not any(n_clicks_list):
        return ''
    # Find which button was clicked
    idx = n_clicks_list.index(max(n_clicks_list))
    if features_data is None or idx >= len(features_data):
        return ''
    # Get features for this row
    row_features = [features_data[idx]]
    try:
        logger.info(f"Making explanation request for row {idx}")
        response = requests.post(f'{config.API_URL}/explain', json={'features': row_features}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            shap_vals = data['shap_values'][0]
            feature_names = data['feature_names']
            pred = data['predictions'][0]
            fig = go.Figure([
                go.Bar(x=feature_names, y=shap_vals, marker_color='#3aafa9')
            ])
            fig.update_layout(
                title=f'Feature Attribution for Prediction (Value: {pred:.4f})',
                xaxis_title='Feature',
                yaxis_title='SHAP Value',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Nunito, Inter, Segoe UI, Arial, sans-serif', size=15),
                margin=dict(l=40, r=40, t=60, b=40),
                height=320,
            )
            return dcc.Graph(figure=fig)
        else:
            error_msg = f'API Error ({response.status_code}): {response.text}'
            logger.error(error_msg)
            return dbc.Alert(error_msg, color='danger')
    except requests.exceptions.Timeout:
        error_msg = 'API request timeout - please try again'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger')
    except requests.exceptions.ConnectionError:
        error_msg = f'Cannot connect to API at {config.API_URL}'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger')
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        logger.error(error_msg)
        return dbc.Alert(error_msg, color='danger')

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run the dashboard
    app.run(
        host=config.DASH_HOST,
        port=config.DASH_PORT,
        debug=config.is_development
    )
