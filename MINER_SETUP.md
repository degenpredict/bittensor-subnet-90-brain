# 🤖 AI Miner Setup Guide

This guide shows you how to set up an AI-powered miner that uses the same APIs and reasoning as the centralized brainstorm engine.

## 🚀 Quick Start

### 1. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

### 2. Required API Keys

**For Basic AI Mining** (minimum setup):
```bash
OPENAI_API_KEY=sk-your-openai-key-here
COINGECKO_API_KEY=your-coingecko-key-here  # Free tier available
```

**For Full AI Mining** (same as brainstorm engine):
```bash
# AI Models
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Crypto Data
COINGECKO_API_KEY=your-coingecko-key-here

# Stock Data  
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here

# Social Data
X_API_KEY=your-twitter-key-here
X_API_SECRET=your-twitter-secret-here
X_BEARER_TOKEN=your-twitter-bearer-here

# Search
GOOGLE_CUSTOM_SEARCH_API_KEY=your-google-key-here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-search-engine-id

# Commodities
METAL_PRICE_API_KEY=your-metals-key-here

# Sports
API_SPORTS_API_KEY=your-sports-key-here

# Economic Data
FRED_API_KEY=your-fred-key-here
```

### 3. Choose Your Strategy

Set your mining strategy in `.env`:

```bash
# Strategy options:
MINER_STRATEGY=hybrid        # Best accuracy (recommended)
MINER_STRATEGY=brainstorm    # Use brainstorm API directly  
MINER_STRATEGY=ai_reasoning  # Pure AI reasoning
MINER_STRATEGY=dummy         # Testing only
```

### 4. Run Your Miner

```bash
# Install dependencies
pip install -r requirements.txt

# Run the miner
python run_miner.py
```

## 📊 Strategy Comparison

| Strategy | Accuracy | Cost | Speed | Requirements |
|----------|----------|------|-------|--------------|
| `hybrid` | Highest | Medium | Medium | OpenAI + Data APIs |
| `brainstorm` | High | Low | Fast | None (uses our API) |
| `ai_reasoning` | High | High | Slow | OpenAI + All Data APIs |
| `dummy` | Low | Free | Fast | None |

## 💰 Cost Estimates

### OpenAI Costs
- **GPT-4o**: ~$0.03 per statement analysis
- **Daily cost**: $1-5 for active mining
- **Monthly cost**: $30-150 depending on activity

### Data API Costs
- **CoinGecko**: Free tier (50 calls/min) or $10/month
- **Alpha Vantage**: Free tier (25 calls/day) or $50/month  
- **Others**: Most have free tiers suitable for testing

### Total Estimated Costs
- **Hobby Miner**: $10-50/month
- **Professional Miner**: $100-500/month
- **Enterprise Miner**: $500+/month

## 🎯 Example Configurations

### Budget Setup ($10/month)
```bash
MINER_STRATEGY=brainstorm
OPENAI_API_KEY=your-key-here  # Backup only
COINGECKO_API_KEY=your-key-here  # Free tier
```

### Professional Setup ($100/month)
```bash
MINER_STRATEGY=hybrid
OPENAI_API_KEY=your-key-here
COINGECKO_API_KEY=your-key-here
ALPHA_VANTAGE_API_KEY=your-key-here
X_BEARER_TOKEN=your-token-here
```

### Enterprise Setup ($500+/month)
```bash
MINER_STRATEGY=ai_reasoning
# All API keys configured
# Multiple data sources
# Custom logic additions
```

## 🔧 How It Works

Your AI miner will:

1. **Receive statements** from validators via Bittensor
2. **Analyze statements** using OpenAI GPT-4o (same as brainstorm)
3. **Collect data** from the same APIs as brainstorm engine:
   - CoinGecko for crypto prices
   - Alpha Vantage for stock data  
   - Twitter API for social sentiment
   - Google Search for news/events
4. **Reason about outcomes** using AI
5. **Submit responses** back to validators
6. **Earn rewards** based on accuracy

## 📈 Performance Tips

### Maximize Accuracy
- Use `MINER_STRATEGY=hybrid` for best results
- Configure multiple data sources
- Set reasonable confidence levels
- Monitor your accuracy vs other miners

### Minimize Costs
- Start with `MINER_STRATEGY=brainstorm` 
- Use free API tiers initially
- Monitor API usage and costs
- Upgrade data sources based on performance

### Optimize Speed
- Set appropriate `REQUEST_TIMEOUT`
- Use async processing (already implemented)
- Cache common data when possible
- Monitor response times

## 🚨 Important Notes

### API Rate Limits
- OpenAI: 3,500 requests/minute (paid tier)
- CoinGecko: 50 calls/minute (free tier)
- Monitor your usage to avoid rate limiting

### Cost Management
- Start small and scale up
- Monitor API costs daily
- Set usage alerts where possible
- Consider API cost vs mining rewards

### Security
- Never commit `.env` file to git
- Use environment variables for all secrets
- Rotate API keys regularly
- Monitor for unauthorized usage

## 📞 Need Help?

- Check the logs: `tail -f logs/miner.log`
- Test API keys: `python -c "import os; print(os.getenv('OPENAI_API_KEY')[:10])"`
- Validate config: See agent initialization logs
- Join our Discord for miner support

Your AI miner now has the same reasoning capabilities as the centralized brainstorm engine! 🎉