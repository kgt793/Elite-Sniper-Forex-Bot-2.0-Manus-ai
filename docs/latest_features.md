# Forex Trading Bot - Latest Features Documentation

## New Features Overview

This document describes the latest features added to the Forex Trading Bot:

1. **Breakout Detection for Trend Lines**
2. **Pattern Verification using TradingView Screenshots**

These features enhance your trading capabilities with advanced technical analysis tools.

## 1. Breakout Detection for Trend Lines

### Overview

The breakout detection system identifies when price breaks through significant trend lines and support/resistance levels, optimized for hourly data frequency.

### Key Features

#### Trend Line Detection
- Automatically identifies swing highs and lows
- Draws trend lines connecting these points
- Calculates trend line strength based on number of touches and timespan
- Works with both ascending and descending trend lines

#### Support/Resistance Level Detection
- Identifies horizontal support and resistance levels
- Calculates level strength based on price clustering
- Counts number of touches for each level
- Prioritizes levels with higher strength

#### Breakout Detection
- Detects bullish breakouts (price breaking above resistance)
- Detects bearish breakouts (price breaking below support)
- Requires confirmation candles to avoid false breakouts
- Calculates breakout percentage to filter insignificant movements

### API Endpoints

#### Detect Breakouts
- **Endpoint**: `/api/detect-breakouts`
- **Method**: GET
- **Parameters**: 
  - `symbol`: Currency pair symbol (e.g., "EUR/USD")
  - `timeframe`: Timeframe for analysis (default: "1h")
- **Response**: Complete analysis including trend lines, support/resistance levels, and detected breakouts

### Usage Examples

#### Web Interface
The breakout detection is integrated into the main dashboard, showing:
- Active trend lines for each currency pair
- Support and resistance levels with strength indicators
- Recent breakouts with confirmation status
- Breakout alerts when new breakouts are detected

#### Telegram Bot
New commands for breakout detection:
- `/breakouts [symbol]` - Get breakout analysis for a currency pair
- `/trendlines [symbol]` - View active trend lines for a currency pair
- `/levels [symbol]` - View support and resistance levels

## 2. Pattern Verification using TradingView Screenshots

### Overview

This feature allows you to upload TradingView chart screenshots and have the system verify chart patterns using computer vision and machine learning techniques.

### Key Features

#### Pattern Recognition
- Identifies 15 common chart patterns:
  - Head and Shoulders / Inverse Head and Shoulders
  - Double Top / Double Bottom
  - Triple Top / Triple Bottom
  - Ascending / Descending / Symmetrical Triangles
  - Flag / Pennant / Wedge
  - Cup and Handle
  - Rounding Bottom / Rounding Top

#### Image Analysis
- Extracts the chart region from screenshots
- Detects candlesticks and their patterns
- Identifies trend lines in the image
- Provides confidence scores for pattern matches

#### Multi-Pattern Detection
- Returns top 3 possible patterns with confidence scores
- Allows for pattern verification with confidence threshold
- Provides alternative interpretations when patterns are ambiguous

### API Endpoints

#### Verify Pattern
- **Endpoint**: `/api/verify-pattern`
- **Method**: POST
- **Parameters**: 
  - `image`: TradingView screenshot file (multipart/form-data)
- **Response**: Pattern verification results including:
  - Detected pattern with confidence score
  - Alternative pattern interpretations
  - Extracted chart region
  - Detected trend lines and candlesticks

### Usage Examples

#### Web Interface
The pattern verification is integrated into the dashboard:
- Upload button for TradingView screenshots
- Pattern verification results display
- Visual overlay of detected patterns on the chart
- Confidence score indicator

#### Telegram Bot
New commands for pattern verification:
- `/verify` (with attached image) - Verify pattern in a TradingView screenshot
- `/patterns` - List all recognizable chart patterns

## Integration with Existing Features

These new features are fully integrated with the existing functionality:

1. **With Signal Filtering**
   - Breakout signals can be filtered using the same confirmation techniques
   - Pattern verification provides an additional confirmation layer for detected patterns

2. **With Risk Management**
   - Breakout trades use the same 0.2% risk per trade rule
   - Respects the 8% drawdown limit based on previous day's balance

3. **With Live Data**
   - Breakout detection uses the hourly data from exchangeratesapi.io
   - Updates automatically when new data is fetched

## Technical Requirements

### For Breakout Detection
- No additional requirements (uses existing libraries)

### For Pattern Verification
- TensorFlow and OpenCV for image processing and pattern recognition
- Additional dependencies added to requirements.txt:
  - tensorflow>=2.8.0
  - opencv-python>=4.5.5
  - pillow>=9.0.0
  - scikit-learn>=1.0.2

## Best Practices

### For Breakout Trading
1. **Wait for Confirmation**
   - Always wait for the confirmation candles (default: 2) before trading a breakout
   - Higher timeframe breakouts are generally more reliable

2. **Consider Trend Line Strength**
   - Breakouts from stronger trend lines (more touches, longer timespan) are more significant
   - Look for confluence with other technical indicators

3. **Watch for False Breakouts**
   - Be cautious of breakouts with small percentage movements
   - Use the signal filtering system to reduce false positives

### For Pattern Verification
1. **Use Clear Screenshots**
   - Ensure your TradingView screenshots are clear and show the complete pattern
   - Avoid screenshots with too many indicators that might obscure the pattern

2. **Check Confidence Scores**
   - Patterns with higher confidence scores (>80%) are more reliable
   - Consider alternative pattern interpretations when confidence is lower

3. **Combine with Other Analysis**
   - Use pattern verification alongside breakout detection and signal filtering
   - The most powerful signals occur when multiple systems align

## Troubleshooting

### Breakout Detection Issues
- If no breakouts are detected, try increasing the lookback period
- If too many breakouts are detected, increase the confirmation candles or price percentage threshold

### Pattern Verification Issues
- If pattern recognition fails, ensure your screenshot clearly shows the chart area
- Try different zoom levels in TradingView for better pattern visibility
- Make sure the pattern is complete (not still forming)

## Future Enhancements

Planned improvements for these features:

1. **For Breakout Detection**
   - Multi-timeframe breakout confirmation
   - Volume-based breakout validation
   - Breakout strength scoring system

2. **For Pattern Verification**
   - Improved model training with more pattern examples
   - Pattern completion percentage estimation
   - Price target calculation based on verified patterns
