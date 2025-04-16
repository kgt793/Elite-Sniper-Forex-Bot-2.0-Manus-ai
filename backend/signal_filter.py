import os
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class SignalFilter:
    """
    A class to filter trading signals and reduce noise using various confirmation techniques
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize the signal filter
        
        Args:
            db_connection: SQLite database connection (optional)
        """
        self.db_connection = db_connection
    
    def set_db_connection(self, db_connection):
        """
        Set the database connection
        
        Args:
            db_connection: SQLite database connection
        """
        self.db_connection = db_connection
    
    def get_historical_data(self, pair_symbol, timeframe='1h', limit=100):
        """
        Get historical data for a currency pair from the database
        
        Args:
            pair_symbol (str): The currency pair symbol
            timeframe (str): The timeframe
            limit (int): The number of candles to return
            
        Returns:
            pd.DataFrame: Historical data as a pandas DataFrame
        """
        if not self.db_connection:
            raise ValueError("Database connection not set")
        
        cursor = self.db_connection.cursor()
        
        # Get pair_id
        cursor.execute("SELECT pair_id FROM currency_pairs WHERE symbol = ?", (pair_symbol,))
        pair_row = cursor.fetchone()
        
        if not pair_row:
            raise ValueError(f"Currency pair {pair_symbol} not found")
        
        pair_id = pair_row[0]
        
        # Get historical data
        cursor.execute(
            """
            SELECT timestamp, open_price, high_price, low_price, close_price, volume
            FROM historical_data
            WHERE pair_id = ? AND timeframe = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (pair_id, timeframe, limit)
        )
        
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for confirmation
        
        Args:
            df (pd.DataFrame): Historical data
            
        Returns:
            pd.DataFrame: DataFrame with indicators
        """
        if df.empty:
            return df
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Calculate moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Calculate RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD (Moving Average Convergence Divergence)
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Calculate Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        # Calculate ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        return df
    
    def confirm_pattern(self, pattern_detection, confidence_threshold=70):
        """
        Confirm a chart pattern using multiple indicators
        
        Args:
            pattern_detection (dict): Pattern detection data
            confidence_threshold (float): Minimum confidence threshold
            
        Returns:
            dict: Confirmation results with confidence score and reasons
        """
        if not self.db_connection:
            raise ValueError("Database connection not set")
        
        cursor = self.db_connection.cursor()
        
        # Get pattern and pair information
        cursor.execute(
            """
            SELECT cp.symbol, cp.pair_type, p.name as pattern_name, p.type as pattern_type
            FROM pattern_detections pd
            JOIN currency_pairs cp ON pd.pair_id = cp.pair_id
            JOIN chart_patterns p ON pd.pattern_id = p.pattern_id
            WHERE pd.detection_id = ?
            """,
            (pattern_detection['detection_id'],)
        )
        
        info = cursor.fetchone()
        
        if not info:
            return {
                'confirmed': False,
                'confidence': 0,
                'reasons': ['Pattern detection not found']
            }
        
        pair_symbol = info[0]
        pattern_name = info[2]
        pattern_type = info[3]
        
        # Get historical data
        df = self.get_historical_data(pair_symbol, timeframe='1h', limit=100)
        
        if df.empty:
            return {
                'confirmed': False,
                'confidence': 0,
                'reasons': ['Insufficient historical data']
            }
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Initialize confirmation variables
        confirmed = False
        confidence = pattern_detection['confidence_score']
        reasons = []
        
        # Check trend confirmation based on pattern type
        if pattern_type == 'continuation':
            # For continuation patterns, check if the trend is still intact
            if latest['sma_20'] > latest['sma_50'] and latest['close'] > latest['sma_20']:
                confidence += 10
                reasons.append('Uptrend confirmed by moving averages')
            elif latest['sma_20'] < latest['sma_50'] and latest['close'] < latest['sma_20']:
                confidence += 10
                reasons.append('Downtrend confirmed by moving averages')
            else:
                confidence -= 10
                reasons.append('Trend not confirmed by moving averages')
        
        elif pattern_type == 'reversal':
            # For reversal patterns, check for trend exhaustion
            if pattern_name.lower().find('top') >= 0:
                # Bearish reversal
                if latest['rsi'] > 70:
                    confidence += 10
                    reasons.append('Overbought conditions confirmed by RSI')
                if latest['close'] > latest['bb_upper']:
                    confidence += 10
                    reasons.append('Price above upper Bollinger Band')
                if latest['macd_hist'] < 0 and latest['macd'] < 0:
                    confidence += 10
                    reasons.append('Bearish momentum confirmed by MACD')
            
            elif pattern_name.lower().find('bottom') >= 0 or pattern_name.lower().find('inverse') >= 0:
                # Bullish reversal
                if latest['rsi'] < 30:
                    confidence += 10
                    reasons.append('Oversold conditions confirmed by RSI')
                if latest['close'] < latest['bb_lower']:
                    confidence += 10
                    reasons.append('Price below lower Bollinger Band')
                if latest['macd_hist'] > 0 and latest['macd'] > 0:
                    confidence += 10
                    reasons.append('Bullish momentum confirmed by MACD')
        
        # Volume confirmation
        recent_volume = df['volume'].iloc[-5:].mean()
        previous_volume = df['volume'].iloc[-10:-5].mean()
        
        if recent_volume > previous_volume * 1.2:
            confidence += 10
            reasons.append('Increasing volume confirms pattern')
        else:
            confidence -= 5
            reasons.append('Volume not confirming pattern')
        
        # Check for false breakouts
        if 'price_at_detection' in pattern_detection and 'target_price' in pattern_detection:
            price_at_detection = pattern_detection['price_at_detection']
            target_price = pattern_detection['target_price']
            
            # If price moved in expected direction but then reversed
            if (target_price > price_at_detection and 
                max(df['high'].iloc[-5:]) > price_at_detection and 
                latest['close'] < price_at_detection):
                confidence -= 20
                reasons.append('Possible false breakout detected')
            
            elif (target_price < price_at_detection and 
                  min(df['low'].iloc[-5:]) < price_at_detection and 
                  latest['close'] > price_at_detection):
                confidence -= 20
                reasons.append('Possible false breakout detected')
        
        # Final confirmation
        confirmed = confidence >= confidence_threshold
        
        return {
            'confirmed': confirmed,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def filter_signals(self, min_confidence=75):
        """
        Filter all active pattern detections and return only confirmed signals
        
        Args:
            min_confidence (float): Minimum confidence threshold
            
        Returns:
            list: List of confirmed signals
        """
        if not self.db_connection:
            raise ValueError("Database connection not set")
        
        cursor = self.db_connection.cursor()
        
        # Get all active pattern detections
        cursor.execute(
            """
            SELECT pd.*, cp.symbol, p.name as pattern_name, p.type as pattern_type
            FROM pattern_detections pd
            JOIN currency_pairs cp ON pd.pair_id = cp.pair_id
            JOIN chart_patterns p ON pd.pattern_id = p.pattern_id
            WHERE pd.status = 'active'
            """
        )
        
        detections = [dict(zip([column[0] for column in cursor.description], row)) 
                     for row in cursor.fetchall()]
        
        confirmed_signals = []
        
        for detection in detections:
            confirmation = self.confirm_pattern(detection, confidence_threshold=min_confidence)
            
            if confirmation['confirmed']:
                # Add confirmation details to the detection
                detection['confirmation'] = confirmation
                confirmed_signals.append(detection)
        
        return confirmed_signals
    
    def get_multi_timeframe_confirmation(self, pair_symbol, pattern_detection):
        """
        Check if a pattern is confirmed across multiple timeframes
        
        Args:
            pair_symbol (str): The currency pair symbol
            pattern_detection (dict): Pattern detection data
            
        Returns:
            dict: Multi-timeframe confirmation results
        """
        timeframes = ['1h', '4h', '1d']
        confirmations = {}
        
        for tf in timeframes:
            df = self.get_historical_data(pair_symbol, timeframe=tf, limit=100)
            
            if not df.empty:
                df = self.calculate_indicators(df)
                latest = df.iloc[-1]
                
                # Check trend direction
                trend = 'neutral'
                if latest['sma_20'] > latest['sma_50'] and latest['close'] > latest['sma_20']:
                    trend = 'bullish'
                elif latest['sma_20'] < latest['sma_50'] and latest['close'] < latest['sma_20']:
                    trend = 'bearish'
                
                # Check momentum
                momentum = 'neutral'
                if latest['macd'] > 0 and latest['macd_hist'] > 0:
                    momentum = 'bullish'
                elif latest['macd'] < 0 and latest['macd_hist'] < 0:
                    momentum = 'bearish'
                
                # Check volatility
                volatility = 'normal'
                if latest['atr'] > df['atr'].mean() * 1.5:
                    volatility = 'high'
                elif latest['atr'] < df['atr'].mean() * 0.5:
                    volatility = 'low'
                
                confirmations[tf] = {
                    'trend': trend,
                    'momentum': momentum,
                    'volatility': volatility
                }
        
        # Check for alignment across timeframes
        aligned = False
        if len(confirmations) >= 2:
            # Check if at least 2 timeframes have the same trend direction
            trends = [conf['trend'] for conf in confirmations.values()]
            if trends.count('bullish') >= 2 or trends.count('bearish') >= 2:
                aligned = True
        
        return {
            'timeframes': confirmations,
            'aligned': aligned
        }
    
    def update_pattern_detection_status(self, detection_id, status, notes=None):
        """
        Update the status of a pattern detection
        
        Args:
            detection_id (int): The detection ID
            status (str): The new status ('active', 'confirmed', 'invalidated', 'completed')
            notes (str): Optional notes
            
        Returns:
            bool: Success status
        """
        if not self.db_connection:
            raise ValueError("Database connection not set")
        
        cursor = self.db_connection.cursor()
        
        try:
            if notes:
                cursor.execute(
                    "UPDATE pattern_detections SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE detection_id = ?",
                    (status, notes, detection_id)
                )
            else:
                cursor.execute(
                    "UPDATE pattern_detections SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE detection_id = ?",
                    (status, detection_id)
                )
            
            self.db_connection.commit()
            return True
        
        except Exception as e:
            print(f"Error updating pattern detection status: {str(e)}")
            return False
