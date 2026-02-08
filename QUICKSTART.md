# 🚀 Quick Start Guide

Get your trading bot running in 5 minutes!

## Step 1: Install Dependencies (2 min)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

## Step 2: Get API Keys (1 min)

### Gemini API (FREE!)
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Copy your key

### Binance API (Optional for testing)
1. Go to https://testnet.binance.vision/
2. Sign up for testnet account
3. Get your testnet API keys

## Step 3: Configure (1 min)

```bash
# Copy example config
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Minimum required settings:**
```env
GEMINI_API_KEY=your_gemini_key_here
BINANCE_API_KEY=your_binance_testnet_key
BINANCE_API_SECRET=your_binance_testnet_secret
BINANCE_TESTNET=true
```

## Step 4: Test Run (1 min)

```bash
# Test components individually
python -m src.config.settings           # Check config
python -m src.llm.gemini_client        # Test Gemini
python -m src.data.binance_client      # Test Binance
python -m src.strategy.llm_strategy    # Test strategy

# Run full bot (backtest mode)
python main.py
```

## Expected Output

```
============================================================
🤖 Auto Trading Bot - Configuration Summary
============================================================
Trading Mode:     BACKTEST
Market Type:      SPOT
Testnet:          True
Symbol:           BTC/USDT
Timeframe:        1h
Risk per Trade:   2.0%
...

✅ All components initialized successfully
🚀 Starting trading loop...

============================================================
Iteration #1 - 2026-02-08 14:30:00
============================================================

Fetching market data for BTC/USDT (1h)
Requesting decision from Gemini...

📊 Decision: HOLD
   Confidence: 65.0%
   Reasoning: Market shows mixed signals...

⏸️  Backtest mode - stopping after one iteration
🛑 Trading bot stopped
```

## Common Issues

### "Gemini API key not configured"
- Make sure you copied the key correctly
- Remove any quotes or spaces
- The key should start with "AIza..."

### "Binance connection failed"
- Using testnet? Make sure `BINANCE_TESTNET=true`
- Check if testnet API keys are from https://testnet.binance.vision/
- Real Binance keys won't work with testnet!

### "Module not found"
- Did you activate the virtual environment?
- Run `pip install -r requirements.txt` again

## Next Steps

1. ✅ **Test Components** - Make sure everything works
2. 📊 **Paper Trading** - Run with real-time data, no money
3. 💰 **Small Live Trade** - Start with $10-20
4. 📈 **Scale Up** - Increase capital slowly

## Safety Checklist

Before live trading:
- [ ] Tested in backtest mode ✅
- [ ] Tested in paper trading for 1+ week
- [ ] Understand the risks
- [ ] Using money you can afford to lose
- [ ] Set appropriate risk limits (2-5% per trade)
- [ ] Monitoring system is working
- [ ] Know how to stop the bot (Ctrl+C)

---

**Need Help?** Check the full [README.md](README.md) or open an issue.

**Ready to Trade?** Remember: Start small, test thoroughly, never risk more than you can lose!
