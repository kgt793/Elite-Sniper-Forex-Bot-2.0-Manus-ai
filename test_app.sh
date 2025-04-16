#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p /home/ubuntu/forex_trading_bot/data
mkdir -p /home/ubuntu/forex_trading_bot/logs

# Install required Python packages
echo "Installing required Python packages..."
pip3 install flask python-telegram-bot requests

# Run tests for risk management calculator
echo "Testing risk management calculator..."
cd /home/ubuntu/forex_trading_bot/backend
python3 -c "
from risk_calculator import RiskManagementCalculator

# Test initialization
calculator = RiskManagementCalculator(5000, 0.2, 8)
metrics = calculator.get_risk_metrics()
print('Initial metrics:', metrics)
assert metrics['balance'] == 5000, 'Initial balance should be 5000'
assert metrics['risk_percentage'] == 0.2, 'Risk percentage should be 0.2'
assert metrics['drawdown_percentage'] == 8, 'Drawdown percentage should be 8'
assert metrics['max_drawdown_amount'] == 400, 'Max drawdown should be 400'

# Test position size calculation
position_info = calculator.calculate_position_size(1.2000, 1.1950)
print('Position info:', position_info)
assert position_info['risk_amount'] == 10.0, 'Risk amount should be 10.0'
assert position_info['stop_loss_pips'] == 50.0, 'Stop loss pips should be 50.0'

# Test trade simulation
trade_result = calculator.simulate_trade_outcome(
    entry_price=1.2000,
    position_size=position_info['position_size'],
    stop_loss_price=1.1950,
    take_profit_price=1.2100
)
print('Trade result:', trade_result)

# Test new trading day
max_drawdown = calculator.new_trading_day()
print('New trading day max drawdown:', max_drawdown)

print('Risk management calculator tests passed!')
"

# Test database initialization
echo "Testing database initialization..."
cd /home/ubuntu/forex_trading_bot/backend
python3 -c "
import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath('.')), 'data', 'forex_bot.db')
print(f'Database path: {DATABASE_PATH}')

# Create database directory if it doesn't exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Initialize database
from app import init_db
init_db()

# Verify tables were created
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Check if tables exist
tables = cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\").fetchall()
table_names = [table[0] for table in tables]
print('Tables created:', table_names)

required_tables = [
    'currency_pairs', 
    'chart_patterns', 
    'pattern_detections', 
    'account', 
    'trades', 
    'historical_data', 
    'user_settings'
]

for table in required_tables:
    assert table in table_names, f'Table {table} should exist in database'

# Check if initial data was inserted
currency_pairs_count = cursor.execute('SELECT COUNT(*) FROM currency_pairs').fetchone()[0]
chart_patterns_count = cursor.execute('SELECT COUNT(*) FROM chart_patterns').fetchone()[0]
account_count = cursor.execute('SELECT COUNT(*) FROM account').fetchone()[0]

print(f'Currency pairs count: {currency_pairs_count}')
print(f'Chart patterns count: {chart_patterns_count}')
print(f'Account count: {account_count}')

assert currency_pairs_count > 0, 'Currency pairs table should have data'
assert chart_patterns_count > 0, 'Chart patterns table should have data'
assert account_count > 0, 'Account table should have data'

# Check account settings
account = cursor.execute('SELECT * FROM account').fetchone()
print(f'Account settings: {account}')
assert account[1] == 5000.00, 'Account balance should be 5000.00'
assert account[5] == 0.2, 'Risk percentage should be 0.2'
assert account[6] == 8.0, 'Drawdown percentage should be 8.0'

conn.close()
print('Database initialization tests passed!')
"

# Test Flask API endpoints
echo "Testing Flask API endpoints..."
cd /home/ubuntu/forex_trading_bot/backend

# Start Flask server in background
python3 -c "
import subprocess
import time
import requests
import json
import sys

