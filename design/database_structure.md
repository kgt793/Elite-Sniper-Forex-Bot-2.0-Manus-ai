# Database Structure for Forex Trading Bot

## Overview
This document outlines the database structure for our Forex trading bot, which will store information about currency pairs, chart patterns, and trading signals.

## Database Tables

### 1. Currency Pairs Table
```sql
CREATE TABLE currency_pairs (
    pair_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    base_currency VARCHAR(3) NOT NULL,
    quote_currency VARCHAR(3) NOT NULL,
    pip_value DECIMAL(10, 5) NOT NULL,
    average_spread DECIMAL(10, 5),
    trading_hours VARCHAR(100),
    description TEXT,
    pair_type VARCHAR(20) NOT NULL,  -- 'major', 'cross', 'exotic'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Chart Patterns Table
```sql
CREATE TABLE chart_patterns (
    pattern_id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- 'continuation', 'reversal', 'bilateral'
    description TEXT,
    formation_criteria TEXT,
    success_rate DECIMAL(5, 2),
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Pattern Detection Table
```sql
CREATE TABLE pattern_detections (
    detection_id INTEGER PRIMARY KEY,
    pair_id INTEGER NOT NULL,
    pattern_id INTEGER NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h', '4h', '1d', etc.
    detection_time TIMESTAMP NOT NULL,
    confidence_score DECIMAL(5, 2),
    price_at_detection DECIMAL(10, 5) NOT NULL,
    target_price DECIMAL(10, 5),
    stop_loss_price DECIMAL(10, 5),
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'invalidated'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(pair_id),
    FOREIGN KEY (pattern_id) REFERENCES chart_patterns(pattern_id)
);
```

### 4. Account Table
```sql
CREATE TABLE account (
    account_id INTEGER PRIMARY KEY,
    balance DECIMAL(15, 2) NOT NULL,
    previous_day_balance DECIMAL(15, 2),
    max_drawdown_amount DECIMAL(15, 2),
    current_drawdown DECIMAL(15, 2) DEFAULT 0,
    risk_percentage DECIMAL(5, 2) DEFAULT 0.2,
    drawdown_percentage DECIMAL(5, 2) DEFAULT 8.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Trades Table
```sql
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY,
    pair_id INTEGER NOT NULL,
    detection_id INTEGER,
    entry_price DECIMAL(10, 5) NOT NULL,
    exit_price DECIMAL(10, 5),
    position_size DECIMAL(10, 5) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    stop_loss DECIMAL(10, 5) NOT NULL,
    take_profit DECIMAL(10, 5),
    risk_amount DECIMAL(10, 2) NOT NULL,
    profit_loss DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(pair_id),
    FOREIGN KEY (detection_id) REFERENCES pattern_detections(detection_id)
);
```

### 6. Historical Data Table
```sql
CREATE TABLE historical_data (
    data_id INTEGER PRIMARY KEY,
    pair_id INTEGER NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 5) NOT NULL,
    high_price DECIMAL(10, 5) NOT NULL,
    low_price DECIMAL(10, 5) NOT NULL,
    close_price DECIMAL(10, 5) NOT NULL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(pair_id)
);
```

### 7. User Settings Table
```sql
CREATE TABLE user_settings (
    setting_id INTEGER PRIMARY KEY,
    telegram_chat_id VARCHAR(50),
    notification_preferences JSON,
    ui_preferences JSON,
    api_keys JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relationships

1. **Currency Pairs to Pattern Detections**: One-to-many (one currency pair can have many pattern detections)
2. **Chart Patterns to Pattern Detections**: One-to-many (one chart pattern can be detected many times)
3. **Pattern Detections to Trades**: One-to-many (one pattern detection can lead to multiple trades)
4. **Currency Pairs to Historical Data**: One-to-many (one currency pair has many historical data points)
5. **Currency Pairs to Trades**: One-to-many (one currency pair can have many trades)

## Data Flow

1. **Historical Data Collection**:
   - Fetch data from Forex API
   - Store in historical_data table
   - Update currency_pairs table with latest information

2. **Pattern Detection**:
   - Analyze historical data for patterns
   - Record detected patterns in pattern_detections table
   - Calculate confidence scores

3. **Trade Management**:
   - Calculate position size based on account risk settings
   - Record trades in trades table
   - Update account balance and drawdown information

4. **User Interface**:
   - Display currency pairs and detected patterns
   - Show account statistics and trade history
   - Allow configuration of user settings

## Indexes for Performance

```sql
-- Indexes for faster queries
CREATE INDEX idx_currency_pairs_symbol ON currency_pairs(symbol);
CREATE INDEX idx_pattern_detections_pair_id ON pattern_detections(pair_id);
CREATE INDEX idx_pattern_detections_pattern_id ON pattern_detections(pattern_id);
CREATE INDEX idx_trades_pair_id ON trades(pair_id);
CREATE INDEX idx_historical_data_pair_id_timestamp ON historical_data(pair_id, timestamp);
CREATE INDEX idx_historical_data_timeframe ON historical_data(timeframe);
```

## Initial Data Population

The database will be initially populated with:
1. Common currency pairs (majors, crosses, exotics)
2. Well-known chart patterns with their characteristics
3. Default account settings with $5,000 balance, 0.2% risk, and 8% drawdown limit

This database structure provides a solid foundation for the Forex trading bot, allowing for efficient storage and retrieval of currency pair information, chart patterns, and trading data.
