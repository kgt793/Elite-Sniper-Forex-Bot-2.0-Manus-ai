import os
import logging
import json
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

class TelegramBotIntegration:
    """
    A class to handle Telegram bot integration for the Forex trading bot
    """
    
    def __init__(self, token=None, webapp_url=None):
        """
        Initialize the Telegram bot integration
        
        Args:
            token (str): Telegram bot token
            webapp_url (str): URL of the web application
        """
        self.token = token or os.environ.get('TELEGRAM_BOT_TOKEN', '7895580284:AAGTKQSDJzst5Ri7ZMeQcQiGQOFbt9_sNzo')
        self.webapp_url = webapp_url or os.environ.get('WEBAPP_URL', 'https://your-render-url.onrender.com')
        self.application = None
        
    def set_token(self, token):
        """
        Set the Telegram bot token
        
        Args:
            token (str): Telegram bot token
        """
        self.token = token
        
    def set_webapp_url(self, webapp_url):
        """
        Set the web application URL
        
        Args:
            webapp_url (str): URL of the web application
        """
        self.webapp_url = webapp_url
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command
        """
        keyboard = [
            [InlineKeyboardButton("Open Forex Trading Bot", web_app=WebAppInfo(url=self.webapp_url))],
            [InlineKeyboardButton("View Signals", callback_data='signals')],
            [InlineKeyboardButton("Settings", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Welcome to the Forex Trading Bot!\n\n"
            "• View all currency pairs and chart patterns in table format\n"
            "• Get real-time trading signals with entry, SL, and TP levels\n"
            "• Monitor your account with 0.2% risk management\n"
            "• 8% drawdown protection based on previous day's balance\n\n"
            "Click the button below to open the trading dashboard:",
            reply_markup=reply_markup
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /help command
        """
        help_text = (
            "📊 *Forex Trading Bot Commands* 📊\n\n"
            "/start - Open the main menu\n"
            "/signals - View latest trading signals in table format\n"
            "/pairs - List available currency pairs\n"
            "/patterns - List recognized chart patterns\n"
            "/verify - Upload a TradingView screenshot for pattern verification\n"
            "/breakouts - Check for recent breakouts\n"
            "/settings - Configure your trading preferences\n"
            "/risk - View risk management calculator\n\n"
            "To use the full dashboard, click the 'Open Forex Trading Bot' button in the main menu."
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /signals command
        """
        # This would typically fetch signals from your database
        # For now, we'll return sample data
        signals = [
            {
                "pair": "EUR/USD",
                "type": "Bullish Breakout",
                "entry": "1.0850",
                "stop_loss": "1.0820",
                "take_profit": "1.0910",
                "risk_amount": "$10.00",
                "confidence": "85%",
                "duration": "2-3 days",
                "time": "2025-04-16 10:30"
            },
            {
                "pair": "GBP/JPY",
                "type": "Double Bottom",
                "entry": "185.20",
                "stop_loss": "184.50",
                "take_profit": "187.40",
                "risk_amount": "$11.67",
                "confidence": "92%",
                "duration": "1-2 days",
                "time": "2025-04-16 09:15"
            }
        ]
        
        # Format signals as a table
        message = "📈 *Latest Trading Signals* 📈\n\n"
        message += "```\n"
        message += "PAIR     | TYPE           | ENTRY   | SL      | TP      | RISK    | CONF | DURATION\n"
        message += "---------|----------------|---------|---------|---------|---------|------|----------\n"
        
        for signal in signals:
            message += f"{signal['pair']:<9}| {signal['type']:<16}| {signal['entry']:<9}| {signal['stop_loss']:<9}| {signal['take_profit']:<9}| {signal['risk_amount']:<9}| {signal['confidence']:<6}| {signal['duration']}\n"
        
        message += "```\n\n"
        message += "Use this table to manually enter trades in your Alchemy Trade & Invest app."
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /pairs command
        """
        pairs_message = (
            "💱 *Available Currency Pairs* 💱\n\n"
            "*Major Pairs:*\n"
            "• EUR/USD - Euro / US Dollar\n"
            "• USD/JPY - US Dollar / Japanese Yen\n"
            "• GBP/USD - British Pound / US Dollar\n"
            "• USD/CHF - US Dollar / Swiss Franc\n"
            "• AUD/USD - Australian Dollar / US Dollar\n"
            "• USD/CAD - US Dollar / Canadian Dollar\n"
            "• NZD/USD - New Zealand Dollar / US Dollar\n\n"
            
            "*Cross Pairs:*\n"
            "• EUR/GBP - Euro / British Pound\n"
            "• EUR/JPY - Euro / Japanese Yen\n"
            "• GBP/JPY - British Pound / Japanese Yen\n"
            "• AUD/JPY - Australian Dollar / Japanese Yen\n"
            "• EUR/AUD - Euro / Australian Dollar\n\n"
            
            "*Exotic Pairs:*\n"
            "• USD/SGD - US Dollar / Singapore Dollar\n"
            "• USD/HKD - US Dollar / Hong Kong Dollar\n"
            "• USD/TRY - US Dollar / Turkish Lira\n"
            "• USD/MXN - US Dollar / Mexican Peso\n"
        )
        
        await update.message.reply_text(pairs_message, parse_mode='Markdown')
        
    async def patterns_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /patterns command
        """
        patterns_message = (
            "📊 *Recognized Chart Patterns* 📊\n\n"
            "*Reversal Patterns:*\n"
            "• Head and Shoulders\n"
            "• Inverse Head and Shoulders\n"
            "• Double Top\n"
            "• Double Bottom\n"
            "• Triple Top\n"
            "• Triple Bottom\n"
            "• Rounding Bottom (Saucer)\n"
            "• Rounding Top\n\n"
            
            "*Continuation Patterns:*\n"
            "• Flags (Bullish/Bearish)\n"
            "• Pennants\n"
            "• Wedges (Rising/Falling)\n"
            "• Rectangles\n"
            "• Cup and Handle\n\n"
            
            "*Bilateral Patterns:*\n"
            "• Triangles (Ascending/Descending/Symmetrical)\n"
            "• Diamond\n"
        )
        
        await update.message.reply_text(patterns_message, parse_mode='Markdown')
        
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle button callbacks
        """
        query = update.callback_query
        await query.answer()
        
        if query.data == 'signals':
            await self.signals_command(update, context)
        elif query.data == 'settings':
            settings_text = (
                "⚙️ *Trading Bot Settings* ⚙️\n\n"
                "*Risk Management:*\n"
                "• Risk per trade: 0.2%\n"
                "• Max drawdown: 8% of previous day's balance\n"
                "• Starting balance: $5,000\n\n"
                
                "*Signal Filters:*\n"
                "• Minimum confidence: 75%\n"
                "• Confirmation indicators: 3\n"
                "• Pattern verification: Enabled\n\n"
                
                "*Notifications:*\n"
                "• Telegram alerts: Enabled\n\n"
                
                "To change settings, use the web dashboard."
            )
            await query.message.reply_text(settings_text, parse_mode='Markdown')
            
    def run(self):
        """
        Run the Telegram bot
        """
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("pairs", self.pairs_command))
        self.application.add_handler(CommandHandler("patterns", self.patterns_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start the bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    def start_webhook(self, webhook_url):
        """
        Start the bot using webhooks (for production)
        
        Args:
            webhook_url (str): Webhook URL
        """
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("pairs", self.pairs_command))
        self.application.add_handler(CommandHandler("patterns", self.patterns_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Set up webhook
        self.application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8443)),
            url_path=self.token,
            webhook_url=f"{webhook_url}/{self.token}"
        )