# Start Flask server in background
print('Starting Flask server...')
server_process = subprocess.Popen(['python3', 'app.py'], 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

# Wait for server to start
time.sleep(5)

# Test API endpoints
try:
    # Test currency pairs endpoint
    print('Testing /api/currency-pairs endpoint...')
    response = requests.get('http://localhost:5000/api/currency-pairs')
    assert response.status_code == 200, 'Currency pairs endpoint should return 200'
    pairs = response.json()
    assert len(pairs) > 0, 'Currency pairs endpoint should return data'
    print(f'Found {len(pairs)} currency pairs')
    
    # Test chart patterns endpoint
    print('Testing /api/chart-patterns endpoint...')
    response = requests.get('http://localhost:5000/api/chart-patterns')
    assert response.status_code == 200, 'Chart patterns endpoint should return 200'
    patterns = response.json()
    assert len(patterns) > 0, 'Chart patterns endpoint should return data'
    print(f'Found {len(patterns)} chart patterns')
    
    # Test account endpoint
    print('Testing /api/account endpoint...')
    response = requests.get('http://localhost:5000/api/account')
    assert response.status_code == 200, 'Account endpoint should return 200'
    account = response.json()
    assert account['balance'] == 5000.00, 'Account balance should be 5000.00'
    assert account['risk_percentage'] == 0.2, 'Risk percentage should be 0.2'
    assert account['drawdown_percentage'] == 8.0, 'Drawdown percentage should be 8.0'
    print('Account settings verified')
    
    # Test calculate position endpoint
    print('Testing /api/calculate-position endpoint...')
    data = {
        'entry_price': 1.2000,
        'stop_loss_price': 1.1950,
        'pair_symbol': 'EUR/USD'
    }
    response = requests.post('http://localhost:5000/api/calculate-position', json=data)
    assert response.status_code == 200, 'Calculate position endpoint should return 200'
    position = response.json()
    assert position['risk_amount'] == 10.0, 'Risk amount should be 10.0'
    print('Position calculation verified')
    
    # Test user settings endpoint
    print('Testing /api/user-settings endpoint...')
    response = requests.get('http://localhost:5000/api/user-settings')
    assert response.status_code == 200, 'User settings endpoint should return 200'
    settings = response.json()
    assert 'notification_preferences' in settings, 'Settings should include notification preferences'
    print('User settings verified')
    
    print('All API tests passed!')
    
except Exception as e:
    print(f'Error testing API: {str(e)}')
    sys.exit(1)
finally:
    # Kill Flask server
    server_process.terminate()
    print('Flask server terminated')
"

# Test Telegram bot functionality (mock test since we can't actually run the bot without a token)
echo "Testing Telegram bot functionality..."
cd /home/ubuntu/forex_trading_bot/backend
python3 -c "
import sys
from telegram_bot import get_currency_pairs, get_chart_patterns, get_account_info, calculate_position_size

try:
    # Test helper functions
    print('Testing Telegram bot helper functions...')
    
    # Test get_currency_pairs
    pairs = get_currency_pairs()
    assert len(pairs) > 0, 'get_currency_pairs should return data'
    print(f'Found {len(pairs)} currency pairs')
    
    # Test get_chart_patterns
    patterns = get_chart_patterns()
    assert len(patterns) > 0, 'get_chart_patterns should return data'
    print(f'Found {len(patterns)} chart patterns')
    
    # Test get_account_info
    account = get_account_info()
    assert account['balance'] == 5000.00, 'Account balance should be 5000.00'
    assert account['risk_percentage'] == 0.2, 'Risk percentage should be 0.2'
    assert account['drawdown_percentage'] == 8.0, 'Drawdown percentage should be 8.0'
    print('Account settings verified')
    
    # Test calculate_position_size
    position_info = calculate_position_size(1.2000, 1.1950, 'EUR/USD')
    assert position_info['risk_amount'] == 10.0, 'Risk amount should be 10.0'
    print('Position calculation verified')
    
    print('All Telegram bot helper function tests passed!')
    
except Exception as e:
    print(f'Error testing Telegram bot: {str(e)}')
    sys.exit(1)
"

# Test frontend (basic check that files exist)
echo "Testing frontend files..."
if [ -f "/home/ubuntu/forex_trading_bot/frontend/index.html" ]; then
    echo "Frontend index.html exists"
else
    echo "ERROR: Frontend index.html not found"
    exit 1
fi

echo "All tests completed successfully!"
