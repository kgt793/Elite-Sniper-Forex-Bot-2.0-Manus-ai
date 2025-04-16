import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
import requests

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create chart patterns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chart_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        description TEXT,
        reliability REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create pattern detections table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pattern_detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair_id INTEGER,
        pattern_id INTEGER,
        timeframe TEXT,
        entry_price REAL,
        stop_loss REAL,
        take_profit REAL,
        confidence REAL,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pair_id) REFERENCES currency_pairs (id),
        FOREIGN KEY (pattern_id) REFERENCES chart_patterns (id)
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
        status TEXT,
        profit_loss REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP,
        FOREIGN KEY (pair_id) REFERENCES currency_pairs (id),
        FOREIGN KEY (pattern_id) REFERENCES chart_patterns (id)
    )
    ''')
    
    # Create historical data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historical_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair_id INTEGER,
        timeframe TEXT,
        open_price REAL,
        high_price REAL,
        low_price REAL,
        close_price REAL,
        volume REAL,
        timestamp TIMESTAMP,
        FOREIGN KEY (pair_id) REFERENCES currency_pairs (id)
    )
    ''')
    
    # Create breakouts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS breakouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair_id INTEGER,
        type TEXT,
        price REAL,
        strength REAL,
        confirmed BOOLEAN,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pair_id) REFERENCES currency_pairs (id)
    )
    ''')
    
    # Create settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert default settings if they don't exist
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                  ("telegram_bot_token", TELEGRAM_BOT_TOKEN))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                  ("webapp_url", WEBAPP_URL))
    
    # Insert default account if it doesn't exist
    cursor.execute("INSERT OR IGNORE INTO account (balance, previous_balance, risk_percentage, drawdown_percentage) VALUES (?, ?, ?, ?)", 
                  (5000, 5000, 0.2, 8))
    
    # Insert major currency pairs if they don't exist
    major_pairs = [
        ("EUR/USD", "Euro / US Dollar", "major", 0.0001),
        ("USD/JPY", "US Dollar / Japanese Yen", "major", 0.01),
        ("GBP/USD", "British Pound / US Dollar", "major", 0.0001),
        ("USD/CHF", "US Dollar / Swiss Franc", "major", 0.0001),
        ("AUD/USD", "Australian Dollar / US Dollar", "major", 0.0001),
        ("USD/CAD", "US Dollar / Canadian Dollar", "major", 0.0001),
        ("NZD/USD", "New Zealand Dollar / US Dollar", "major", 0.0001)
    ]
    
    for pair in major_pairs:
        cursor.execute("INSERT OR IGNORE INTO currency_pairs (symbol, name, type, pip_value) VALUES (?, ?, ?, ?)", pair)
    
    # Insert cross currency pairs if they don't exist
    cross_pairs = [
        ("EUR/GBP", "Euro / British Pound", "cross", 0.0001),
        ("EUR/JPY", "Euro / Japanese Yen", "cross", 0.01),
        ("GBP/JPY", "British Pound / Japanese Yen", "cross", 0.01),
        ("AUD/JPY", "Australian Dollar / Japanese Yen", "cross", 0.01),
        ("EUR/AUD", "Euro / Australian Dollar", "cross", 0.0001)
    ]
    
    for pair in cross_pairs:
        cursor.execute("INSERT OR IGNORE INTO currency_pairs (symbol, name, type, pip_value) VALUES (?, ?, ?, ?)", pair)
    
    # Insert exotic currency pairs if they don't exist
    exotic_pairs = [
        ("USD/SGD", "US Dollar / Singapore Dollar", "exotic", 0.0001),
        ("USD/HKD", "US Dollar / Hong Kong Dollar", "exotic", 0.0001),
        ("USD/TRY", "US Dollar / Turkish Lira", "exotic", 0.0001),
        ("USD/MXN", "US Dollar / Mexican Peso", "exotic", 0.0001)
    ]
    
    for pair in exotic_pairs:
        cursor.execute("INSERT OR IGNORE INTO currency_pairs (symbol, name, type, pip_value) VALUES (?, ?, ?, ?)", pair)
    
    # Insert chart patterns if they don't exist
    patterns = [
        ("Head and Shoulders", "reversal", "Bearish reversal pattern", 0.75),
        ("Inverse Head and Shoulders", "reversal", "Bullish reversal pattern", 0.75),
        ("Double Top", "reversal", "Bearish reversal pattern", 0.8),
        ("Double Bottom", "reversal", "Bullish reversal pattern", 0.8),
        ("Triple Top", "reversal", "Bearish reversal pattern", 0.85),
        ("Triple Bottom", "reversal", "Bullish reversal pattern", 0.85),
        ("Ascending Triangle", "continuation", "Bullish continuation pattern", 0.7),
        ("Descending Triangle", "continuation", "Bearish continuation pattern", 0.7),
        ("Symmetrical Triangle", "bilateral", "Bilateral pattern", 0.65),
        ("Flag", "continuation", "Continuation pattern", 0.6),
        ("Pennant", "continuation", "Continuation pattern", 0.6),
        ("Wedge", "continuation", "Continuation pattern", 0.65),
        ("Cup and Handle", "continuation", "Bullish continuation pattern", 0.75),
        ("Rounding Bottom", "reversal", "Bullish reversal pattern", 0.7),
        ("Rounding Top", "reversal", "Bearish reversal pattern", 0.7)
    ]
    
    for pattern in patterns:
        cursor.execute("INSERT OR IGNORE INTO chart_patterns (name, type, description, reliability) VALUES (?, ?, ?, ?)", pattern)
    
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# Initialize components
risk_calculator = RiskManagementCalculator(5000, 0.2, 8)
exchange_api = ExchangeRatesAPI(api_key="ef6f59a6a8bfcb2d200e77fc573d2729")
signal_filter = SignalFilter()
breakout_detector = BreakoutDetector()
pattern_verifier = PatternVerifier()

# Set up database connections
conn = sqlite3.connect(DATABASE_PATH)
signal_filter.set_db_connection(conn)
breakout_detector.set_db_connection(conn)
conn.close()

# API Routes
# IFTTT integration removed as requested by user

@app.route('/api/detect-breakouts', methods=['GET'])
def detect_breakouts():
    """Detect breakouts from trend lines and support/resistance levels"""
    pair_symbol = request.args.get('symbol')
    timeframe = request.args.get('timeframe', '1h')
    
    if not pair_symbol:
        return jsonify({"error": "Currency pair symbol is required"}), 400
    
    conn = sqlite3.connect(DATABASE_PATH)
    breakout_detector.set_db_connection(conn)
    
    try:
        # Analyze pair for breakouts
        analysis = breakout_detector.analyze_pair(pair_symbol, timeframe)
        
        # Save detected breakouts to database
        if 'breakouts' in analysis and analysis['breakouts']:
            for breakout in analysis['breakouts']:
                breakout_detector.save_breakout_to_db(breakout, pair_symbol)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/verify-pattern', methods=['POST'])
def verify_pattern_from_image():
    """Verify chart pattern using TradingView screenshot"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    
    if image_file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    try:
        # Save the uploaded image
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        image_path = os.path.join(upload_dir, image_file.filename)
        image_file.save(image_path)
        
        # Analyze the image
        analysis = pattern_verifier.analyze_tradingview_screenshot(image_path)
        
        # Add the image path to the response
        analysis['image_path'] = image_path
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/update-forex-data', methods=['GET'])
def update_forex_data():
    """Update forex data from exchangeratesapi.io"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Get all currency pairs
        cursor = conn.cursor()
        cursor.execute("SELECT id, symbol FROM currency_pairs")
        pairs = cursor.fetchall()
        
        results = {}
        
        for pair_id, pair_symbol in pairs:
            # Get latest rates
            rates = exchange_api.get_latest_rates(pair_symbol.split('/')[0], [pair_symbol.split('/')[1]])
            
            if rates and 'success' in rates and rates['success']:
                # Extract rate
                base_currency = pair_symbol.split('/')[0]
                quote_currency = pair_symbol.split('/')[1]
                rate = rates['rates'].get(quote_currency)
                
                if rate:
                    # Store in database
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        "INSERT INTO historical_data (pair_id, timeframe, open_price, high_price, low_price, close_price, volume, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (pair_id, '1h', rate, rate, rate, rate, 0, timestamp)
                    )
                    
                    results[pair_symbol] = {
                        'rate': rate,
                        'timestamp': timestamp
                    }
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Forex data updated successfully",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/currency-pairs', methods=['GET'])
def get_currency_pairs():
    """Get all currency pairs"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, symbol, name, type, pip_value FROM currency_pairs")
        pairs = cursor.fetchall()
        
        result = []
        for pair in pairs:
            result.append({
                'id': pair[0],
                'symbol': pair[1],
                'name': pair[2],
                'type': pair[3],
                'pip_value': pair[4]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/chart-patterns', methods=['GET'])
def get_chart_patterns():
    """Get all chart patterns"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, description, reliability FROM chart_patterns")
        patterns = cursor.fetchall()
        
        result = []
        for pattern in patterns:
            result.append({
                'id': pattern[0],
                'name': pattern[1],
                'type': pattern[2],
                'description': pattern[3],
                'reliability': pattern[4]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/pattern-detections', methods=['GET'])
def get_pattern_detections():
    """Get pattern detections"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pd.id, cp.symbol, chp.name, pd.timeframe, pd.entry_price, pd.stop_loss, pd.take_profit, pd.confidence, pd.detected_at
            FROM pattern_detections pd
            JOIN currency_pairs cp ON pd.pair_id = cp.id
            JOIN chart_patterns chp ON pd.pattern_id = chp.id
            ORDER BY pd.detected_at DESC
            LIMIT 20
        """)
        detections = cursor.fetchall()
        
        result = []
        for detection in detections:
            result.append({
                'id': detection[0],
                'pair_symbol': detection[1],
                'pattern_name': detection[2],
                'timeframe': detection[3],
                'entry_price': detection[4],
                'stop_loss': detection[5],
                'take_profit': detection[6],
                'confidence': detection[7],
                'detected_at': detection[8]
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance, previous_balance, risk_percentage, drawdown_percentage, updated_at FROM account ORDER BY id DESC LIMIT 1")
        account = cursor.fetchone()
        
        if account:
            result = {
                'balance': account[0],
                'previous_balance': account[1],
                'risk_percentage': account[2],
                'drawdown_percentage': account[3],
                'updated_at': account[4]
            }
            
            # Calculate drawdown
            drawdown_amount = account[1] * (account[3] / 100)
            drawdown_threshold = account[1] - drawdown_amount
            
            result['drawdown_amount'] = drawdown_amount
            result['drawdown_threshold'] = drawdown_threshold
            
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "No account information found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/calculate-risk', methods=['POST'])
def calculate_risk():
    """Calculate risk for a trade"""
    data = request.json
    
    if not data or 'entry_price' not in data or 'stop_loss' not in data:
        return jsonify({
            "success": False,
            "error": "Entry price and stop loss are required"
        }), 400
    
    try:
        # Get account information
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT balance, risk_percentage FROM account ORDER BY id DESC LIMIT 1")
        account = cursor.fetchone()
        conn.close()
        
        if not account:
            return jsonify({
                "success": False,
                "error": "No account information found"
            }), 404
        
        balance = account[0]
        risk_percentage = account[1]
        
        # Calculate risk
        entry_price = float(data['entry_price'])
        stop_loss = float(data['stop_loss'])
        
        risk_amount = balance * (risk_percentage / 100)
        price_difference = abs(entry_price - stop_loss)
        position_size = risk_amount / price_difference
        
        # Calculate take profit based on risk:reward ratio
        risk_reward_ratio = data.get('risk_reward_ratio', 2)
        take_profit = entry_price + (price_difference * risk_reward_ratio) if entry_price > stop_loss else entry_price - (price_difference * risk_reward_ratio)
        
        return jsonify({
            "success": True,
            "risk_amount": risk_amount,
            "position_size": position_size,
            "take_profit": take_profit
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/filtered-signals', methods=['GET'])
def get_filtered_signals():
    """Get filtered trading signals"""
    min_confidence = request.args.get('min_confidence', 75, type=int)
    
    conn = sqlite3.connect(DATABASE_PATH)
    signal_filter.set_db_connection(conn)
    
    try:
        # Get filtered signals
        signals = signal_filter.filter_signals(min_confidence=min_confidence)
        
        # Calculate risk for each signal
        cursor = conn.cursor()
        cursor.execute("SELECT balance, risk_percentage FROM account ORDER BY id DESC LIMIT 1")
        account = cursor.fetchone()
        
        if account:
            balance = account[0]
            risk_percentage = account[1]
            
            for signal in signals:
                entry_price = signal['entry_price']
                stop_loss = signal['stop_loss']
                
                risk_amount = balance * (risk_percentage / 100)
                price_difference = abs(entry_price - stop_loss)
                position_size = risk_amount / price_difference
                
                signal['risk_amount'] = risk_amount
                signal['position_size'] = position_size
        
        return jsonify(signals)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/telegram-bot/config', methods=['GET', 'POST'])
def telegram_bot_config():
    """Configure Telegram bot"""
    if request.method == 'GET':
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'telegram_bot_token'")
            token = cursor.fetchone()
            
            cursor.execute("SELECT value FROM settings WHERE key = 'webapp_url'")
            url = cursor.fetchone()
            
            return jsonify({
                "success": True,
                "token": token[0] if token else TELEGRAM_BOT_TOKEN,
                "webapp_url": url[0] if url else WEBAPP_URL
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
        finally:
            conn.close()
    else:  # POST
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            cursor = conn.cursor()
            
            if 'token' in data:
                cursor.execute("UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'telegram_bot_token'", 
                              (data['token'],))
            
            if 'webapp_url' in data:
                cursor.execute("UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'webapp_url'", 
                              (data['webapp_url'],))
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Telegram bot configuration updated successfully"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
        finally:
            conn.close()

@app.route('/api/telegram-bot/start', methods=['POST'])
def start_telegram_bot():
    """Start Telegram bot"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'telegram_bot_token'")
        token = cursor.fetchone()
        
        cursor.execute("SELECT value FROM settings WHERE key = 'webapp_url'")
        url = cursor.fetchone()
        
        token = token[0] if token else TELEGRAM_BOT_TOKEN
        url = url[0] if url else WEBAPP_URL
        
        # Initialize and start the bot
        bot = TelegramBotIntegration(token=token, webapp_url=url)
        
        # Start the bot in a separate thread
        import threading
        bot_thread = threading.Thread(target=bot.run)
        bot_thread.daemon = True
        bot_thread.start()
        
        return jsonify({
            "success": True,
            "message": "Telegram bot started successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()

# Frontend routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
