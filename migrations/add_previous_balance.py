#!/usr/bin/env python3
"""
Database migration script to add the missing previous_balance column to the account table.
This fixes the 'sqlite3.OperationalError: table account has no column named previous_balance' error.
"""

import sqlite3
import os
import sys

# Get the absolute path to the database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'forex_bot.db')

def add_previous_balance_column():
    """Add the missing previous_balance column to the account table."""
    print(f"Using database at: {DATABASE_PATH}")
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the account table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account'")
        if not cursor.fetchone():
            print("Creating account table as it doesn't exist...")
            cursor.execute('''
            CREATE TABLE account (
                id INTEGER PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 5000.0,
                previous_balance REAL NOT NULL DEFAULT 5000.0,
                risk_percentage REAL NOT NULL DEFAULT 0.2,
                max_drawdown_percentage REAL NOT NULL DEFAULT 8.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("Account table created successfully with previous_balance column.")
            
            # Insert initial account data
            cursor.execute('''
            INSERT INTO account (balance, previous_balance, risk_percentage, max_drawdown_percentage)
            VALUES (5000.0, 5000.0, 0.2, 8.0)
            ''')
            print("Initial account data inserted.")
        else:
            # Check if previous_balance column exists
            try:
                cursor.execute("SELECT previous_balance FROM account LIMIT 1")
                print("previous_balance column already exists.")
            except sqlite3.OperationalError:
                print("Adding previous_balance column to account table...")
                cursor.execute("ALTER TABLE account ADD COLUMN previous_balance REAL DEFAULT 5000.0")
                
                # Update the previous_balance to match current balance for existing records
                cursor.execute("UPDATE account SET previous_balance = balance")
                print("previous_balance column added and initialized successfully.")
        
        conn.commit()
        print("Database migration completed successfully.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = add_previous_balance_column()
    sys.exit(0 if success else 1)
