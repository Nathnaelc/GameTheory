# gametheory.py
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
        self.rate_of_return = rate_of_return  # Annual rate of return
        self.windfall = windfall  # Additional windfall revenue
        self.payoff_matrix = {}
        self.generate_payoff_matrix()
        self.nash_equilibria = self.find_nash_equilibria()
        self.dominant_strategies = self.find_dominant_strategies()
        self.repeated_game_analysis = self.analyze_repeated_game(discount_factor=0.9)
    
    def generate_payoff_matrix(self):
        """
        Generates a payoff matrix for all pricing combinations of Waymo and Cruise.
        """
        strategies = list(self.price_tiers.keys())
        for w_strategy in strategies:
            for c_strategy in strategies:
                w_payoff, c_payoff = self.calculate_payoffs(w_strategy, c_strategy)
                self.payoff_matrix[(w_strategy, c_strategy)] = (w_payoff, c_payoff)
        return self.payoff_matrix

    def calculate_payoffs(self, w_strategy, c_strategy):
        """
        Calculate payoffs for a given combination of Waymo's and Cruise's strategies.
        
        :param w_strategy: Waymo's pricing strategy
        :param c_strategy: Cruise's pricing strategy
        :return: Tuple of (Waymo Payoff, Cruise Payoff)
        """
        price_diff = self.price_tiers[c_strategy] - self.price_tiers[w_strategy]
        waymo_share = 0.5 + (price_diff * self.demand_elasticity)
        waymo_share = max(0.1, min(0.9, waymo_share))
        cruise_share = 1 - waymo_share

        # Calculate revenues
        waymo_revenue = waymo_share * self.market_size * self.price_tiers[w_strategy]
        cruise_revenue = cruise_share * self.market_size * self.price_tiers[c_strategy]

        # Apply windfall if applicable
        waymo_revenue += self.windfall if w_strategy == 'High' else 0
        cruise_revenue += self.windfall if c_strategy == 'High' else 0

        # Calculate payoffs including rate of return
        waymo_payoff = waymo_revenue * (1 + self.rate_of_return)
        cruise_payoff = cruise_revenue * (1 + self.rate_of_return)

        # Introduce potential negative payoffs (e.g., strategic pricing leading to losses)
        # For simplicity, assume that if a company's price is 'Low' and their revenue is significantly lower, they incur a loss
        if w_strategy == 'Low' and waymo_revenue < 0.8 * (self.market_size * self.price_tiers['High']):
            waymo_payoff -= 50000  # Arbitrary loss
        if c_strategy == 'Low' and cruise_revenue < 0.8 * (self.market_size * self.price_tiers['High']):
            cruise_payoff -= 50000  # Arbitrary loss

        return waymo_payoff, cruise_payoff

    def find_nash_equilibria(self):
        """
        Identifies Nash equilibria in the payoff matrix.
        
        :return: List of Nash equilibria dictionaries
        """
        strategies = list(self.price_tiers.keys())
        nash_equilibria = []

        for w_strategy in strategies:
            for c_strategy in strategies:
                w_payoff, c_payoff = self.payoff_matrix[(w_strategy, c_strategy)]

                # Check if Waymo could improve payoff by changing strategy
                waymo_best_response = all(
                    w_payoff >= self.payoff_matrix[(alt_w, c_strategy)][0]
                    for alt_w in strategies
                )

                # Check if Cruise could improve payoff by changing strategy
                cruise_best_response = all(
                    c_payoff >= self.payoff_matrix[(w_strategy, alt_c)][1]
                    for alt_c in strategies
                )

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
        Identifies dominant strategies for Waymo and Cruise.
        
        :return: Dictionary with dominant strategies for Waymo and Cruise
        """
        strategies = list(self.price_tiers.keys())
        waymo_dominant = None
        cruise_dominant = None

        # Waymo's dominant strategy
        for w_strategy in strategies:
            is_dominant = True
            for other_w in strategies:
                if other_w != w_strategy:
                    for c_strategy in strategies:
                        w_payoff = self.payoff_matrix[(w_strategy, c_strategy)][0]
                        other_w_payoff = self.payoff_matrix[(other_w, c_strategy)][0]
                        if w_payoff < other_w_payoff:
                            is_dominant = False
                            break
                    if not is_dominant:
                        break
            if is_dominant:
                waymo_dominant = w_strategy
                break

        # Cruise's dominant strategy
        for c_strategy in strategies:
            is_dominant = True
            for other_c in strategies:
                if other_c != c_strategy:
                    for w_strategy in strategies:
                        c_payoff = self.payoff_matrix[(w_strategy, c_strategy)][1]
                        other_c_payoff = self.payoff_matrix[(w_strategy, other_c)][1]
                        if c_payoff < other_c_payoff:
                            is_dominant = False
                            break
                    if not is_dominant:
                        break
            if is_dominant:
                cruise_dominant = c_strategy
                break

        return {'Waymo': waymo_dominant, 'Cruise': cruise_dominant}

    def analyze_repeated_game(self, discount_factor):
        """
        Analyzes the repeated game using Grim Trigger or other strategies.
        
        :param discount_factor: Discount factor for future payoffs
        :return: Dictionary with repeated game analysis
        """
        # Cooperation payoff when both choose 'High'
        cooperation_payoff = self.payoff_matrix[('High', 'High')]
        # Defection payoff when one defects to 'Low' and the other stays at 'High'
        waymo_defect_payoff = self.payoff_matrix[('Low', 'High')]
        cruise_defect_payoff = self.payoff_matrix[('High', 'Low')]

        # Punishment payoff when both choose 'Low'
        punishment_payoff = self.payoff_matrix[('Low', 'Low')]

        # Temptation payoff
        waymo_temptation = waymo_defect_payoff[0]
        cruise_temptation = cruise_defect_payoff[1]

        # Calculate critical discount factor for Grim Trigger
        waymo_delta = (waymo_temptation - cooperation_payoff[0]) / (waymo_temptation - punishment_payoff[0])
        cruise_delta = (cruise_temptation - cooperation_payoff[1]) / (cruise_temptation - punishment_payoff[1])

        # Determine if cooperation can be sustained
        can_cooperate_waymo = discount_factor >= waymo_delta
        can_cooperate_cruise = discount_factor >= cruise_delta

        return {
            'Waymo Critical Discount Factor': waymo_delta,
            'Cruise Critical Discount Factor': cruise_delta,
            'Discount Factor': discount_factor,
            'Can Sustain Cooperation (Waymo)': can_cooperate_waymo,
            'Can Sustain Cooperation (Cruise)': can_cooperate_cruise
        }

    def get_game_theory_metrics(self, discount_factor=0.9):
        """
        Retrieves the repeated game analysis metrics.
        
        :param discount_factor: Discount factor for future payoffs
        :return: Dictionary with repeated game analysis
        """
        return self.analyze_repeated_game(discount_factor)

    def update_parameters(self, rate_of_return=None, windfall=None):
        """
        Updates rate of return and windfall parameters and regenerates the payoff matrix.
        
        :param rate_of_return: New rate of return
        :param windfall: New windfall revenue
        """
        if rate_of_return is not None:
            self.rate_of_return = rate_of_return
        if windfall is not None:
            self.windfall = windfall
        self.generate_payoff_matrix()
        self.nash_equilibria = self.find_nash_equilibria()
        self.dominant_strategies = self.find_dominant_strategies()
        self.repeated_game_analysis = self.analyze_repeated_game(discount_factor=0.9)
