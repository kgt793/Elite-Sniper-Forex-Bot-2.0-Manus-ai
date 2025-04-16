#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p /home/ubuntu/forex_trading_bot/data
mkdir -p /home/ubuntu/forex_trading_bot/logs

# Install required Python packages if not already installed
echo "Installing required Python packages..."
pip3 install flask python-telegram-bot requests

# Set up environment variables
export FLASK_APP=/home/ubuntu/forex_trading_bot/backend/app.py
export FLASK_ENV=production

# Start the Flask application
echo "Starting Flask application..."
cd /home/ubuntu/forex_trading_bot
python3 -m flask run --host=0.0.0.0 --port=5000 > /home/ubuntu/forex_trading_bot/logs/flask.log 2>&1 &
FLASK_PID=$!
echo "Flask application started with PID: $FLASK_PID"
echo $FLASK_PID > /home/ubuntu/forex_trading_bot/flask.pid

# Wait for Flask to start
echo "Waiting for Flask to start..."
sleep 5

# Expose the port for external access
echo "Exposing port 5000 for external access..."
echo "The web application will be available at the URL provided below."

# Print instructions
echo ""
echo "==================================================================="
echo "Forex Trading Bot Deployment Complete!"
echo "==================================================================="
echo ""
echo "Web Interface: http://localhost:5000"
echo ""
echo "To stop the application, run: kill \$(cat /home/ubuntu/forex_trading_bot/flask.pid)"
echo ""
echo "To start the Telegram bot (after configuring the token):"
echo "python3 /home/ubuntu/forex_trading_bot/backend/telegram_bot.py"
echo ""
echo "==================================================================="
