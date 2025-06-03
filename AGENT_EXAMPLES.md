# Agent Implementation Examples

## API Agent Example

```python
# miner/agents/api_agent.py
import asyncio
from typing import List, Dict
from datetime import datetime

class APIAgent(BaseAgent):
    """Verifies statements using multiple financial APIs"""
    
    def __init__(self):
        self.sources = {
            'coingecko': CoinGeckoClient(),
            'yahoo': YahooFinanceClient(),
            'alphaavantage': AlphaVantageClient()
        }
        
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        # Extract ticker and target from statement
        parsed = self.parse_statement(statement.statement)
        # E.g., {"asset": "Bitcoin", "ticker": "BTC", "target": 100000, "comparison": ">"}
        
        # Fetch current/historical prices from multiple sources
        price_data = await self.fetch_prices(parsed.ticker, statement.end_date)
        
        # Determine resolution
        resolution = self.evaluate_prices(price_data, parsed, statement.end_date)
        
        # Calculate confidence based on source agreement
        confidence = self.calculate_confidence(price_data)
        
        return MinerResponse(
            statement=statement.statement,
            resolution=resolution,
            confidence=confidence,
            summary=f"BTC reached ${max(price_data.values())} based on {len(price_data)} sources",
            sources=list(price_data.keys()),
            target_date=statement.end_date,
            target_value=parsed.target,
            current_value=max(price_data.values()),
            direction_inferred=parsed.comparison,
            proof_hash=self.generate_hash(price_data)
        )
    
    async def fetch_prices(self, ticker: str, end_date: str) -> Dict[str, float]:
        """Fetch prices from all sources in parallel"""
        tasks = []
        for name, client in self.sources.items():
            tasks.append(self.fetch_with_fallback(name, client, ticker, end_date))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {k: v for k, v in results if v is not None}
```

## LLM Agent Example

```python
# miner/agents/llm_agent.py
class LLMAgent(BaseAgent):
    """Uses LLMs to understand and verify complex statements"""
    
    def __init__(self):
        self.llm_providers = {
            'primary': OpenAIClient(model="gpt-4"),
            'fallback': AnthropicClient(model="claude-3")
        }
        
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        # Step 1: Parse statement with LLM
        parse_prompt = f"""
        Parse this prediction statement and extract:
        - What is being predicted
        - Target values/conditions
        - Any implicit assumptions
        
        Statement: {statement.statement}
        Created: {statement.createdAt}
        Deadline: {statement.end_date}
        """
        
        parsed = await self.llm_call(parse_prompt)
        
        # Step 2: Gather evidence
        evidence_prompt = f"""
        Find evidence to verify: {statement.statement}
        
        Search for:
        - Current values
        - Historical trends
        - Recent news/events
        - Expert predictions
        
        Return sources and confidence level.
        """
        
        evidence = await self.llm_call(evidence_prompt)
        
        # Step 3: Make determination
        verdict_prompt = f"""
        Based on the evidence, determine if this statement is TRUE, FALSE, or PENDING:
        
        Statement: {statement.statement}
        Evidence: {evidence}
        Current date: {datetime.now()}
        Deadline: {statement.end_date}
        
        Provide reasoning and confidence (0-100).
        """
        
        verdict = await self.llm_call(verdict_prompt)
        
        return MinerResponse(
            statement=statement.statement,
            resolution=verdict.resolution,
            confidence=verdict.confidence,
            summary=verdict.reasoning,
            sources=evidence.sources,
            proof_hash=self.hash_llm_interaction(parsed, evidence, verdict)
        )
```

## Hybrid Agent Example (Default)

```python
# miner/agents/hybrid_agent.py
class HybridAgent(BaseAgent):
    """Combines API data with LLM reasoning for best results"""
    
    def __init__(self):
        self.api_agent = APIAgent()
        self.llm_agent = LLMAgent()
        
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        # Run both agents in parallel
        api_task = asyncio.create_task(
            self.api_agent.verify_statement(statement)
        )
        llm_task = asyncio.create_task(
            self.llm_agent.verify_statement(statement)
        )
        
        api_response, llm_response = await asyncio.gather(api_task, llm_task)
        
        # Combine results intelligently
        if api_response.resolution == llm_response.resolution:
            # Both agree - high confidence
            final_confidence = (api_response.confidence + llm_response.confidence) / 2
            final_resolution = api_response.resolution
        else:
            # Disagreement - need to resolve
            if api_response.confidence > llm_response.confidence:
                final_resolution = api_response.resolution
                final_confidence = api_response.confidence * 0.8  # Reduce due to disagreement
            else:
                final_resolution = llm_response.resolution
                final_confidence = llm_response.confidence * 0.8
        
        # Merge sources and summaries
        all_sources = list(set(api_response.sources + llm_response.sources))
        combined_summary = f"API: {api_response.summary} | LLM: {llm_response.summary}"
        
        return MinerResponse(
            statement=statement.statement,
            resolution=final_resolution,
            confidence=final_confidence,
            summary=combined_summary,
            sources=all_sources[:5],  # Top 5 sources
            target_date=statement.end_date,
            target_value=api_response.target_value,
            current_value=api_response.current_value,
            proof_hash=self.hash_combined(api_response, llm_response)
        )
```

## Running Different Agents

### Out-of-the-box (Hybrid Default)
```bash
# No configuration needed
python miner/main.py
```

### API-Only Mode
```bash
# For miners who trust data sources
python miner/main.py --agent api

# Or in .env
MINER_AGENT=api
```

### LLM-Only Mode
```bash
# For complex/subjective statements
python miner/main.py --agent llm

# Requires API keys in .env
OPENAI_API_KEY=sk-...
```

### Custom Agent
```bash
# Point to your implementation
python miner/main.py --agent custom --agent-class miner.agents.my_agent.MyAgent
```

## Example Verification Flow

### Statement: "Bitcoin will cross $100,000 by December 31, 2024"

1. **API Agent Process:**
   - Queries CoinGecko: BTC = $98,000 on Dec 31
   - Queries Yahoo: BTC = $97,850 on Dec 31
   - Queries AlphaVantage: BTC = $98,200 on Dec 31
   - Resolution: FALSE (didn't cross $100k)
   - Confidence: 95% (all sources agree)

2. **LLM Agent Process:**
   - Parses: "Bitcoin price > $100,000 by deadline"
   - Searches: Finds news about BTC rally stopping at $98k
   - Analyzes: Market resistance at $100k psychological barrier
   - Resolution: FALSE
   - Confidence: 88% (based on analysis)

3. **Hybrid Result:**
   - Both agree: FALSE
   - Final confidence: 91.5%
   - Sources: ["CoinGecko", "Yahoo Finance", "AlphaVantage", "Reuters", "CoinDesk"]
   - Summary: "BTC peaked at $98,200 on Dec 31. API data and news analysis confirm it did not reach $100,000 target."