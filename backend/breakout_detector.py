import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.signal import argrelextrema
from sklearn.linear_model import LinearRegression

class BreakoutDetector:
    """
    A class to detect breakouts from trend lines and support/resistance levels
    using hourly data frequency
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize the breakout detector
        
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
    
    def get_historical_data(self, pair_symbol, timeframe='1h', limit=200):
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
    
    def identify_swing_points(self, df, window=5):
        """
        Identify swing highs and lows in price data
        
        Args:
            df (pd.DataFrame): Historical price data
            window (int): Window size for detecting local extrema
            
        Returns:
            tuple: DataFrames containing swing highs and swing lows
        """
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Find local maxima (swing highs)
        df['swing_high'] = df.iloc[argrelextrema(df['high'].values, np.greater_equal, order=window)[0]]['high']
        
        # Find local minima (swing lows)
        df['swing_low'] = df.iloc[argrelextrema(df['low'].values, np.less_equal, order=window)[0]]['low']
        
        # Extract swing points
        swing_highs = df[~df['swing_high'].isna()].copy()
        swing_lows = df[~df['swing_low'].isna()].copy()
        
        return swing_highs, swing_lows
    
    def find_trend_lines(self, df, swing_highs, swing_lows, min_points=3, max_distance=0.0015):
        """
        Find trend lines using swing points
        
        Args:
            df (pd.DataFrame): Historical price data
            swing_highs (pd.DataFrame): Swing high points
            swing_lows (pd.DataFrame): Swing low points
            min_points (int): Minimum number of points to form a trend line
            max_distance (float): Maximum distance from point to line (as percentage of price)
            
        Returns:
            dict: Dictionary containing resistance and support trend lines
        """
        if df.empty or swing_highs.empty or swing_lows.empty:
            return {'resistance': [], 'support': []}
        
        # Convert timestamp to numeric for regression
        df['timestamp_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
        swing_highs['timestamp_numeric'] = (swing_highs['timestamp'] - df['timestamp'].min()).dt.total_seconds()
        swing_lows['timestamp_numeric'] = (swing_lows['timestamp'] - df['timestamp'].min()).dt.total_seconds()
        
        # Find resistance trend lines (connecting swing highs)
        resistance_lines = self._find_lines(swing_highs, 'high', min_points, max_distance)
        
        # Find support trend lines (connecting swing lows)
        support_lines = self._find_lines(swing_lows, 'low', min_points, max_distance)
        
        # Calculate current values for each trend line
        latest_timestamp = df['timestamp_numeric'].iloc[-1]
        
        for line in resistance_lines + support_lines:
            # Calculate current value of the trend line
            line['current_value'] = line['slope'] * latest_timestamp + line['intercept']
            
            # Calculate the line values for all timestamps in the dataframe
            line['values'] = [line['slope'] * t + line['intercept'] for t in df['timestamp_numeric']]
            
            # Calculate the timestamps for the line (for plotting)
            line['timestamps'] = df['timestamp'].tolist()
        
        return {
            'resistance': resistance_lines,
            'support': support_lines
        }
    
    def _find_lines(self, swing_points, price_col, min_points, max_distance):
        """
        Helper method to find trend lines from swing points
        
        Args:
            swing_points (pd.DataFrame): Swing points data
            price_col (str): Column name for price data
            min_points (int): Minimum number of points to form a trend line
            max_distance (float): Maximum distance from point to line
            
        Returns:
            list: List of trend lines
        """
        if len(swing_points) < min_points:
            return []
        
        lines = []
        points_used = set()
        
        # Try to find lines starting from each swing point
        for i in range(len(swing_points) - min_points + 1):
            if i in points_used:
                continue
                
            # Start with initial points
            current_points = swing_points.iloc[i:i+min_points].copy()
            
            # Fit linear regression to these points
            X = current_points['timestamp_numeric'].values.reshape(-1, 1)
            y = current_points[price_col].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            slope = model.coef_[0]
            intercept = model.intercept_
            
            # Try to extend the line with more points
            for j in range(i + min_points, len(swing_points)):
                if j in points_used:
                    continue
                    
                # Calculate distance from point to line
                point_x = swing_points.iloc[j]['timestamp_numeric']
                point_y = swing_points.iloc[j][price_col]
                
                # Predicted y value on the line
                pred_y = slope * point_x + intercept
                
                # Calculate distance as percentage of price
                distance = abs(point_y - pred_y) / point_y
                
                if distance <= max_distance:
                    # Add point to the line
                    current_points = pd.concat([current_points, swing_points.iloc[j:j+1]])
                    
                    # Refit the line
                    X = current_points['timestamp_numeric'].values.reshape(-1, 1)
                    y = current_points[price_col].values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    slope = model.coef_[0]
                    intercept = model.intercept_
            
            # If we have enough points, add the line
            if len(current_points) >= min_points:
                # Mark these points as used
                for idx in current_points.index:
                    points_used.add(swing_points.index.get_loc(idx))
                
                # Calculate line strength based on number of points and timespan
                timespan = current_points['timestamp_numeric'].max() - current_points['timestamp_numeric'].min()
                strength = len(current_points) * timespan / 3600  # Normalize by hour
                
                lines.append({
                    'slope': slope,
                    'intercept': intercept,
                    'points': current_points[[price_col, 'timestamp_numeric']].values.tolist(),
                    'strength': strength,
                    'num_points': len(current_points)
                })
        
        # Sort lines by strength (descending)
        lines.sort(key=lambda x: x['strength'], reverse=True)
        
        return lines
    
    def detect_breakouts(self, df, trend_lines, lookback=5, confirmation_candles=2, price_percentage=0.001):
        """
        Detect breakouts from trend lines
        
        Args:
            df (pd.DataFrame): Historical price data
            trend_lines (dict): Dictionary containing resistance and support trend lines
            lookback (int): Number of candles to look back for breakout detection
            confirmation_candles (int): Number of candles needed to confirm a breakout
            price_percentage (float): Minimum price movement as percentage for valid breakout
            
        Returns:
            list: List of detected breakouts
        """
        if df.empty or (not trend_lines['resistance'] and not trend_lines['support']):
            return []
        
        breakouts = []
        
        # Get recent data for breakout detection
        recent_data = df.iloc[-lookback:].copy()
        
        # Check for resistance breakouts (bullish)
        for line in trend_lines['resistance']:
            # Get line values for recent data
            line_values = line['values'][-lookback:]
            
            # Check if price was below the line and then broke above it
            below_line = recent_data['close'].iloc[:-confirmation_candles] < line_values[:-confirmation_candles]
            
            if below_line.any():
                # Find the last candle where price was below the line
                last_below_idx = below_line.values.nonzero()[0][-1] if below_line.any() else -1
                
                # Check if subsequent candles closed above the line
                if last_below_idx >= 0 and last_below_idx < len(recent_data) - confirmation_candles:
                    above_line = recent_data['close'].iloc[last_below_idx+1:] > line_values[last_below_idx+1:]
                    
                    if above_line.all() and len(above_line) >= confirmation_candles:
                        # Calculate breakout percentage
                        breakout_price = recent_data['close'].iloc[last_below_idx+1]
                        line_value = line_values[last_below_idx+1]
                        breakout_percentage = (breakout_price - line_value) / line_value
                        
                        # Check if breakout is significant enough
                        if breakout_percentage >= price_percentage:
                            breakouts.append({
                                'type': 'bullish',
                                'line_type': 'resistance',
                                'timestamp': recent_data['timestamp'].iloc[last_below_idx+1],
                                'price': breakout_price,
                                'line_value': line_value,
                                'percentage': breakout_percentage,
                                'strength': line['strength'],
                                'confirmed': True if len(above_line) >= confirmation_candles else False
                            })
        
        # Check for support breakouts (bearish)
        for line in trend_lines['support']:
            # Get line values for recent data
            line_values = line['values'][-lookback:]
            
            # Check if price was above the line and then broke below it
            above_line = recent_data['close'].iloc[:-confirmation_candles] > line_values[:-confirmation_candles]
            
            if above_line.any():
                # Find the last candle where price was above the line
                last_above_idx = above_line.values.nonzero()[0][-1] if above_line.any() else -1
                
                # Check if subsequent candles closed below the line
                if last_above_idx >= 0 and last_above_idx < len(recent_data) - confirmation_candles:
                    below_line = recent_data['close'].iloc[last_above_idx+1:] < line_values[last_above_idx+1:]
                    
                    if below_line.all() and len(below_line) >= confirmation_candles:
                        # Calculate breakout percentage
                        breakout_price = recent_data['close'].iloc[last_above_idx+1]
                        line_value = line_values[last_above_idx+1]
                        breakout_percentage = (line_value - breakout_price) / line_value
                        
                        # Check if breakout is significant enough
                        if breakout_percentage >= price_percentage:
                            breakouts.append({
                                'type': 'bearish',
                                'line_type': 'support',
                                'timestamp': recent_data['timestamp'].iloc[last_above_idx+1],
                                'price': breakout_price,
                                'line_value': line_value,
                                'percentage': breakout_percentage,
                                'strength': line['strength'],
                                'confirmed': True if len(below_line) >= confirmation_candles else False
                            })
        
        # Sort breakouts by timestamp (most recent first)
        breakouts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return breakouts
    
    def identify_support_resistance_levels(self, df, window=20, threshold=0.0005):
        """
        Identify horizontal support and resistance levels
        
        Args:
            df (pd.DataFrame): Historical price data
            window (int): Window size for price clustering
            threshold (float): Threshold for price level significance
            
        Returns:
            dict: Dictionary containing support and resistance levels
        """
        if df.empty:
            return {'support': [], 'resistance': []}
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Get high and low prices
        highs = df['high'].values
        lows = df['low'].values
        
        # Find price clusters
        high_clusters = self._find_price_clusters(highs, window, threshold)
        low_clusters = self._find_price_clusters(lows, window, threshold)
        
        # Convert to support and resistance levels
        support_levels = []
        resistance_levels = []
        
        for level, strength in low_clusters:
            # Check if this level is already in support levels (within threshold)
            if not any(abs(level - s['level']) / s['level'] < threshold for s in support_levels):
                support_levels.append({
                    'level': level,
                    'strength': strength,
                    'touches': self._count_touches(df, level, 'support', threshold)
                })
        
        for level, strength in high_clusters:
            # Check if this level is already in resistance levels (within threshold)
            if not any(abs(level - r['level']) / r['level'] < threshold for r in resistance_levels):
                resistance_levels.append({
                    'level': level,
                    'strength': strength,
                    'touches': self._count_touches(df, level, 'resistance', threshold)
                })
        
        # Sort levels by strength (descending)
        support_levels.sort(key=lambda x: x['strength'], reverse=True)
        resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    def _find_price_clusters(self, prices, window, threshold):
        """
        Find clusters of prices that could be support or resistance levels
        
        Args:
            prices (np.array): Array of price values
            window (int): Window size for price clustering
            threshold (float): Threshold for price level significance
            
        Returns:
            list: List of (price_level, strength) tuples
        """
        clusters = []
        
        # Use a sliding window to find price clusters
        for i in range(len(prices) - window + 1):
            window_prices = prices[i:i+window]
            
            # Find clusters within the window
            for j in range(window):
                price = window_prices[j]
                
                # Count prices within threshold
                count = sum(1 for p in window_prices if abs(p - price) / price < threshold)
                
                if count >= 3:  # At least 3 prices in the cluster
                    clusters.append((price, count))
        
        # Merge similar clusters
        merged_clusters = {}
        
        for price, count in clusters:
            # Check if this price is close to an existing cluster
            merged = False
            
            for existing_price in list(merged_clusters.keys()):
                if abs(price - existing_price) / existing_price < threshold:
                    # Merge with existing cluster (weighted average)
                    total_count = merged_clusters[existing_price] + count
                    new_price = (existing_price * merged_clusters[existing_price] + price * count) / total_count
                    
                    # Remove old cluster and add new one
                    merged_clusters.pop(existing_price)
                    merged_clusters[new_price] = total_count
                    
                    merged = True
                    break
            
            if not merged:
                merged_clusters[price] = count
        
        # Convert to list of (price, strength) tuples
        return [(price, count) for price, count in merged_clusters.items()]
    
    def _count_touches(self, df, level, level_type, threshold):
        """
        Count how many times price has touched a level
        
        Args:
            df (pd.DataFrame): Historical price data
            level (float): Price level
            level_type (str): 'support' or 'resistance'
            threshold (float): Threshold for touch detection
            
        Returns:
            int: Number of touches
        """
        touches = 0
        
        if level_type == 'support':
            # Count how many times price approached the level from above and bounced
            for i in range(1, len(df)):
                if (df['low'].iloc[i] < level * (1 + threshold) and 
                    df['low'].iloc[i] > level * (1 - threshold) and
                    df['close'].iloc[i] > level):
                    touches += 1
        else:  # resistance
            # Count how many times price approached the level from below and bounced
            for i in range(1, len(df)):
                if (df['high'].iloc[i] > level * (1 - threshold) and 
                    df['high'].iloc[i] < level * (1 + threshold) and
                    df['close'].iloc[i] < level):
                    touches += 1
        
        return touches
    
    def detect_horizontal_breakouts(self, df, levels, lookback=5, confirmation_candles=2, price_percentage=0.001):
        """
        Detect breakouts from horizontal support and resistance levels
        
        Args:
            df (pd.DataFrame): Historical price data
            levels (dict): Dictionary containing support and resistance levels
            lookback (int): Number of candles to look back for breakout detection
            confirmation_candles (int): Number of candles needed to confirm a breakout
            price_percentage (float): Minimum price movement as percentage for valid breakout
            
        Returns:
            list: List of detected breakouts
        """
        if df.empty or (not levels['resistance'] and not levels['support']):
            return []
        
        breakouts = []
        
        # Get recent data for breakout detection
        recent_data = df.iloc[-lookback:].copy()
        
        # Check for resistance breakouts (bullish)
        for level_info in levels['resistance']:
            level = level_info['level']
            
            # Check if price was below the level and then broke above it
            below_level = recent_data['close'].iloc[:-confirmation_candles] < level
            
            if below_level.any():
                # Find the last candle where price was below the level
                last_below_idx = below_level.values.nonzero()[0][-1] if below_level.any() else -1
                
                # Check if subsequent candles closed above the level
                if last_below_idx >= 0 and last_below_idx < len(recent_data) - confirmation_candles:
                    above_level = recent_data['close'].iloc[last_below_idx+1:] > level
                    
                    if above_level.all() and len(above_level) >= confirmation_candles:
                        # Calculate breakout percentage
                        breakout_price = recent_data['close'].iloc[last_below_idx+1]
                        breakout_percentage = (breakout_price - level) / level
                        
                        # Check if breakout is significant enough
                        if breakout_percentage >= price_percentage:
                            breakouts.append({
                                'type': 'bullish',
                                'line_type': 'horizontal_resistance',
                                'timestamp': recent_data['timestamp'].iloc[last_below_idx+1],
                                'price': breakout_price,
                                'level': level,
                                'percentage': breakout_percentage,
                                'strength': level_info['strength'],
                                'touches': level_info['touches'],
                                'confirmed': True if len(above_level) >= confirmation_candles else False
                            })
        
        # Check for support breakouts (bearish)
        for level_info in levels['support']:
            level = level_info['level']
            
            # Check if price was above the level and then broke below it
            above_level = recent_data['close'].iloc[:-confirmation_candles] > level
            
            if above_level.any():
                # Find the last candle where price was above the level
                last_above_idx = above_level.values.nonzero()[0][-1] if above_level.any() else -1
                
                # Check if subsequent candles closed below the level
                if last_above_idx >= 0 and last_above_idx < len(recent_data) - confirmation_candles:
                    below_level = recent_data['close'].iloc[last_above_idx+1:] < level
                    
                    if below_level.all() and len(below_level) >= confirmation_candles:
                        # Calculate breakout percentage
                        breakout_price = recent_data['close'].iloc[last_above_idx+1]
                        breakout_percentage = (level - breakout_price) / level
                        
                        # Check if breakout is significant enough
                        if breakout_percentage >= price_percentage:
                            breakouts.append({
                                'type': 'bearish',
                                'line_type': 'horizontal_support',
                                'timestamp': recent_data['timestamp'].iloc[last_above_idx+1],
                                'price': breakout_price,
                                'level': level,
                                'percentage': breakout_percentage,
                                'strength': level_info['strength'],
                                'touches': level_info['touches'],
                                'confirmed': True if len(below_level) >= confirmation_candles else False
                            })
        
        # Sort breakouts by timestamp (most recent first)
        breakouts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return breakouts
    
    def analyze_pair(self, pair_symbol, timeframe='1h'):
        """
        Perform complete breakout analysis for a currency pair
        
        Args:
            pair_symbol (str): The currency pair symbol
            timeframe (str): The timeframe
            
        Returns:
            dict: Analysis results including trend lines, levels, and breakouts
        """
        # Get historical data
        df = self.get_historical_data(pair_symbol, timeframe=timeframe, limit=200)
        
        if df.empty:
            return {
                'pair_symbol': pair_symbol,
                'timeframe': timeframe,
                'error': 'Insufficient historical data'
            }
        
        # Identify swing points
        swing_highs, swing_lows = self.identify_swing_points(df)
        
        # Find trend lines
        trend_lines = self.find_trend_lines(df, swing_highs, swing_lows)
        
        # Identify support and resistance levels
        levels = self.identify_support_resistance_levels(df)
        
        # Detect breakouts
        trend_breakouts = self.detect_breakouts(df, trend_lines)
        horizontal_breakouts = self.detect_horizontal_breakouts(df, levels)
        
        # Combine all breakouts
        all_breakouts = trend_breakouts + horizontal_breakouts
        all_breakouts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'pair_symbol': pair_symbol,
            'timeframe': timeframe,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trend_lines': trend_lines,
            'support_resistance_levels': levels,
            'breakouts': all_breakouts,
            'latest_price': df['close'].iloc[-1],
            'latest_timestamp': df['timestamp'].iloc[-1]
        }
    
    def save_breakout_to_db(self, breakout, pair_symbol):
        """
        Save a detected breakout to the database
        
        Args:
            breakout (dict): Breakout information
            pair_symbol (str): The currency pair symbol
            
        Returns:
            int: ID of the saved breakout
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
        
        # Check if we need to create the breakouts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS breakouts (
            breakout_id INTEGER PRIMARY KEY,
            pair_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            breakout_type VARCHAR(20) NOT NULL,
            line_type VARCHAR(30) NOT NULL,
            price DECIMAL(10, 5) NOT NULL,
            level_value DECIMAL(10, 5) NOT NULL,
            percentage DECIMAL(10, 5) NOT NULL,
            strength DECIMAL(10, 5) NOT NULL,
            confirmed BOOLEAN NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pair_id) REFERENCES currency_pairs(pair_id)
        )
        """)
        
        # Insert the breakout
        cursor.execute(
            """
            INSERT INTO breakouts 
            (pair_id, timestamp, breakout_type, line_type, price, level_value, percentage, strength, confirmed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pair_id,
                breakout['timestamp'],
                breakout['type'],
                breakout['line_type'],
                breakout['price'],
                breakout.get('level', breakout.get('line_value')),
                breakout['percentage'],
                breakout['strength'],
                breakout['confirmed'],
                'active'
            )
        )
        
        self.db_connection.commit()
        
        # Get the ID of the inserted breakout
        breakout_id = cursor.lastrowid
        
        return breakout_id
