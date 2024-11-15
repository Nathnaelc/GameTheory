# decisiontree.py
import plotly.graph_objects as go
import networkx as nx

class RideShareGameAnalyzer:
    def __init__(self, market_size=1000000, price_sensitivity=0.3, scenario='Short-term'):
        self.market_size = market_size
        self.price_sensitivity = price_sensitivity
        self.scenario = scenario
        
        self.price_tiers = {
            "High": 25,
            "Medium": 20,
            "Low": 15
        }
        
        # Add abbreviations for node labels
        self.node_abbrev = {
            "High": "H",
            "Medium": "M",
            "Low": "L"
        }
        
        self.nodes = {}
        self.edges = []
        self.initialize_game()

    def initialize_game(self):
        """
        Initializes nodes and edges for the decision tree.
        """
        self.nodes = self.initialize_nodes()
        self.edges = self.initialize_edges()

    def initialize_nodes(self):
        base_nodes = {
            "Start": {"label": "Start", "short_label": "S", "payoff": None, "pos": (0, 2)},
            "W_High": {"label": "Waymo High ($25)", "short_label": "W-H", "payoff": None, "pos": (-2, 1)},
            "W_Medium": {"label": "Waymo Medium ($20)", "short_label": "W-M", "payoff": None, "pos": (0, 1)},
            "W_Low": {"label": "Waymo Low ($15)", "short_label": "W-L", "payoff": None, "pos": (2, 1)},
        }

        for w_price in ["High", "Medium", "Low"]:
            for c_price in ["High", "Medium", "Low"]:
                node_key = f"C_{w_price}_{c_price}"
                
                # Calculate market dynamics
                price_diff = self.price_tiers[c_price] - self.price_tiers[w_price]
                waymo_share = 0.5 + (price_diff * self.price_sensitivity)
                waymo_share = max(0.1, min(0.9, waymo_share))
                cruise_share = 1 - waymo_share

                # Calculate revenues and payoffs
                waymo_revenue = waymo_share * self.market_size * self.price_tiers[w_price]
                cruise_revenue = cruise_share * self.market_size * self.price_tiers[c_price]

                if self.scenario == 'Long-term':
                    waymo_payoff = waymo_revenue * 12
                    cruise_payoff = cruise_revenue * 12
                else:
                    waymo_payoff = waymo_revenue
                    cruise_payoff = cruise_revenue

                # Penalties for low pricing
                if w_price == 'Low' and waymo_revenue < 0.8 * (self.market_size * self.price_tiers['High']):
                    waymo_payoff -= 50000
                if c_price == 'Low' and cruise_revenue < 0.8 * (self.market_size * self.price_tiers['High']):
                    cruise_payoff -= 50000

                # Normalize payoffs
                max_possible_revenue = self.market_size * max(self.price_tiers.values()) * (12 if self.scenario == 'Long-term' else 1)
                waymo_payoff_normalized = int((waymo_payoff / max_possible_revenue) * 100)
                cruise_payoff_normalized = int((cruise_payoff / max_possible_revenue) * 100)
                
                # Ensure non-negative payoffs
                waymo_payoff_normalized = max(0, waymo_payoff_normalized)
                cruise_payoff_normalized = max(0, cruise_payoff_normalized)

                # Create short label using abbreviations
                short_label = f"{self.node_abbrev[w_price]}-{self.node_abbrev[c_price]}"

                base_nodes[node_key] = {
                    "label": f"W:{w_price}/C:{c_price}",
                    "short_label": short_label,
                    "payoff": (waymo_payoff_normalized, cruise_payoff_normalized),
                    "pos": self.get_terminal_position(w_price, c_price),
                    "market_share": (waymo_share, cruise_share),
                    "revenue": (waymo_payoff, cruise_payoff),
                    "avg_price": (self.price_tiers[w_price], self.price_tiers[c_price]),
                    "w_price": w_price,
                    "c_price": c_price
                }

        return base_nodes
    


    def get_terminal_position(self, w_price, c_price):
        """
        Calculate terminal node positions to prevent overlap.
        
        :param w_price: Waymo's pricing strategy
        :param c_price: Cruise's pricing strategy
        :return: Tuple representing (x, y) coordinates
        """
        base_x = {"High": -4, "Medium": 0, "Low": 4}
        offset = {"High": -1.5, "Medium": 0, "Low": 1.5}
        return (base_x[w_price] + offset[c_price], 0)

    def initialize_edges(self):
        """
        Initializes edges with strategic implications.
        
        :return: List of edges with attributes
        """
        return [
            ("Start", "W_High", "royalblue", "High-price strategy: Focus on premium service"),
            ("Start", "W_Medium", "royalblue", "Balanced strategy: Market share vs. profit"),
            ("Start", "W_Low", "royalblue", "Market penetration: Maximize market share"),
            ("W_High", f"C_High_High", "green", "Price matching: Maintain margins"),
            ("W_High", f"C_High_Medium", "green", "Moderate undercut: Gain share"),
            ("W_High", f"C_High_Low", "green", "Aggressive undercut: Maximize share"),
            ("W_Medium", f"C_Medium_High", "orange", "Premium positioning"),
            ("W_Medium", f"C_Medium_Medium", "orange", "Match and compete"),
            ("W_Medium", f"C_Medium_Low", "orange", "Value leadership"),
            ("W_Low", f"C_Low_High", "red", "Premium differentiation"),
            ("W_Low", f"C_Low_Medium", "red", "Upmarket response"),
            ("W_Low", f"C_Low_Low", "red", "Match at bottom")
        ]

    def find_nash_equilibrium(self):
        """
        Finds Nash equilibrium states.
        
        :return: List of Nash equilibria node keys
        """
        equilibria = []

        # Collect payoffs for all combinations
        waymo_strategies = ["High", "Medium", "Low"]
        cruise_strategies = ["High", "Medium", "Low"]
        waymo_payoffs = {}
        cruise_payoffs = {}

        for w_price in waymo_strategies:
            for c_price in cruise_strategies:
                node_key = f"C_{w_price}_{c_price}"
                payoff = self.nodes[node_key]["payoff"]
                waymo_payoffs[(w_price, c_price)] = payoff[0]
                cruise_payoffs[(w_price, c_price)] = payoff[1]

        # Find best responses
        for w_price in waymo_strategies:
            for c_price in cruise_strategies:
                node_key = f"C_{w_price}_{c_price}"
                waymo_payoff = waymo_payoffs[(w_price, c_price)]
                cruise_payoff = cruise_payoffs[(w_price, c_price)]

                # Waymo's best response
                waymo_best = True
                for alt_w in waymo_strategies:
                    if alt_w != w_price:
                        if waymo_payoffs[(alt_w, c_price)] > waymo_payoff:
                            waymo_best = False
                            break

                # Cruise's best response
                cruise_best = True
                for alt_c in cruise_strategies:
                    if alt_c != c_price:
                        if cruise_payoffs[(w_price, alt_c)] > cruise_payoff:
                            cruise_best = False
                            break

                if waymo_best and cruise_best:
                    equilibria.append(node_key)

        return equilibria

    def create_visualization(self, selected_waymo=None, selected_cruise=None):
        """
        Creates an interactive decision tree visualization using NetworkX and Plotly.
        
        :param selected_waymo: Selected Waymo strategy
        :param selected_cruise: Selected Cruise strategy
        :return: Plotly Figure object
        """
        G = nx.DiGraph()

        # Add nodes
        for key, val in self.nodes.items():
            G.add_node(key, **val)

        # Add edges
        for edge in self.edges:
            src, dst, color, strategy = edge
            if src in self.nodes and dst in self.nodes:  # Add safety check
                G.add_edge(src, dst, color=color, strategy=strategy)

        # Get positions
        pos = {key: val['pos'] for key, val in self.nodes.items()}

        # Edge traces
        edge_traces = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_color = edge[2]['color']
            if selected_waymo and edge[0] == 'Start':
                if edge[1] != f"W_{selected_waymo}":
                    edge_color = 'lightgrey'
            if selected_waymo and selected_cruise and edge[0].startswith('W_'):
                if edge[1] != f"C_{selected_waymo}_{selected_cruise}":
                    edge_color = 'lightgrey'
            edge_trace = go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                line=dict(width=2, color=edge_color),
                hoverinfo='text',
                mode='lines',
                hovertext=edge[2]['strategy'],
                showlegend=False
            )
            edge_traces.append(edge_trace)

        # Node traces
        node_x = []
        node_y = []
        hover_texts = []
        customdata = []
        marker_colors = []
        marker_symbols = []
        marker_sizes = []

        equilibria = self.find_nash_equilibrium()

        for node in G.nodes(data=True):
            x, y = node[1]['pos']
            node_x.append(x)
            node_y.append(y)

            val = node[1]

            # Create short hover text
            hover_text = val['label']

            hover_texts.append(hover_text)
            customdata.append(node[0])  # Node key for callback identification

            # Determine marker color
            node_color = self.get_node_color(val)
            if selected_waymo and val['label'] != 'Waymo\'s Initial Move':
                if val['label'] != f"Waymo {selected_waymo} (${self.price_tiers[selected_waymo]})":
                    node_color = 'lightgrey'

            if selected_waymo and selected_cruise and val.get('w_price') and val.get('c_price'):
                if val['w_price'] != selected_waymo or val['c_price'] != selected_cruise:
                    node_color = 'lightgrey'

            # Highlight Nash equilibria
            if node[0] in equilibria:
                marker_size = 30
                if not selected_waymo and not selected_cruise:
                    node_color = 'gold'
            else:
                marker_size = 25

            marker_colors.append(node_color)
            marker_symbols.append(self.get_node_symbol(val))
            marker_sizes.append(marker_size)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hovertext=hover_texts,
            hoverinfo='text',
            customdata=customdata,
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                line=dict(width=2, color='black'),
                symbol=marker_symbols
            ),
            showlegend=False
        )

        # Create the figure
        fig = go.Figure()

        # Add edge traces
        for edge_trace in edge_traces:
            fig.add_trace(edge_trace)

        # Add node trace
        fig.add_trace(node_trace)

        # Add node labels as annotations to prevent overlap
        for i, node in enumerate(G.nodes(data=True)):
            x, y = node[1]['pos']
            label = node[1]['label']
            if y == 0:
                y_offset = -20
            else:
                y_offset = 20
            fig.add_annotation(
                x=x,
                y=y,
                text=label,
                showarrow=False,
                yshift=y_offset,
                font=dict(size=10)
            )

        # Update layout
        fig.update_layout(
            title={
                'text': "Advanced Game Theory Analysis: Waymo vs Cruise Pricing Strategy",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=False,
            width=1000,
            height=700,
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            clickmode='event+select'  # Enable click events
        )

        # Remove axis labels and grid
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)

        return fig

    def get_node_color(self, node):
        """
        Determines node color based on payoff.
        
        :param node: Node attributes
        :return: Color string
        """
        if not node.get("payoff"):
            return "lightblue"

        total_payoff = sum(node["payoff"])

        total_payoff = max(0, min(total_payoff, 200))
        # Color gradient from red (low) to green (high)
        green_value = int((total_payoff / 200) * 255)
        red_value = 255 - green_value
        return f"rgb({red_value}, {green_value}, 100)"

    def get_node_symbol(self, node):
        """
        Determines node symbol based on type.
        
        :param node: Node attributes
        :return: Symbol string
        """
        if not node.get("payoff"):
            return "circle"
        return "square"

    def get_node_info(self, node_key):
        """
        Retrieves detailed information for a given node key.
        
        :param node_key: Key of the node
        :return: Dictionary with node information
        """
        if node_key in self.nodes:
            val = self.nodes[node_key]
            if val.get('payoff'):
                w_price = val['w_price']
                c_price = val['c_price']
                current_payoff = val['payoff']

                # Waymo's alternative payoffs
                waymo_alt_payoffs = []
                for alt_w in ["High", "Medium", "Low"]:
                    if alt_w != w_price:
                        alt_node_key = f"C_{alt_w}_{c_price}"
                        alt_payoff = self.nodes[alt_node_key]['payoff']
                        diff = alt_payoff[0] - current_payoff[0]
                        waymo_alt_payoffs.append({'Strategy': alt_w, 'Payoff Change': f"{diff:+}%"})

                # Cruise's alternative payoffs
                cruise_alt_payoffs = []
                for alt_c in ["High", "Medium", "Low"]:
                    if alt_c != c_price:
                        alt_node_key = f"C_{w_price}_{alt_c}"
                        alt_payoff = self.nodes[alt_node_key]['payoff']
                        diff = alt_payoff[1] - current_payoff[1]
                        cruise_alt_payoffs.append({'Strategy': alt_c, 'Payoff Change': f"{diff:+}%"})

                node_info = {
                    'Node': val['label'],
                    'Waymo Payoff': f"{val['payoff'][0]}%",
                    'Cruise Payoff': f"{val['payoff'][1]}%",
                    'Market Share': f"{val['market_share'][0]:.1%} / {val['market_share'][1]:.1%}",
                    'Revenue': f"${val['revenue'][0]:,.0f} / ${val['revenue'][1]:,.0f}",
                    'Average Price': f"${val['avg_price'][0]} / ${val['avg_price'][1]}",
                    'Waymo Alternative Payoffs': waymo_alt_payoffs,
                    'Cruise Alternative Payoffs': cruise_alt_payoffs
                }
                return node_info
            else:
                return {'Node': val['label']}
        else:
            return {}