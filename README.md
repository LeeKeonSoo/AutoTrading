# 🤖 LLM Auto Trading Bot

AI-powered cryptocurrency trading system that uses Claude (LLM) to make intelligent trading decisions on Binance.

## ⚠️ Disclaimer

**THIS SOFTWARE IS FOR EDUCATIONAL PURPOSES ONLY.**

- Trading cryptocurrencies carries significant risk of financial loss
- This is experimental software and may contain bugs
- Never invest more than you can afford to lose
- Always test thoroughly with testnet and paper trading before using real money
- The developers are not responsible for any financial losses incurred

## 🎯 Features

- **LLM-Powered Decision Making**: Uses Anthropic's Claude to analyze market data and make trading decisions
- **Comprehensive Backtesting**: Test strategies on historical data with realistic fees and slippage
- **Paper Trading**: Practice with real-time data without risking real money
- **Risk Management**: Built-in stop-loss, position sizing, and daily loss limits
- **Real-time Monitoring**: Streamlit dashboard and Telegram notifications
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, and more
- **Safe by Default**: Starts with testnet and paper trading mode

## 📋 Prerequisites

- Python 3.11 or higher
- Binance account (or testnet account for practice)
- Anthropic API key (for Claude)
- Basic understanding of cryptocurrency trading

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (or download as ZIP)
cd AutoTrading

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required settings:**
- `BINANCE_API_KEY`: Your Binance API key ([Get it here](https://www.binance.com/en/my/settings/api-management))
- `BINANCE_API_SECRET`: Your Binance API secret
- `ANTHROPIC_API_KEY`: Your Anthropic API key ([Get it here](https://console.anthropic.com/))
- `BINANCE_TESTNET`: Set to `true` for safe testing

**Recommended first-time settings:**
```
BINANCE_TESTNET=true
TRADING_MODE=backtest
TRADING_SYMBOL=BTC/USDT
RISK_PER_TRADE=0.02
```

### 3. Run Backtest

```bash
# Download historical data
python scripts/download_data.py

# Run backtest
python scripts/run_backtest.py
```

### 4. Launch Dashboard

```bash
# Start Streamlit dashboard
streamlit run dashboard/app.py
```

## 📊 Trading Modes

### 1. Backtest Mode
Test strategies on historical data to evaluate performance.

```bash
# In .env file:
TRADING_MODE=backtest

# Run backtest
python scripts/run_backtest.py
```

### 2. Paper Trading Mode
Simulate live trading with real-time data but no real money.

```bash
# In .env file:
TRADING_MODE=paper
BINANCE_TESTNET=true

# Run paper trading
python main.py
```

### 3. Live Trading Mode
**⚠️ USE WITH EXTREME CAUTION**

Only use after:
- Successful backtesting (Sharpe > 1.0, Max DD < 20%)
- 2-4 weeks of successful paper trading
- Starting with small amounts (5-10% of capital)

```bash
# In .env file:
TRADING_MODE=live
BINANCE_TESTNET=false  # Real money!

# Run live trading
python main.py
```

## 🏗️ Project Structure

```
AutoTrading/
├── src/
│   ├── config/          # Configuration management
│   ├── data/            # Data collection (Binance API, indicators)
│   ├── llm/             # LLM integration (Claude)
│   ├── strategy/        # Trading strategies
│   ├── backtesting/     # Backtesting engine
│   ├── risk/            # Risk management
│   ├── execution/       # Order execution
│   ├── monitoring/      # Logging and notifications
│   └── database/        # Database models
├── tests/               # Unit and integration tests
├── notebooks/           # Jupyter notebooks for analysis
├── dashboard/           # Streamlit dashboard
├── scripts/             # Utility scripts
├── data/                # Data storage
│   ├── historical/      # Historical market data
│   └── trades/          # Trading history
└── main.py              # Main entry point
```

## 🛡️ Risk Management

The system includes multiple layers of risk management:

1. **Position Sizing**: Automatically calculates position size based on account balance and risk tolerance
2. **Stop Loss**: Automatic stop-loss orders on every trade
3. **Daily Loss Limit**: Trading stops if daily loss exceeds threshold
4. **Max Positions**: Limits number of simultaneous positions
5. **Confidence Threshold**: Only executes trades when LLM confidence is high
6. **Validation**: All LLM decisions are validated before execution

## 📈 Performance Metrics

The system tracks comprehensive performance metrics:

- **Total Return**: Overall profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Average Trade**: Mean profit/loss per trade

## 🔧 Configuration

Key configuration options in `.env`:

| Setting | Description | Default |
|---------|-------------|---------|
| `TRADING_SYMBOL` | Cryptocurrency pair | BTC/USDT |
| `TRADING_TIMEFRAME` | Candle timeframe | 1h |
| `RISK_PER_TRADE` | Risk per trade (%) | 0.02 (2%) |
| `MAX_POSITION_SIZE` | Max position size (%) | 0.05 (5%) |
| `MIN_CONFIDENCE` | Min LLM confidence | 0.70 |
| `DEFAULT_STOP_LOSS_PCT` | Stop loss (%) | 0.02 (2%) |
| `DEFAULT_TAKE_PROFIT_PCT` | Take profit (%) | 0.05 (5%) |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_data/test_binance_client.py
```

## 📱 Monitoring

### Streamlit Dashboard
Real-time monitoring interface:
```bash
streamlit run dashboard/app.py
```

### Telegram Notifications
Get alerts for trades and errors:
1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add to `.env`:
```
ENABLE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🐛 Troubleshooting

### "ccxt.binance() connection failed"
- Check your API keys
- Verify testnet setting matches your API keys
- Check internet connection

### "Anthropic API error"
- Verify your API key is correct
- Check API quota and billing
- Ensure model name is correct

### "Insufficient balance"
- In paper trading, initial balance is set in config
- In live trading, check your Binance balance
- Verify you have enough for fees

### "Rate limit exceeded"
- Reduce `API_RATE_LIMIT` in `.env`
- Increase delays between requests
- Consider upgrading Binance API tier

## 📚 Documentation

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [CCXT Documentation](https://docs.ccxt.com/)

## 🛣️ Roadmap

- [ ] Phase 1: Project setup and infrastructure ✅
- [ ] Phase 2: Data collection module
- [ ] Phase 3: LLM integration
- [ ] Phase 4: Backtesting engine
- [ ] Phase 5: Risk management
- [ ] Phase 6: Execution and position management
- [ ] Phase 7: Monitoring and dashboard
- [ ] Phase 8: Testing and validation
- [ ] Phase 9: Deployment

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome! Please open an issue before submitting major changes.

## 📄 License

This project is for personal use and educational purposes. No license is granted for commercial use.

## 💡 Tips for Success

1. **Start Small**: Always begin with testnet and paper trading
2. **Be Patient**: Test for at least 2-4 weeks before live trading
3. **Monitor Actively**: Don't set and forget - watch your trades
4. **Adjust Parameters**: Market conditions change, adapt your strategy
5. **Keep Learning**: Review your trades and learn from mistakes
6. **Risk Management**: Never risk more than you can afford to lose
7. **Diversify**: Don't put all capital in one strategy or coin

## 📞 Support

For issues and questions:
- Check existing GitHub issues
- Review documentation
- Ensure you're using latest version
- Provide detailed error messages and logs

---

**Remember**: Past performance does not guarantee future results. This system is not a money-printing machine. Trade responsibly.
