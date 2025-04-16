import os
import requests
import json
from datetime import datetime

class IFTTTWebhook:
    """
    A class to send trade signals to IFTTT via webhooks
    """
    
    def __init__(self, webhook_key=None):
        """
        Initialize the IFTTT webhook integration
        
        Args:
            webhook_key (str): Your IFTTT webhook key (optional)
        """
        self.webhook_key = webhook_key or os.environ.get('IFTTT_WEBHOOK_KEY')
        self.webhook_url = f"https://maker.ifttt.com/trigger/{{event}}/with/key/{self.webhook_key}"
    
    def set_webhook_key(self, webhook_key):
        """
        Set the IFTTT webhook key
        
        Args:
            webhook_key (str): Your IFTTT webhook key
        """
        self.webhook_key = webhook_key
        self.webhook_url = f"https://maker.ifttt.com/trigger/{{event}}/with/key/{self.webhook_key}"
    
    def send_trade_signal(self, signal_data):
        """
        Send a trade signal to IFTTT
        
        Args:
            signal_data (dict): Trade signal data including:
                - pair_symbol: Currency pair symbol
                - signal_type: Type of signal (e.g., 'bullish_breakout', 'bearish_pattern')
                - entry_price: Entry price
                - stop_loss: Stop loss price
                - take_profit: Take profit price
                - confidence: Confidence score
                - timeframe: Timeframe of the signal
                - duration: Expected duration to reach take profit
                
        Returns:
            dict: Response from IFTTT webhook
        """
        if not self.webhook_key:
            raise ValueError("IFTTT webhook key not set")
        
        # Format the signal data for IFTTT
        event_name = "forex_signal"
        
        # Create a clean signal type for display
        signal_type_display = signal_data.get('signal_type', '').replace('_', ' ').title()
        
        # Format the values for IFTTT
        value1 = f"{signal_data.get('pair_symbol')} - {signal_type_display}"
        value2 = f"Entry: {signal_data.get('entry_price')} | SL: {signal_data.get('stop_loss')} | TP: {signal_data.get('take_profit')}"
        value3 = f"Confidence: {signal_data.get('confidence')}% | Duration: {signal_data.get('duration')} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Prepare the payload
        payload = {
            "value1": value1,
            "value2": value2,
            "value3": value3
        }
        
        # Send the webhook request
        url = self.webhook_url.format(event=event_name)
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Trade signal sent to IFTTT successfully",
                "response": response.text
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send trade signal to IFTTT: {response.status_code}",
                "response": response.text
            }
    
    def send_breakout_signal(self, breakout_data):
        """
        Send a breakout signal to IFTTT
        
        Args:
            breakout_data (dict): Breakout data from the breakout detector
                
        Returns:
            dict: Response from IFTTT webhook
        """
        if not self.webhook_key:
            raise ValueError("IFTTT webhook key not set")
        
        # Extract relevant data from the breakout
        pair_symbol = breakout_data.get('pair_symbol')
        breakout_type = breakout_data.get('type', 'unknown')
        price = breakout_data.get('price')
        
        # Calculate stop loss and take profit based on breakout type and percentage
        percentage = breakout_data.get('percentage', 0.001)
        if breakout_type == 'bullish':
            stop_loss = round(price * (1 - percentage * 1.5), 5)
            take_profit = round(price * (1 + percentage * 3), 5)
            duration = "1-2 days"
        else:  # bearish
            stop_loss = round(price * (1 + percentage * 1.5), 5)
            take_profit = round(price * (1 - percentage * 3), 5)
            duration = "1-2 days"
        
        # Create signal data
        signal_data = {
            'pair_symbol': pair_symbol,
            'signal_type': f"{breakout_type}_breakout",
            'entry_price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': int(min(breakout_data.get('strength', 0) * 10, 95)),
            'timeframe': breakout_data.get('timeframe', '1h'),
            'duration': duration
        }
        
        # Send the signal
        return self.send_trade_signal(signal_data)
    
    def send_pattern_signal(self, pattern_data, pair_symbol, price_data):
        """
        Send a pattern signal to IFTTT
        
        Args:
            pattern_data (dict): Pattern verification data
            pair_symbol (str): Currency pair symbol
            price_data (dict): Current price data
                
        Returns:
            dict: Response from IFTTT webhook
        """
        if not self.webhook_key:
            raise ValueError("IFTTT webhook key not set")
        
        # Extract relevant data
        pattern_name = pattern_data.get('top_pattern', 'unknown')
        confidence = pattern_data.get('confidence', 0) * 100
        
        # Get current price
        current_price = price_data.get('close', 0)
        
        # Determine if pattern is bullish or bearish
        bullish_patterns = ['double_bottom', 'inverse_head_and_shoulders', 'bullish_flag', 
                           'cup_and_handle', 'ascending_triangle', 'rounding_bottom']
        bearish_patterns = ['double_top', 'head_and_shoulders', 'bearish_flag',
                           'descending_triangle', 'rounding_top']
        
        is_bullish = any(p in pattern_name for p in bullish_patterns)
        is_bearish = any(p in pattern_name for p in bearish_patterns)
        
        if not (is_bullish or is_bearish):
            # For patterns that could be either, use the recent price action
            is_bullish = price_data.get('close', 0) > price_data.get('open', 0)
            is_bearish = not is_bullish
        
        # Calculate stop loss and take profit
        atr = price_data.get('atr', current_price * 0.001)  # Default to 0.1% if ATR not available
        
        if is_bullish:
            signal_type = f"bullish_{pattern_name}"
            stop_loss = round(current_price - atr * 2, 5)
            take_profit = round(current_price + atr * 4, 5)
            duration = "3-5 days"
        else:  # bearish
            signal_type = f"bearish_{pattern_name}"
            stop_loss = round(current_price + atr * 2, 5)
            take_profit = round(current_price - atr * 4, 5)
            duration = "3-5 days"
        
        # Create signal data
        signal_data = {
            'pair_symbol': pair_symbol,
            'signal_type': signal_type,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': int(confidence),
            'timeframe': 'daily',
            'duration': duration
        }
        
        # Send the signal
        return self.send_trade_signal(signal_data)
    
    def send_filtered_signal(self, signal_data, price_data):
        """
        Send a filtered signal to IFTTT
        
        Args:
            signal_data (dict): Signal data from the signal filter
            price_data (dict): Current price data
                
        Returns:
            dict: Response from IFTTT webhook
        """
        if not self.webhook_key:
            raise ValueError("IFTTT webhook key not set")
        
        # Extract relevant data
        pair_symbol = signal_data.get('symbol')
        pattern_name = signal_data.get('pattern_name', 'unknown')
        confidence = signal_data.get('confirmation', {}).get('confidence', 0)
        
        # Get current price
        current_price = price_data.get('close', 0)
        
        # Determine if pattern is bullish or bearish
        pattern_type = signal_data.get('pattern_type', '')
        
        if 'reversal' in pattern_type.lower():
            # For reversal patterns, check the current trend
            is_bullish = 'bottom' in pattern_name.lower() or 'inverse' in pattern_name.lower()
            is_bearish = not is_bullish
        else:
            # For continuation patterns, use the recent price action
            is_bullish = price_data.get('close', 0) > price_data.get('open', 0)
            is_bearish = not is_bullish
        
        # Calculate stop loss and take profit
        atr = price_data.get('atr', current_price * 0.001)  # Default to 0.1% if ATR not available
        
        if is_bullish:
            signal_type = f"bullish_{pattern_name}"
            stop_loss = round(current_price - atr * 2, 5)
            take_profit = round(current_price + atr * 4, 5)
            duration = "2-4 days"
        else:  # bearish
            signal_type = f"bearish_{pattern_name}"
            stop_loss = round(current_price + atr * 2, 5)
            take_profit = round(current_price - atr * 4, 5)
            duration = "2-4 days"
        
        # Create signal data
        signal_data = {
            'pair_symbol': pair_symbol,
            'signal_type': signal_type,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': int(confidence),
            'timeframe': signal_data.get('timeframe', '1h'),
            'duration': duration
        }
        
        # Send the signal
        return self.send_trade_signal(signal_data)
