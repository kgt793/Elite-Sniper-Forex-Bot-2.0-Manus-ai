import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
import requests

# Set TensorFlow logging level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Import TensorFlow configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tensorflow_config import tensorflow_version

# Import custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from exchange_rates_api import ExchangeRatesAPI
from signal_filter import SignalFilter
from breakout_detector import BreakoutDetector
from pattern_verifier import PatternVerifier
# Add the backend directory to the path to import the risk calculator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from risk_calculator import RiskManagementCalculator
# Import Telegram bot integration
from telegram_bot import TelegramBotIntegration

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'forex_bot.db')
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'flask.log')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7895580284:AAGTKQSDJzst5Ri7ZMeQcQiGQOFbt9_sNzo')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://your-render-url.onrender.com')

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Log TensorFlow version
print(f"TensorFlow version: {tensorflow_version}")

# Database initialization
def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create currency pairs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS currency_pairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        name TEXT,
        type TEXT,
        pip_value REAL,
        spread REAL,
        trading_hours TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create chart patterns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chart_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        bullish BOOLEAN,
        reliability INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create account table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        balance REAL,
        previous_balance REAL,
        risk_percentage REAL,
        drawdown_percentage REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create trades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair_id INTEGER,
        pattern_id INTEGER,
        entry_price REAL,
        stop_loss REAL,
        take_profit REAL,
        position_size REAL,
        risk_amount REAL,
        profit_loss REAL,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP,
        FOREIGN KEY (pair_id) REFERENCES currency_pairs (id),
        FOREIGN KEY (pattern_id) REFERENCES chart_patterns (id)
    )
    ''')
    
    # Insert default account if not exists
    cursor.execute("SELECT COUNT(*) FROM account")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO account (balance, previous_balance, risk_percentage, drawdown_percentage) VALUES (?, ?, ?, ?)", 
                      (5000.0, 5000.0, 0.2, 8.0))
    
    # Insert some default currency pairs if not exists
    cursor.execute("SELECT COUNT(*) FROM currency_pairs")
    if cursor.fetchone()[0] == 0:
        pairs = [
            ('EUR/USD', 'Euro / US Dollar', 'major', 0.0001, 1.0, '24/7'),
            ('GBP/USD', 'British Pound / US Dollar', 'major', 0.0001, 1.2, '24/7'),
            ('USD/JPY', 'US Dollar / Japanese Yen', 'major', 0.01, 1.0, '24/7'),
            ('AUD/USD', 'Australian Dollar / US Dollar', 'major', 0.0001, 1.4, '24/7'),
            ('USD/CAD', 'US Dollar / Canadian Dollar', 'major', 0.0001, 1.3, '24/7'),
            ('USD/CHF', 'US Dollar / Swiss Franc', 'major', 0.0001, 1.2, '24/7'),
            ('NZD/USD', 'New Zealand Dollar / US Dollar', 'major', 0.0001, 1.5, '24/7')
        ]
        cursor.executemany("INSERT OR IGNORE INTO currency_pairs (symbol, name, type, pip_value, spread, trading_hours) VALUES (?, ?, ?, ?, ?, ?)", pairs)
    
    # Insert some default chart patterns if not exists
    cursor.execute("SELECT COUNT(*) FROM chart_patterns")
    if cursor.fetchone()[0] == 0:
        patterns = [
            ('Head and Shoulders', 'A reversal pattern with a peak (head) and two lower peaks (shoulders)', 0, 80),
            ('Double Top', 'A reversal pattern with two peaks at approximately the same level', 0, 75),
            ('Double Bottom', 'A reversal pattern with two troughs at approximately the same level', 1, 75),
            ('Triangle', 'A continuation pattern where price consolidates into a triangle shape', 2, 65),
            ('Flag', 'A continuation pattern that appears as a parallelogram against the trend', 2, 70),
            ('Pennant', 'A continuation pattern similar to a triangle but smaller in size and duration', 2, 68),
            ('Cup and Handle', 'A bullish continuation pattern resembling a cup with a handle', 1, 72)
        ]
        cursor.executemany("INSERT OR IGNORE INTO chart_patterns (name, description, bullish, reliability) VALUES (?, ?, ?, ?)", patterns)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Serve static files
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)

# API endpoints
@app.route('/api/account', methods=['GET'])
def get_account():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT balance, previous_balance, risk_percentage, drawdown_percentage, updated_at FROM account ORDER BY id DESC LIMIT 1")
        account = cursor.fetchone()
        
        if account:
            return jsonify({
                'balance': account[0],
                'previous_balance': account[1],
                'risk_percentage': account[2],
                'drawdown_percentage': account[3],
                'updated_at': account[4]
            })
        else:
            return jsonify({'error': 'No account data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/account', methods=['POST'])
def update_account():
    data = request.json
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get current balance to store as previous_balance
        cursor.execute("SELECT balance FROM account ORDER BY id DESC LIMIT 1")
        current = cursor.fetchone()
        previous_balance = current[0] if current else 5000.0
        
        # Insert new account record
        cursor.execute(
            "INSERT INTO account (balance, previous_balance, risk_percentage, drawdown_percentage) VALUES (?, ?, ?, ?)",
            (
                data.get('balance', 5000.0),
                previous_balance,
                data.get('risk_percentage', 0.2),
                data.get('drawdown_percentage', 8.0)
            )
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Account updated successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pairs', methods=['GET'])
def get_pairs():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM currency_pairs ORDER BY symbol")
        pairs = [dict(row) for row in cursor.fetchall()]
        return jsonify(pairs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM chart_patterns ORDER BY name")
        patterns = [dict(row) for row in cursor.fetchall()]
        return jsonify(patterns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/trades', methods=['GET'])
def get_trades():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT t.*, cp.symbol as pair_symbol, chp.name as pattern_name 
            FROM trades t
            LEFT JOIN currency_pairs cp ON t.pair_id = cp.id
            LEFT JOIN chart_patterns chp ON t.pattern_id = chp.id
            ORDER BY t.created_at DESC
        """)
        trades = [dict(row) for row in cursor.fetchall()]
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/trades', methods=['POST'])
def create_trade():
    data = request.json
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO trades 
               (pair_id, pattern_id, entry_price, stop_loss, take_profit, position_size, risk_amount, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get('pair_id'),
                data.get('pattern_id'),
                data.get('entry_price'),
                data.get('stop_loss'),
                data.get('take_profit'),
                data.get('position_size'),
                data.get('risk_amount'),
                data.get('status', 'open')
            )
        )
        trade_id = cursor.lastrowid
        conn.commit()
        return jsonify({'success': True, 'id': trade_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/system_status', methods=['GET'])
def system_status():
    """Return system status including TensorFlow version"""
    return jsonify({
        "status": "online",
        "tensorflow_version": tensorflow_version,
        "database_connected": True,
        "version": "2.0.1",
        "environment": os.environ.get('FLASK_ENV', 'production')
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
