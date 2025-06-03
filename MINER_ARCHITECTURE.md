# Miner Architecture Design

## Overview
The miner system provides a flexible framework where operators can run default agents out-of-the-box or implement custom verification strategies.

## Core Components

### 1. Base Agent Framework
```python
# miner/agents/base_agent.py
class BaseAgent:
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        """Override this method to implement verification logic"""
        raise NotImplementedError
```

### 2. Default Agents (Ready to Use)

#### API Agent
```python
# miner/agents/api_agent.py
class APIAgent(BaseAgent):
    """Uses multiple price APIs for verification"""
    
    data_sources = [
        CoinGeckoClient(),
        YahooFinanceClient(),
        AlphaVantageClient()
    ]
    
    async def verify_statement(self, statement):
        # Cross-reference multiple sources
        # Calculate confidence based on agreement
        # Return structured response
```

#### LLM Agent
```python
# miner/agents/llm_agent.py
class LLMAgent(BaseAgent):
    """Uses LLMs for complex statement analysis"""
    
    providers = {
        'openai': OpenAIClient(),
        'anthropic': AnthropicClient(),
        'local': LocalLLMClient()  # Ollama, etc.
    }
    
    async def verify_statement(self, statement):
        # Parse statement with LLM
        # Gather supporting evidence
        # Return reasoned response
```

#### Hybrid Agent (Default)
```python
# miner/agents/hybrid_agent.py
class HybridAgent(BaseAgent):
    """Combines API and LLM verification"""
    
    def __init__(self):
        self.api_agent = APIAgent()
        self.llm_agent = LLMAgent()
    
    async def verify_statement(self, statement):
        # Use APIs for price data
        # Use LLM for complex reasoning
        # Combine results with weights
```

### 3. Custom Agent Template
```python
# miner/agents/custom_template.py
class CustomAgent(BaseAgent):
    """Template for miners to implement their own logic"""
    
    async def verify_statement(self, statement):
        # Step 1: Parse the statement
        parsed = self.parse_statement(statement)
        
        # Step 2: Gather data from your sources
        data = await self.fetch_data(parsed)
        
        # Step 3: Apply your verification logic
        result = self.verify_logic(data, parsed)
        
        # Step 4: Build response
        return MinerResponse(
            statement=statement.statement,
            resolution=result.resolution,
            confidence=result.confidence,
            sources=result.sources,
            proof_hash=self.generate_proof(result)
        )
```

## Miner Configuration

### Default Setup (Zero Config)
```bash
# Just run with defaults
python miner/main.py
```

### Basic Configuration (.env)
```env
# Choose your agent
MINER_AGENT=hybrid  # api, llm, hybrid, custom

# API Keys (optional - uses free tiers by default)
COINGECKO_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Performance
VERIFICATION_TIMEOUT=30
CACHE_DURATION=300
```

### Advanced Configuration (config.yaml)
```yaml
agent:
  type: custom
  class: miner.agents.my_agent.MyCustomAgent
  
data_sources:
  - name: coingecko
    rate_limit: 10/min
    priority: 1
  - name: custom_api
    url: https://myapi.com
    auth: bearer_token
    
verification:
  min_sources: 2
  confidence_threshold: 0.7
  
logging:
  level: INFO
  wandb_project: my-miner
```

## Agent Development Guide

### For Basic Users
1. Install and run with defaults
2. Add API keys for better rate limits
3. Monitor performance via logs

### For Power Users
1. Copy `custom_template.py`
2. Implement your verification logic
3. Add custom data sources
4. Override confidence calculation
5. Deploy with your agent

### Example: Custom News-Based Agent
```python
class NewsAgent(BaseAgent):
    """Verifies statements using news sentiment"""
    
    def __init__(self):
        self.news_api = NewsAPIClient()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    async def verify_statement(self, statement):
        # Search for relevant news
        articles = await self.news_api.search(
            keywords=self.extract_keywords(statement),
            date_range=(statement.createdAt, statement.end_date)
        )
        
        # Analyze sentiment and relevance
        analysis = self.sentiment_analyzer.analyze(articles)
        
        # Determine if news supports/refutes statement
        resolution = self.evaluate_sentiment(analysis, statement)
        
        return MinerResponse(
            statement=statement.statement,
            resolution=resolution,
            confidence=analysis.confidence,
            sources=[a.url for a in articles[:5]],
            summary=f"Based on {len(articles)} news articles",
            proof_hash=self.hash_articles(articles)
        )
```

## Performance Optimizations

### Built-in Features
- Response caching (5 min default)
- Parallel API calls
- Rate limit management
- Automatic retries

### Optional Enhancements
- Redis caching
- Custom data pipelines
- ML model integration
- Historical data storage

## Testing Your Agent

```python
# test_my_agent.py
async def test_custom_agent():
    agent = MyCustomAgent()
    
    # Test with sample statement
    statement = Statement(
        statement="Bitcoin will cross $100,000 by December 31, 2024",
        end_date="2024-12-31T23:59:00Z",
        createdAt="2023-01-15T12:00:00Z",
        initialValue=21500.75
    )
    
    response = await agent.verify_statement(statement)
    
    # Validate response format
    assert response.resolution in ["TRUE", "FALSE", "PENDING"]
    assert 0 <= response.confidence <= 100
    assert len(response.sources) > 0
```

## Deployment Options

### 1. Simple (Single Agent)
```bash
python miner/main.py --agent hybrid
```

### 2. Docker
```bash
docker run -e MINER_AGENT=hybrid degenbrain/miner:latest
```

### 3. Kubernetes (Multi-Agent Pool)
```yaml
replicas: 3
env:
  - name: MINER_AGENT
    value: "hybrid"
  - name: AGENT_VARIANT
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
```

## Monitoring & Debugging

### Default Metrics
- Statements processed/hour
- Average confidence score
- API call success rate
- Response time percentiles

### Debug Mode
```bash
python miner/main.py --debug --test-statement "BTC > 100k"
```

This will:
1. Run verification once
2. Show detailed logs
3. Display all API calls
4. Explain confidence calculation