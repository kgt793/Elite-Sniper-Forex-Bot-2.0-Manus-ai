import math

class RiskManagementCalculator:
    """
    Risk Management Calculator for Forex Trading
    
    This calculator implements:
    - Position sizing based on account balance and risk percentage
    - Drawdown tracking based on previous day's balance
    - Stop loss calculation based on entry price and risk amount
    """
    
    def __init__(self, starting_balance=5000, risk_percentage=0.2, drawdown_percentage=8):
        """
        Initialize the Risk Management Calculator
        
        Args:
            starting_balance (float): Initial account balance in USD
            risk_percentage (float): Risk per trade as percentage of account balance
            drawdown_percentage (float): Maximum allowed drawdown as percentage of previous day's balance
        """
        self.balance = starting_balance
        self.previous_day_balance = starting_balance
        self.risk_percentage = risk_percentage / 100  # Convert to decimal
        self.drawdown_percentage = drawdown_percentage / 100  # Convert to decimal
        self.max_drawdown_amount = self.previous_day_balance * self.drawdown_percentage
        self.current_drawdown = 0
        self.trades_today = 0
        
    def update_balance(self, new_balance):
        """
        Update the current account balance
        
        Args:
            new_balance (float): New account balance
            
        Returns:
            float: Current drawdown amount
        """
        old_balance = self.balance
        self.balance = new_balance
        
        # Update drawdown if balance decreased
        if new_balance < old_balance:
            self.current_drawdown += (old_balance - new_balance)
        
        return self.current_drawdown
    
    def new_trading_day(self):
        """
        Reset for a new trading day
        
        Returns:
            float: Maximum drawdown amount for the new day
        """
        self.previous_day_balance = self.balance
        self.max_drawdown_amount = self.previous_day_balance * self.drawdown_percentage
        self.current_drawdown = 0
        self.trades_today = 0
        
        return self.max_drawdown_amount
    
    def calculate_position_size(self, entry_price, stop_loss_price, pair_info=None):
        """
        Calculate the appropriate position size based on risk parameters
        
        Args:
            entry_price (float): Entry price for the trade
            stop_loss_price (float): Stop loss price for the trade
            pair_info (dict, optional): Information about the currency pair
            
        Returns:
            dict: Position size information including:
                - risk_amount: Dollar amount at risk
                - position_size: Position size in standard lots
                - pip_value: Value of one pip for this position
                - stop_loss_pips: Distance to stop loss in pips
        """
        # Calculate risk amount in dollars
        risk_amount = self.balance * self.risk_percentage
        
        # Calculate stop loss distance in pips
        if entry_price > stop_loss_price:  # Long position
            stop_loss_pips = (entry_price - stop_loss_price) * 10000
        else:  # Short position
            stop_loss_pips = (stop_loss_price - entry_price) * 10000
        
        # Calculate position size in standard lots
        # For simplicity, assuming 1 pip = $10 for 1 standard lot for most pairs
        pip_value = 10  # Default value for 1 standard lot
        
        if pair_info and 'pip_value' in pair_info:
            pip_value = pair_info['pip_value']
            
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round down to nearest 0.01 lot
        position_size = math.floor(position_size * 100) / 100
        
        return {
            'risk_amount': risk_amount,
            'position_size': position_size,
            'pip_value': pip_value,
            'stop_loss_pips': stop_loss_pips
        }
    
    def can_place_trade(self):
        """
        Check if a new trade can be placed based on drawdown limits
        
        Returns:
            bool: True if a new trade can be placed, False otherwise
            str: Message explaining the decision
        """
        if self.current_drawdown >= self.max_drawdown_amount:
            return False, f"Daily drawdown limit reached: ${self.current_drawdown:.2f} of ${self.max_drawdown_amount:.2f}"
        
        return True, "Trade allowed within risk parameters"
    
    def get_risk_metrics(self):
        """
        Get current risk metrics
        
        Returns:
            dict: Current risk metrics
        """
        return {
            'balance': self.balance,
            'previous_day_balance': self.previous_day_balance,
            'risk_percentage': self.risk_percentage * 100,
            'drawdown_percentage': self.drawdown_percentage * 100,
            'max_drawdown_amount': self.max_drawdown_amount,
            'current_drawdown': self.current_drawdown,
            'drawdown_percentage_used': (self.current_drawdown / self.max_drawdown_amount * 100) if self.max_drawdown_amount > 0 else 0,
            'trades_today': self.trades_today
        }
    
    def simulate_trade_outcome(self, entry_price, position_size, take_profit_price=None, stop_loss_price=None, actual_exit_price=None, pair_info=None):
        """
        Simulate the outcome of a trade
        
        Args:
            entry_price (float): Entry price for the trade
            position_size (float): Position size in standard lots
            take_profit_price (float, optional): Take profit price
            stop_loss_price (float, optional): Stop loss price
            actual_exit_price (float, optional): Actual exit price if known
            pair_info (dict, optional): Information about the currency pair
            
        Returns:
            dict: Trade outcome information
        """
        pip_value = 10  # Default value for 1 standard lot
        
        if pair_info and 'pip_value' in pair_info:
            pip_value = pair_info['pip_value']
        
        # Determine exit price
        exit_price = actual_exit_price
        if exit_price is None:
            if take_profit_price is not None and stop_loss_price is not None:
                # Randomly choose between take profit and stop loss for simulation
                import random
                exit_price = random.choice([take_profit_price, stop_loss_price])
            elif take_profit_price is not None:
                exit_price = take_profit_price
            elif stop_loss_price is not None:
                exit_price = stop_loss_price
            else:
                return {"error": "No exit price provided for simulation"}
        
        # Calculate profit/loss
        if entry_price < exit_price:  # Long position
            pip_difference = (exit_price - entry_price) * 10000
        else:  # Short position
            pip_difference = (entry_price - exit_price) * 10000
        
        profit_loss = pip_difference * pip_value * position_size
        
        # Update balance and drawdown
        new_balance = self.balance + profit_loss
        self.update_balance(new_balance)
        self.trades_today += 1
        
        return {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'pip_difference': pip_difference,
            'profit_loss': profit_loss,
            'new_balance': new_balance
        }


