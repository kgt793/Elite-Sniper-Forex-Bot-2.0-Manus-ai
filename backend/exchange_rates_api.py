import os
import requests
import json
from datetime import datetime, timedelta

class ExchangeRatesAPI:
    """
    A class to interact with the exchangeratesapi.io API for live forex data
    """
    
    def __init__(self, api_key):
        """
        Initialize the API client with the provided API key
        
        Args:
            api_key (str): The API key for exchangeratesapi.io
        """
        self.api_key = api_key
        self.base_url = "http://api.exchangeratesapi.io/v1/"
        
    def get_latest_rates(self, base_currency="EUR", symbols=None):
        """
        Get the latest exchange rates
        
        Args:
            base_currency (str): The base currency (default: EUR)
            symbols (list): List of currency symbols to get rates for
            
        Returns:
            dict: The latest exchange rates
        """
        endpoint = "latest"
        params = {
            "access_key": self.api_key,
            "base": base_currency
        }
        
        if symbols:
            params["symbols"] = ",".join(symbols)
            
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching latest rates: {response.status_code} - {response.text}")
    
    def get_historical_rates(self, date, base_currency="EUR", symbols=None):
        """
        Get historical exchange rates for a specific date
        
        Args:
            date (str): Date in YYYY-MM-DD format
            base_currency (str): The base currency (default: EUR)
            symbols (list): List of currency symbols to get rates for
            
        Returns:
            dict: The historical exchange rates
        """
        endpoint = date
        params = {
            "access_key": self.api_key,
            "base": base_currency
        }
        
        if symbols:
            params["symbols"] = ",".join(symbols)
            
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching historical rates: {response.status_code} - {response.text}")
    
    def get_time_series(self, start_date, end_date, base_currency="EUR", symbols=None):
        """
        Get exchange rates for a time period
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            base_currency (str): The base currency (default: EUR)
            symbols (list): List of currency symbols to get rates for
            
        Returns:
            dict: The time series exchange rates
        """
        endpoint = "timeseries"
        params = {
            "access_key": self.api_key,
            "start_date": start_date,
            "end_date": end_date,
            "base": base_currency
        }
        
        if symbols:
            params["symbols"] = ",".join(symbols)
            
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching time series: {response.status_code} - {response.text}")
    
    def convert_currency(self, from_currency, to_currency, amount):
        """
        Convert an amount from one currency to another
        
        Args:
            from_currency (str): The source currency
            to_currency (str): The target currency
            amount (float): The amount to convert
            
        Returns:
            dict: The conversion result
        """
        endpoint = "convert"
        params = {
            "access_key": self.api_key,
            "from": from_currency,
            "to": to_currency,
            "amount": amount
        }
        
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error converting currency: {response.status_code} - {response.text}")
    
    def get_ohlc_data(self, symbol, timeframe="1h", limit=100):
        """
        Get OHLC (Open, High, Low, Close) data for a currency pair
        
        Note: This is a simulated method as exchangeratesapi.io doesn't provide OHLC data directly.
        We'll use time series data to approximate OHLC.
        
        Args:
            symbol (str): The currency pair (e.g., "EUR/USD")
            timeframe (str): The timeframe (e.g., "1h", "4h", "1d")
            limit (int): The number of candles to return
            
        Returns:
            list: List of OHLC candles
        """
        # Parse the symbol to get base and quote currencies
        base_currency, quote_currency = symbol.split('/')
        
        # Calculate date range based on timeframe and limit
        end_date = datetime.now()
        
        if timeframe == "1h":
            start_date = end_date - timedelta(hours=limit)
            interval_hours = 1
        elif timeframe == "4h":
            start_date = end_date - timedelta(hours=limit * 4)
            interval_hours = 4
        elif timeframe == "1d":
            start_date = end_date - timedelta(days=limit)
            interval_hours = 24
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Format dates for API
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Get time series data
        time_series = self.get_time_series(
            start_date_str, 
            end_date_str, 
            base_currency=base_currency, 
            symbols=[quote_currency]
        )
        
        # Process time series data into OHLC format
        # Note: This is an approximation since we only have daily rates
        ohlc_data = []
        
        # Sort dates
        dates = sorted(time_series.get('rates', {}).keys())
        
        for i, date in enumerate(dates):
            rate = time_series['rates'][date].get(quote_currency)
            
            # For simplicity, we'll use the same rate for O, H, L, C
            # In a real implementation, you would need intraday data
            candle = {
                'timestamp': date,
                'open': rate,
                'high': rate * 1.001,  # Simulate a slightly higher high
                'low': rate * 0.999,   # Simulate a slightly lower low
                'close': rate,
                'volume': 0            # Volume not available
            }
            
            ohlc_data.append(candle)
        
        return ohlc_data
    
    def update_forex_database(self, db_connection, pairs=None):
        """
        Update the forex database with the latest rates
        
        Args:
            db_connection: SQLite database connection
            pairs (list): List of currency pairs to update
            
        Returns:
            int: Number of pairs updated
        """
        cursor = db_connection.cursor()
        
        # If no pairs specified, get all active pairs from the database
        if not pairs:
            cursor.execute("SELECT symbol, base_currency, quote_currency FROM currency_pairs WHERE is_active = 1")
            pairs = cursor.fetchall()
        
        updated_count = 0
        
        for pair in pairs:
            if isinstance(pair, tuple):
                symbol, base_currency, quote_currency = pair
            else:
                # Parse the symbol to get base and quote currencies
                symbol = pair
                base_currency, quote_currency = symbol.split('/')
            
            try:
                # Get the latest rate for this pair
                latest_rates = self.get_latest_rates(base_currency=base_currency, symbols=[quote_currency])
                
                if latest_rates.get('success', False):
                    rate = latest_rates['rates'].get(quote_currency)
                    
                    if rate:
                        # Get pair_id
                        cursor.execute("SELECT pair_id FROM currency_pairs WHERE symbol = ?", (symbol,))
                        pair_row = cursor.fetchone()
                        
                        if pair_row:
                            pair_id = pair_row[0]
                            
                            # Insert into historical_data
                            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            cursor.execute(
                                """
                                INSERT INTO historical_data 
                                (pair_id, timeframe, timestamp, open_price, high_price, low_price, close_price, volume) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (pair_id, '1h', now, rate, rate, rate, rate, 0)
                            )
                            
                            updated_count += 1
            
            except Exception as e:
                print(f"Error updating {symbol}: {str(e)}")
                continue
        
        # Commit the changes
        db_connection.commit()
        
        return updated_count
