# app.py
import plotly.graph_objects as go
import networkx as nx
from dash import Dash, html, dcc, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc

# Import the modules
from decisiontree import RideShareGameAnalyzer
from gametheory import GameTheorySimulator

# Initialize the Dash application with suppress_callback_exceptions=True
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Define the layout with tabs for decision tree and payoff matrix
app.layout = dbc.Container([
    html.H1("Waymo vs Cruise: Pricing Strategy Analysis"),
    dbc.Tabs([
        dbc.Tab(label='Decision Tree', tab_id='decision-tree-tab'),
        dbc.Tab(label='Payoff Matrix', tab_id='payoff-matrix-tab'),
    ], id='tabs', active_tab='decision-tree-tab'),
    html.Div(id='tab-content'),
], fluid=True)

# Callback to render the content based on the active tab
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
)
def render_tab_content(active_tab):
    if active_tab == 'decision-tree-tab':
        return render_decision_tree_tab()
    elif active_tab == 'payoff-matrix-tab':
        return render_payoff_matrix_tab()
    return html.Div("Unknown Tab")

# Function to render the Decision Tree tab content
def render_decision_tree_tab():
    return dbc.Row([
        dbc.Col([
            html.Label("Demand Elasticity (Price Sensitivity):"),
            dcc.Slider(
                id='elasticity-slider',
                min=0.1,
                max=1.0,
                step=0.05,
                value=0.3,
                marks={i/10: f'{i/10}' for i in range(1, 11)}
            ),
            html.Br(),
            html.Label("Market Size:"),
            dcc.Input(
                id='market-size-input',
                type='number',
                value=1000000,
                min=100000,
                step=100000,
                style={'width': '100%'}
            ),
            html.Br(),
            html.Label("Scenario:"),
            dcc.RadioItems(
                id='scenario-radio',
                options=[
                    {'label': 'Short-term', 'value': 'Short-term'},
                    {'label': 'Long-term', 'value': 'Long-term'}
                ],
                value='Short-term',
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            ),
            html.Br(),
            html.Label("Select Waymo's Strategy:"),
            dcc.Dropdown(
                id='waymo-strategy-dropdown',
                options=[
                    {'label': 'High', 'value': 'High'},
                    {'label': 'Medium', 'value': 'Medium'},
                    {'label': 'Low', 'value': 'Low'},
                ],
                value=None,
                placeholder='Select Waymo\'s Strategy'
            ),
            html.Br(),
            html.Label("Select Cruise's Strategy:"),
            dcc.Dropdown(
                id='cruise-strategy-dropdown',
                options=[
                    {'label': 'High', 'value': 'High'},
                    {'label': 'Medium', 'value': 'Medium'},
                    {'label': 'Low', 'value': 'Low'},
                ],
                value=None,
                placeholder='Select Cruise\'s Strategy'
            ),
            html.Br(),
            dbc.Button("Reset Strategies", id='reset-button', color='primary'),
            html.Br(),
            html.Br(),
            html.Div(id='node-details', style={'whiteSpace': 'pre-wrap'})
        ], md=4),

        dbc.Col([
            dcc.Graph(id='game-tree-graph')
        ], md=8)
    ])

# Function to render the Payoff Matrix tab content
def render_payoff_matrix_tab():
    return dbc.Row([
        dbc.Col([
            html.Label("Demand Elasticity (Price Sensitivity):"),
            dcc.Slider(
                id='elasticity-slider-matrix',
                min=0.1,
                max=1.0,
                step=0.05,
                value=0.3,
                marks={i/10: f'{i/10}' for i in range(1, 11)}
            ),
            html.Br(),
            html.Label("Market Size:"),
            dcc.Input(
                id='market-size-input-matrix',
                type='number',
                value=1000000,
                min=100000,
                step=100000,
                style={'width': '100%'}
            ),
            html.Br(),
            html.Label("Rate of Return (%):"),
            dcc.Input(
                id='rate-of-return-input-matrix',
                type='number',
                value=5.0,
                min=0,
                step=0.1,
                style={'width': '100%'}
            ),
            html.Br(),
            html.Label("Windfall Revenue ($):"),
            dcc.Input(
                id='windfall-input-matrix',
                type='number',
                value=0,
                min=0,
                step=10000,
                style={'width': '100%'}
            ),
            html.Br(),
            html.Label("Discount Factor for Repeated Game:"),
            dcc.Slider(
                id='discount-factor-slider',
                min=0.5,
                max=1.0,
                step=0.05,
                value=0.9,
                marks={i/10: f'{i/10}' for i in range(5, 11)}
            ),
            html.Br(),
            html.Label("Select Repeated Game Strategy:"),
            dcc.Dropdown(
                id='repeated-game-strategy-dropdown',
                options=[
                    {'label': 'Grim Trigger', 'value': 'Grim Trigger'},
                    {'label': 'Tit for Tat', 'value': 'Tit for Tat'},
                    {'label': 'Always Defect', 'value': 'Always Defect'},
                    {'label': 'Always Cooperate', 'value': 'Always Cooperate'},
                ],
                value='Grim Trigger',
                placeholder='Select Repeated Game Strategy'
            ),
        ], md=4),
        dbc.Col([
            html.Div(id='payoff-matrix-container'),
            html.Br(),
            html.Div(id='game-theory-analysis-container')
        ], md=8)
    ])

