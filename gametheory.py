import numpy as np

class GameTheorySimulator:
    def __init__(self, price_tiers, demand_elasticity=0.3, market_size=1000000, rate_of_return=0.05, windfall=0):
        """
        Initialize the GameTheorySimulator with relevant parameters.
        
        :param price_tiers: Dictionary of price strategies, e.g., {"High": 25, "Medium": 20, "Low": 15}
        :param demand_elasticity: Elasticity coefficient influencing market share based on price differences
        :param market_size: Total market size (e.g., number of rides)
        :param rate_of_return: Annual rate of return (e.g., 0.05 for 5%)
        :param windfall: Additional windfall revenue when choosing 'High' strategy
        """
        self.price_tiers = price_tiers
        self.demand_elasticity = demand_elasticity
        self.market_size = market_size
        self.rate_of_return = rate_of_return
        self.windfall = windfall
        self.payoff_matrix = {}
        self.generate_payoff_matrix()
        self.nash_equilibria = self.find_nash_equilibria()
        self.dominant_strategies = self.find_dominant_strategies()
        self.repeated_game_analysis = self.analyze_repeated_game(discount_factor=0.9)
    
    def calculate_market_share(self, price_diff):
        """
        Calculate market share using a modified logistic function for more realistic elasticity.
        
        :param price_diff: Price difference between competitors
        :return: Market share for Waymo (between 0.1 and 0.9)
        """
        # Using sigmoid function for more realistic market response
        base_share = 0.5
        max_adjustment = 0.4  # Maximum deviation from 50/50 split
        
        # Normalize price difference by average price
        avg_price = np.mean(list(self.price_tiers.values()))
        normalized_diff = price_diff / avg_price
        
        # Apply sigmoid function
        adjustment = max_adjustment * (2 / (1 + np.exp(-self.demand_elasticity * normalized_diff)) - 1)
        share = base_share + adjustment
        
        # Ensure share stays within reasonable bounds
        return np.clip(share, 0.1, 0.9)

    def calculate_payoffs(self, w_strategy, c_strategy):
        """
        Calculate payoffs with enhanced market dynamics and cost considerations.
        """
        # Calculate price difference and market share
        price_diff = self.price_tiers[c_strategy] - self.price_tiers[w_strategy]
        waymo_share = self.calculate_market_share(price_diff)
        cruise_share = 1 - waymo_share

        # Base revenue calculation
        waymo_revenue = waymo_share * self.market_size * self.price_tiers[w_strategy]
        cruise_revenue = cruise_share * self.market_size * self.price_tiers[c_strategy]

        # Cost considerations based on pricing strategy
        cost_factor = {
            'High': 0.6,    # Higher prices assume premium service with higher costs
            'Medium': 0.7,  # Medium pricing with balanced costs
            'Low': 0.8     # Low pricing requires higher operational efficiency
        }

        # Apply costs
        waymo_costs = waymo_revenue * cost_factor[w_strategy]
        cruise_costs = cruise_revenue * cost_factor[c_strategy]

        # Calculate profits
        waymo_profit = waymo_revenue - waymo_costs
        cruise_profit = cruise_revenue - cruise_costs

        # Apply windfall if applicable
        waymo_profit += self.windfall if w_strategy == 'High' else 0
        cruise_profit += self.windfall if c_strategy == 'High' else 0

        # Apply rate of return
        waymo_payoff = waymo_profit * (1 + self.rate_of_return)
        cruise_payoff = cruise_profit * (1 + self.rate_of_return)

        # Market share penalties for extreme price differences
        if abs(price_diff) > max(self.price_tiers.values()) * 0.4:
            if w_strategy == 'Low' and c_strategy == 'High':
                waymo_payoff *= 0.9  # Penalty for being too cheap compared to competitor
            elif w_strategy == 'High' and c_strategy == 'Low':
                waymo_payoff *= 0.85  # Higher penalty for being too expensive

        return waymo_payoff, cruise_payoff

    def generate_payoff_matrix(self):
        """
        Generates a payoff matrix for all pricing combinations.
        """
        strategies = list(self.price_tiers.keys())
        for w_strategy in strategies:
            for c_strategy in strategies:
                w_payoff, c_payoff = self.calculate_payoffs(w_strategy, c_strategy)
                self.payoff_matrix[(w_strategy, c_strategy)] = (w_payoff, c_payoff)
        return self.payoff_matrix

    def find_nash_equilibria(self):
        """
        Identifies Nash equilibria with improved precision and tolerance.
        """
        strategies = list(self.price_tiers.keys())
        nash_equilibria = []
        tolerance = 1e-6  # Small tolerance for floating-point comparisons

        for w_strategy in strategies:
            for c_strategy in strategies:
                w_payoff, c_payoff = self.payoff_matrix[(w_strategy, c_strategy)]
                
                # Check if either player can profitably deviate
                waymo_best_response = True
                cruise_best_response = True
                
                for alt_w in strategies:
                    alt_w_payoff = self.payoff_matrix[(alt_w, c_strategy)][0]
                    if alt_w_payoff > w_payoff + tolerance:
                        waymo_best_response = False
                        break
                
                for alt_c in strategies:
                    alt_c_payoff = self.payoff_matrix[(w_strategy, alt_c)][1]
                    if alt_c_payoff > c_payoff + tolerance:
                        cruise_best_response = False
                        break

                if waymo_best_response and cruise_best_response:
                    nash_equilibria.append({
                        'Waymo Strategy': w_strategy,
                        'Cruise Strategy': c_strategy,
                        'Waymo Payoff': w_payoff,
                        'Cruise Payoff': c_payoff
                    })

        return nash_equilibria

    def find_dominant_strategies(self):
        """
        Identifies dominant strategies with improved precision.
        """
        strategies = list(self.price_tiers.keys())
        tolerance = 1e-6
        
        def is_strictly_dominant(player_strategy, player_index):
            for other_strategy in strategies:
                if other_strategy == player_strategy:
                    continue
                    
                for opponent_strategy in strategies:
                    if player_index == 0:  # Waymo
                        strategy_payoff = self.payoff_matrix[(player_strategy, opponent_strategy)][0]
                        other_payoff = self.payoff_matrix[(other_strategy, opponent_strategy)][0]
                    else:  # Cruise
                        strategy_payoff = self.payoff_matrix[(opponent_strategy, player_strategy)][1]
                        other_payoff = self.payoff_matrix[(opponent_strategy, other_strategy)][1]
                        
                    if strategy_payoff <= other_payoff + tolerance:
                        return False
            return True
        
        waymo_dominant = None
        cruise_dominant = None
        
        for strategy in strategies:
            if is_strictly_dominant(strategy, 0):
                waymo_dominant = strategy
            if is_strictly_dominant(strategy, 1):
                cruise_dominant = strategy
                
        return {'Waymo': waymo_dominant, 'Cruise': cruise_dominant}

    def analyze_repeated_game(self, discount_factor):
        """
        Enhanced repeated game analysis with more sophisticated cooperation metrics.
        """
        # Get relevant payoffs
        coop_payoff = self.payoff_matrix[('High', 'High')]
        defect_waymo = self.payoff_matrix[('Low', 'High')]
        defect_cruise = self.payoff_matrix[('High', 'Low')]
        punish_payoff = self.payoff_matrix[('Low', 'Low')]

        # Calculate critical discount factors with protection against division by zero
        def safe_division(n, d):
            return n / d if abs(d) > 1e-10 else float('inf')

        waymo_delta = safe_division(
            defect_waymo[0] - coop_payoff[0],
            defect_waymo[0] - punish_payoff[0]
        )
        
        cruise_delta = safe_division(
            defect_cruise[1] - coop_payoff[1],
            defect_cruise[1] - punish_payoff[1]
        )

        # Determine if cooperation can be sustained
        can_cooperate_waymo = discount_factor >= waymo_delta
        can_cooperate_cruise = discount_factor >= cruise_delta

        # Calculate long-term cooperative payoff
        if can_cooperate_waymo and can_cooperate_cruise:
            waymo_ltv = coop_payoff[0] / (1 - discount_factor)
            cruise_ltv = coop_payoff[1] / (1 - discount_factor)
        else:
            waymo_ltv = punish_payoff[0] / (1 - discount_factor)
            cruise_ltv = punish_payoff[1] / (1 - discount_factor)

        return {
            'Waymo Critical Discount Factor': waymo_delta,
            'Cruise Critical Discount Factor': cruise_delta,
            'Discount Factor': discount_factor,
            'Can Sustain Cooperation (Waymo)': can_cooperate_waymo,
            'Can Sustain Cooperation (Cruise)': can_cooperate_cruise,
            'Long-term Value (Waymo)': waymo_ltv,
            'Long-term Value (Cruise)': cruise_ltv
        }