# Example usage
if __name__ == "__main__":
    # Initialize calculator with $5000 balance, 0.2% risk per trade, 8% max drawdown
    calculator = RiskManagementCalculator(5000, 0.2, 8)
    
    # Get current risk metrics
    metrics = calculator.get_risk_metrics()
    print("Initial Risk Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Calculate position size for a trade
    entry_price = 1.2000
    stop_loss_price = 1.1950
    
    position_info = calculator.calculate_position_size(entry_price, stop_loss_price)
    print("\nPosition Size Calculation:")
    for key, value in position_info.items():
        print(f"  {key}: {value}")
    
    # Check if trade can be placed
    can_trade, message = calculator.can_place_trade()
    print(f"\nCan place trade: {can_trade}")
    print(f"Message: {message}")
    
    # Simulate a trade outcome
    trade_result = calculator.simulate_trade_outcome(
        entry_price=entry_price,
        position_size=position_info['position_size'],
        stop_loss_price=stop_loss_price,
        take_profit_price=1.2100
    )
    
    print("\nTrade Simulation Result:")
    for key, value in trade_result.items():
        print(f"  {key}: {value}")
    
    # Get updated risk metrics
    updated_metrics = calculator.get_risk_metrics()
    print("\nUpdated Risk Metrics:")
    for key, value in updated_metrics.items():
        print(f"  {key}: {value}")
    
    # Start a new trading day
    max_drawdown = calculator.new_trading_day()
    print(f"\nNew trading day started. Max drawdown: ${max_drawdown:.2f}")