# Callback for the Decision Tree tab
@app.callback(
    Output('game-tree-graph', 'figure'),
    Output('node-details', 'children'),
    Input('elasticity-slider', 'value'),
    Input('market-size-input', 'value'),
    Input('scenario-radio', 'value'),
    Input('waymo-strategy-dropdown', 'value'),
    Input('cruise-strategy-dropdown', 'value'),
    Input('reset-button', 'n_clicks'),
    Input('game-tree-graph', 'clickData'),
    State('node-details', 'children')
)
def update_decision_tree(elasticity, market_size, scenario, waymo_strategy, cruise_strategy, reset_n_clicks, click_data, current_node_details):
    """
    Updates the decision tree graph and node details based on parameter changes and user interactions.
    """
    # Initialize the analyzer with updated parameters
    analyzer = RideShareGameAnalyzer(
        market_size=market_size,
        price_sensitivity=elasticity,
        scenario=scenario
    )
    
    # Handle reset button click
    ctx = callback_context
    if ctx.triggered and 'reset-button.n_clicks' in ctx.triggered[0]['prop_id']:
        waymo_strategy = None
        cruise_strategy = None
        elasticity = 0.3
        market_size = 1000000
        scenario = 'Short-term'
        # Reinitialize analyzer with default values
        analyzer = RideShareGameAnalyzer(
            market_size=market_size,
            price_sensitivity=elasticity,
            scenario=scenario
        )
    
    # Update strategies based on node click
    if click_data and 'points' in click_data:
        point = click_data['points'][0]
        node_key = point['customdata']
        node_data = analyzer.nodes[node_key]
        if node_key.startswith('W_'):
            waymo_strategy = node_data['label'].split(' ')[1]
            cruise_strategy = None
        elif node_key.startswith('C_'):
            waymo_strategy = node_data['w_price']
            cruise_strategy = node_data['c_price']
        # Get node details
        node_info = analyzer.get_node_info(node_key)
        details = ''
        for key, value in node_info.items():
            if isinstance(value, list):
                details += f"{key}:\n"
                for item in value:
                    details += f"  Strategy: {item['Strategy']}, Payoff Change: {item['Payoff Change']}\n"
            else:
                details += f"{key}: {value}\n"
    else:
        details = current_node_details

    # Create visualization
    fig = analyzer.create_visualization(selected_waymo=waymo_strategy, selected_cruise=cruise_strategy)

    return fig, details

