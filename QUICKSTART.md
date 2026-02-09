# 🚀 Quick Start Guide

Get your trading bot running in 5 minutes!

## Step 1: Install Dependencies (2 min)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Get API Keys (1 min)

### Gemini API (FREE!)
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Copy your key

### Binance API (Optional for testing)
1. Go to https://www.binance.com/en/my/settings/api-management
2. Create API keys (or use demo mode for paper trading)
3. Enable "Enable Spot & Margin Trading" permission

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
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
BINANCE_DEMO_MODE=true
```

## Step 4: Test Run (1 min)

```bash
# Quick test (recommended)
python run_test.py

# Or test components individually
python -m src.config.settings
python -m src.llm.gemini_client
python -m src.data.binance_client

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
Demo Mode:        True (Paper Trading)
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
- Using demo mode? Make sure `BINANCE_DEMO_MODE=true`
- Check your API keys are correct
- Ensure API keys have trading permissions enabled

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
