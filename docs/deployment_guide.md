# Forex Trading Bot - GitHub and Render Deployment Guide

This guide explains how to deploy your Forex Trading Bot to GitHub and Render.

## Prerequisites

- GitHub account
- Render account (free tier is sufficient)
- Git installed on your local machine

## Step 1: Initialize Git Repository

```bash
cd /home/ubuntu/forex_trading_bot
git init
```

## Step 2: Create .gitignore File

Create a `.gitignore` file to exclude unnecessary files:

```bash
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Local development settings
.env
*.db
*.sqlite3

# Logs
logs/
*.log

# Virtual Environment
venv/
env/

# OS specific files
.DS_Store
Thumbs.db

# IDE specific files
.idea/
.vscode/
```

## Step 3: Commit Your Code

```bash
git add .
git commit -m "Initial commit of Forex Trading Bot"
```

## Step 4: Create GitHub Repository

1. Go to GitHub.com and log in
2. Click on the "+" icon in the top right corner and select "New repository"
3. Name your repository (e.g., "forex-trading-bot")
4. Choose public or private visibility
5. Click "Create repository"

## Step 5: Push Code to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/forex-trading-bot.git
git branch -M main
git push -u origin main
```

## Step 6: Deploy to Render

1. Sign up or log in to Render (render.com)
2. Click "New" and select "Web Service"
3. Connect your GitHub account and select your repository
4. Configure your web service:
   - Name: forex-trading-bot
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --chdir backend app:app`
   - Plan: Free

5. Click "Create Web Service"

## Step 7: Configure Environment Variables (if needed)

In Render dashboard:
1. Go to your web service
2. Click on "Environment" tab
3. Add any necessary environment variables:
   - TELEGRAM_BOT_TOKEN (if you have one)

## Step 8: Set Up Uptime Robot

1. Create an account on uptimerobot.com
2. Add a new monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: Forex Trading Bot
   - URL: Your Render application URL
   - Monitoring Interval: 5 minutes

## Step 9: Access Your Application

Your application will be available at the URL provided by Render, typically in the format:
`https://forex-trading-bot-xxxx.onrender.com`

## Troubleshooting

- Check Render logs if your application fails to deploy
- Ensure your application is configured to use the PORT environment variable
- Make sure all dependencies are listed in requirements.txt
- If database issues occur, consider using a persistent database service

## Updating Your Application

To update your application:

1. Make changes to your local code
2. Commit changes: `git add . && git commit -m "Update description"`
3. Push to GitHub: `git push origin main`
4. Render will automatically deploy the new version

## Database Considerations

The current implementation uses SQLite, which works for development but has limitations on Render:

1. Render's free tier uses ephemeral storage, meaning your SQLite database will reset on each deploy
2. For production, consider:
   - Using Render's PostgreSQL service
   - Using a cloud database service like MongoDB Atlas
   - Implementing database migration scripts

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [GitHub Documentation](https://docs.github.com/en)
- [Uptime Robot Documentation](https://uptimerobot.com/help)