# Callback for the Payoff Matrix tab
@app.callback(
    Output('payoff-matrix-container', 'children'),
    Output('game-theory-analysis-container', 'children'),
    Input('elasticity-slider-matrix', 'value'),
    Input('market-size-input-matrix', 'value'),
    Input('rate-of-return-input-matrix', 'value'),
    Input('windfall-input-matrix', 'value'),
    Input('discount-factor-slider', 'value'),
    Input('repeated-game-strategy-dropdown', 'value')
)
def update_payoff_matrix(elasticity, market_size, rate_of_return, windfall, discount_factor, repeated_game_strategy):
    """
    Updates the payoff matrix and game theory analysis based on parameter changes.
    """
    # Initialize the game theory simulator with updated parameters
    price_tiers = {"High": 25, "Medium": 20, "Low": 15}
    simulator = GameTheorySimulator(
        price_tiers=price_tiers,
        demand_elasticity=elasticity,
        market_size=market_size,
        rate_of_return=rate_of_return / 100,  # Convert percentage to decimal
        windfall=windfall
    )
    payoff_matrix = simulator.payoff_matrix
    nash_equilibria = simulator.nash_equilibria
    dominant_strategies = simulator.dominant_strategies

    # Repeated game analysis based on selected strategy
    repeated_game_analysis = {}
    strategy_explanation = ""
    if repeated_game_strategy == 'Grim Trigger':
        repeated_game_analysis = simulator.analyze_repeated_game(discount_factor)
        strategy_explanation = "Grim Trigger: If any player defects, the other player will defect forever."
    elif repeated_game_strategy == 'Tit for Tat':
        # Simplistic representation; real simulation would require iterative steps
        repeated_game_analysis = {
            'Waymo Critical Discount Factor': 0.85,
            'Cruise Critical Discount Factor': 0.85,
            'Discount Factor': discount_factor,
            'Can Sustain Cooperation (Waymo)': discount_factor >= 0.85,
            'Can Sustain Cooperation (Cruise)': discount_factor >= 0.85
        }
        strategy_explanation = "Tit for Tat: Players reciprocate each other's previous move."
    elif repeated_game_strategy == 'Always Defect':
        repeated_game_analysis = {}
        strategy_explanation = "Always Defect: Players always choose to defect regardless of the opponent's move."
    elif repeated_game_strategy == 'Always Cooperate':
        repeated_game_analysis = {}
        strategy_explanation = "Always Cooperate: Players always choose to cooperate regardless of the opponent's move."

    # Prepare data for the Dash DataTable
    strategies = list(price_tiers.keys())
    table_data = []

    for w_strategy in strategies:
        row = {'Waymo Strategy': w_strategy}
        for c_strategy in strategies:
            w_payoff, c_payoff = payoff_matrix[(w_strategy, c_strategy)]
            # Convert payoffs to millions for readability
            w_payoff_display = w_payoff / 1e6
            c_payoff_display = c_payoff / 1e6
            # Handle negative payoffs
            if w_payoff_display < 0:
                w_payoff_str = f"(${w_payoff_display:.2f}M)"
            else:
                w_payoff_str = f"(${w_payoff_display:.2f}M)"
            if c_payoff_display < 0:
                c_payoff_str = f"(${c_payoff_display:.2f}M)"
            else:
                c_payoff_str = f"(${c_payoff_display:.2f}M)"
            cell_value = f"({w_payoff_str}, {c_payoff_str})"
            # Highlight Nash equilibria
            is_nash = any(
                eq['Waymo Strategy'] == w_strategy and eq['Cruise Strategy'] == c_strategy
                for eq in nash_equilibria
            )
            row[c_strategy] = cell_value if not is_nash else f"**{cell_value}**"
        table_data.append(row)

    # Define columns
    columns = [{'name': 'Waymo Strategy', 'id': 'Waymo Strategy'}] + [
        {'name': f'Cruise {c_strategy}', 'id': c_strategy} for c_strategy in strategies
    ]

    # Create the DataTable
    data_table = dash_table.DataTable(
        data=table_data,
        columns=columns,
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {'filter_query': f'{{{c_strategy}}} contains "**"'},
                'backgroundColor': 'yellow',
                'fontWeight': 'bold'
            } for c_strategy in strategies
        ] + [
            {
                'if': {'column_id': 'Waymo Strategy'},
                'fontWeight': 'bold'
            }
        ],
        style_header={'fontWeight': 'bold'},
        export_format='csv',  # Allow users to export the table
    )

    # Game theory analysis text
    analysis_text = f"**Nash Equilibria:**\n"
    for eq in nash_equilibria:
        w_strategy = eq['Waymo Strategy']
        c_strategy = eq['Cruise Strategy']
        w_payoff_display = eq['Waymo Payoff'] / 1e6
        c_payoff_display = eq['Cruise Payoff'] / 1e6
        analysis_text += f"- Waymo: {w_strategy}, Cruise: {c_strategy} (Payoffs: Waymo ${w_payoff_display:.2f}M, Cruise ${c_payoff_display:.2f}M)\n"

    analysis_text += f"\n**Dominant Strategies:**\n"
    if dominant_strategies['Waymo']:
        analysis_text += f"- Waymo's dominant strategy: {dominant_strategies['Waymo']}\n"
    else:
        analysis_text += "- Waymo has no dominant strategy\n"
    if dominant_strategies['Cruise']:
        analysis_text += f"- Cruise's dominant strategy: {dominant_strategies['Cruise']}\n"
    else:
        analysis_text += "- Cruise has no dominant strategy\n"

    # Add repeated game analysis if available
    if repeated_game_analysis:
        analysis_text += f"\n**Repeated Game Analysis ({repeated_game_strategy} Strategy):**\n"
        if 'Waymo Critical Discount Factor' in repeated_game_analysis:
            analysis_text += f"- Waymo's critical discount factor: {repeated_game_analysis['Waymo Critical Discount Factor']:.2f}\n"
            analysis_text += f"- Cruise's critical discount factor: {repeated_game_analysis['Cruise Critical Discount Factor']:.2f}\n"
            analysis_text += f"- Current Discount Factor: {repeated_game_analysis['Discount Factor']:.2f}\n"
            analysis_text += f"- Can Sustain Cooperation (Waymo): {'Yes' if repeated_game_analysis['Can Sustain Cooperation (Waymo)'] else 'No'}\n"
            analysis_text += f"- Can Sustain Cooperation (Cruise): {'Yes' if repeated_game_analysis['Can Sustain Cooperation (Cruise)'] else 'No'}\n"
        analysis_text += f"\n*{strategy_explanation}*"

    return data_table, dcc.Markdown(analysis_text)
server = app.server
if __name__ == '__main__':
    app.run_server(debug=True)