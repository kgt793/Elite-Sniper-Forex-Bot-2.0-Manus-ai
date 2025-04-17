# Forex Trading Bot User Guide

## Overview

This Forex Trading Bot is a comprehensive tool designed to help you monitor currency pairs, identify chart patterns, and manage risk in your Forex trading. The application features a web interface and Telegram bot integration, allowing you to access trading information from anywhere.

## Key Features

- **Currency Pair Monitoring**: Track multiple Forex pairs in real-time
- **Chart Pattern Detection**: Automatically identify common chart patterns
- **Risk Management**: Calculate position sizes based on your risk tolerance (0.2% risk per trade)
- **Drawdown Control**: Monitor and limit drawdown to 8% of previous day's balance
- **Telegram Integration**: Receive alerts and control the bot via Telegram

## Getting Started

### System Requirements

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for Forex data updates
- Telegram account (for bot integration)

### Installation

1. Ensure all files are in the `/home/ubuntu/forex_trading_bot` directory
2. Make the deployment script executable:
   ```
   chmod +x /home/ubuntu/forex_trading_bot/deploy.sh
   ```
3. Run the deployment script:
   ```
   ./deploy.sh
   ```
4. The script will install required dependencies and start the web application

### Accessing the Web Interface

Once deployed, the web interface will be available at:
- Local access: http://localhost:5000
- External access: Use the URL provided by the deployment script

### Setting Up Telegram Bot Integration

1. Create a new Telegram bot using BotFather
2. Get your bot token
3. Update the token in Settings → Telegram section of the web interface
4. Start a chat with your bot on Telegram
5. Run the Telegram bot script:
   ```
   python3 /home/ubuntu/forex_trading_bot/backend/telegram_bot.py
   ```

## Using the Web Interface

### Dashboard

The dashboard provides an overview of your account status, including:
- Current balance
- Risk per trade (0.2%)
- Maximum drawdown limit (8%)
- Current drawdown

### Currency Pairs Table

The Currency Pairs table displays all available Forex pairs with:
- Symbol and name
- Current price and daily change
- Detected chart patterns
- Spread information
- Pair type (Major, Cross, Exotic)

You can filter the table by pair type using the buttons above the table.

### Chart Patterns

The Chart Patterns section shows all supported patterns with:
- Pattern name and type
- Description
- Success rate
- Current signals (which pairs are showing this pattern)

Patterns are categorized as:
- **Continuation**: Signal that a current trend will continue
- **Reversal**: Indicate a trend is going to change direction
- **Bilateral**: Indicate a market could move in either direction

### Risk Calculator

The Risk Calculator helps you determine the appropriate position size for a trade:

1. Select a currency pair
2. Enter your entry price
3. Enter your stop loss price
4. Optionally enter a take profit price
5. Select your trade direction (Buy/Sell)
6. Click "Calculate"

The calculator will show:
- Risk amount in dollars (0.2% of your balance)
- Recommended position size
- Stop loss distance in pips
- Risk/reward ratio
- Potential profit

### Settings

The Settings section allows you to configure:
- Account details
- Risk management parameters
- API connections
- Telegram bot settings
- Notification preferences

## Using the Telegram Bot

The Telegram bot provides access to key features via chat commands:

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/status` - Check account status and balance
- `/pairs` - List available currency pairs
- `/patterns` - Show detected chart patterns
- `/calculate` - Calculate position size for a trade
- `/settings` - View and update settings

### Example Commands

- Check account status:
  ```
  /status
  ```

- View all currency pairs:
  ```
  /pairs
  ```

- View only major pairs:
  ```
  /pairs major
  ```

- Calculate position size:
  ```
  /calculate EUR/USD 1.1200 1.1150
  ```

- Calculate with take profit:
  ```
  /calculate EUR/USD 1.1200 1.1150 1.1300
  ```

## Risk Management

This trading bot implements a conservative risk management strategy:

- **Risk per trade**: 0.2% of account balance
- **Maximum daily drawdown**: 8% of previous day's balance
- **Position sizing**: Automatically calculated based on stop loss distance

The system will:
1. Calculate the dollar amount at risk (0.2% of balance)
2. Determine the appropriate position size based on stop loss distance
3. Track drawdown and alert you if approaching the 8% limit
4. Reset drawdown tracking at the start of each trading day

## Troubleshooting

### Web Interface Issues

- **Page not loading**: Ensure the Flask application is running
- **Data not updating**: Check your internet connection
- **Calculation errors**: Verify input values are correct

### Telegram Bot Issues

- **Bot not responding**: Ensure the bot script is running
- **Command errors**: Check command syntax in `/help`
- **Connection issues**: Verify your bot token is correct

### Restarting the Application

To restart the application:

1. Stop the current instance:
   ```
   kill $(cat /home/ubuntu/forex_trading_bot/flask.pid)
   ```
2. Run the deployment script again:
   ```
   ./deploy.sh
   ```

## Support and Feedback

For support or to provide feedback, please contact the developer through the original communication channel.

---

## Technical Information

### Directory Structure

```
forex_trading_bot/
├── backend/
│   ├── app.py                 # Flask application
│   ├── risk_calculator.py     # Risk management calculator
│   └── telegram_bot.py        # Telegram bot implementation
├── data/
│   └── forex_bot.db           # SQLite database
├── frontend/
│   └── index.html             # Web interface
├── research/
│   ├── chart_patterns.md      # Chart patterns documentation
│   ├── forex_pairs.md         # Currency pairs documentation
│   └── risk_management.md     # Risk management documentation
├── deploy.sh                  # Deployment script
├── test_app.sh                # Testing script
└── todo.md                    # Development checklist
```

### Technologies Used

- **Backend**: Python, Flask, SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Data**: SQLite database
- **Communication**: Telegram Bot API
- **Deployment**: Bash scripts

### Database Schema

The application uses a SQLite database with the following tables:

- `currency_pairs`: Information about Forex pairs
- `chart_patterns`: Chart pattern definitions
- `pattern_detections`: Detected patterns for currency pairs
- `account`: Account balance and risk settings
- `trades`: Trade history
- `historical_data`: Historical price data
- `user_settings`: User preferences and API keys
