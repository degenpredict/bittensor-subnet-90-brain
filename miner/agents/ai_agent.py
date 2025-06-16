"""
AI-powered agent for statement verification using multiple AI models and data sources.
"""
import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import aiohttp
import structlog

from miner.agents.base_agent import BaseAgent
from shared.types import Statement, MinerResponse, Resolution


logger = structlog.get_logger()


class AIAgent(BaseAgent):
    """
    AI-powered agent that uses multiple approaches to verify statements:
    
    1. **Direct API Integration**: Connect to brainstorm/degenbrain resolve endpoint
    2. **Multi-Model AI**: Use OpenAI, Anthropic, or local models for reasoning
    3. **Data Collection**: Fetch real-time data from APIs (CoinGecko, Alpha Vantage, etc.)
    4. **Ensemble Methods**: Combine multiple approaches for better accuracy
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # AI Model Configuration
        self.openai_api_key = config.get("openai_api_key")
        self.anthropic_api_key = config.get("anthropic_api_key")
        self.use_brainstorm = config.get("use_brainstorm", True)
        self.brainstorm_url = config.get("brainstorm_url", "https://degenbrain-459147590380.us-central1.run.app")
        
        # Data Source Configuration
        self.coingecko_api_key = config.get("coingecko_api_key")
        self.alpha_vantage_api_key = config.get("alpha_vantage_api_key")
        
        # Strategy Configuration
        self.strategy = config.get("strategy", "hybrid")  # "brainstorm", "ai_reasoning", "hybrid"
        self.timeout = config.get("timeout", 30)
        
        logger.info("AI Agent initialized", 
                   strategy=self.strategy,
                   has_openai=bool(self.openai_api_key),
                   has_anthropic=bool(self.anthropic_api_key),
                   use_brainstorm=self.use_brainstorm)
    
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        """
        Main verification method using AI and data sources.
        """
        logger.info("Starting AI verification", 
                   statement=statement.statement[:60] + "...",
                   strategy=self.strategy)
        
        try:
            if self.strategy == "brainstorm":
                return await self._verify_with_brainstorm(statement)
            elif self.strategy == "ai_reasoning":
                return await self._verify_with_ai_reasoning(statement)
            elif self.strategy == "hybrid":
                return await self._verify_hybrid(statement)
            else:
                logger.warning("Unknown strategy, falling back to hybrid", strategy=self.strategy)
                return await self._verify_hybrid(statement)
                
        except Exception as e:
            logger.error("AI verification failed", error=str(e))
            return self._create_error_response(statement, str(e))
    
    async def _verify_with_brainstorm(self, statement: Statement) -> MinerResponse:
        """
        Use the brainstorm/degenbrain resolve endpoint directly.
        
        This is essentially using the same system as the official validator,
        but miners can use it independently for their own analysis.
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                payload = {
                    "statement": statement.statement,
                    "end_date": statement.end_date,
                    "createdAt": statement.createdAt,
                    "initialValue": statement.initialValue,
                    "direction": statement.direction
                }
                
                async with session.post(f"{self.brainstorm_url}/resolve", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._convert_brainstorm_response(statement, result)
                    else:
                        logger.warning("Brainstorm API error", status=response.status)
                        return await self._verify_with_ai_reasoning(statement)  # Fallback
                        
        except Exception as e:
            logger.error("Brainstorm verification failed", error=str(e))
            return await self._verify_with_ai_reasoning(statement)  # Fallback
    
    async def _verify_with_ai_reasoning(self, statement: Statement) -> MinerResponse:
        """
        Use AI models (OpenAI/Anthropic) for reasoning about the statement.
        
        This approach:
        1. Analyzes the statement context
        2. Identifies what data is needed
        3. Fetches relevant data from APIs
        4. Uses AI to reason about the outcome
        """
        # Step 1: Analyze statement to understand what we need
        analysis = await self._analyze_statement(statement)
        
        # Step 2: Collect relevant data
        data = await self._collect_data(analysis)
        
        # Step 3: Use AI to reason about the outcome
        reasoning_result = await self._ai_reasoning(statement, analysis, data)
        
        return reasoning_result
    
    async def _verify_hybrid(self, statement: Statement) -> MinerResponse:
        """
        Hybrid approach: Try brainstorm first, then AI reasoning, then ensemble.
        """
        results = []
        
        # Try brainstorm approach
        try:
            brainstorm_result = await self._verify_with_brainstorm(statement)
            results.append(("brainstorm", brainstorm_result))
        except:
            pass
        
        # Try AI reasoning approach
        try:
            ai_result = await self._verify_with_ai_reasoning(statement)
            results.append(("ai_reasoning", ai_result))
        except:
            pass
        
        # If we have multiple results, ensemble them
        if len(results) > 1:
            return self._ensemble_results(statement, results)
        elif len(results) == 1:
            return results[0][1]
        else:
            return self._create_error_response(statement, "All verification methods failed")
    
    async def _analyze_statement(self, statement: Statement) -> Dict[str, Any]:
        """
        Use AI to analyze what the statement is asking and what data we need.
        """
        analysis_prompt = f"""
        Analyze this prediction statement and identify:
        1. What type of prediction is this? (price, event, date-based, etc.)
        2. What specific data sources would be needed to verify it?
        3. What is the target value/condition?
        4. What is the deadline?
        
        Statement: {statement.statement}
        End Date: {statement.end_date}
        Initial Value: {statement.initialValue}
        Direction: {statement.direction}
        
        Return your analysis in JSON format:
        {{
            "prediction_type": "...",
            "asset_symbol": "...",
            "target_value": ...,
            "deadline": "...",
            "data_sources_needed": [...],
            "verification_strategy": "..."
        }}
        """
        
        if self.openai_api_key:
            return await self._call_openai(analysis_prompt, response_format="json")
        else:
            # Fallback to pattern matching
            return self._pattern_based_analysis(statement)
    
    async def _collect_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect relevant data based on the analysis.
        """
        data = {}
        
        # Crypto price data
        if analysis.get("prediction_type") == "crypto_price":
            symbol = analysis.get("asset_symbol")
            if symbol:
                data["price_data"] = await self._get_crypto_price(symbol)
        
        # Stock price data
        elif analysis.get("prediction_type") == "stock_price":
            symbol = analysis.get("asset_symbol")
            if symbol:
                data["price_data"] = await self._get_stock_price(symbol)
        
        # Add more data sources as needed
        # data["news_sentiment"] = await self._get_news_sentiment(analysis)
        # data["market_indicators"] = await self._get_market_indicators(analysis)
        
        return data
    
    async def _ai_reasoning(self, statement: Statement, analysis: Dict, data: Dict) -> MinerResponse:
        """
        Use AI to reason about the statement given the analysis and data.
        """
        reasoning_prompt = f"""
        You are a financial prediction verification expert. Based on the data provided, determine if this prediction statement is TRUE, FALSE, or PENDING.
        
        Statement: {statement.statement}
        End Date: {statement.end_date}
        
        Analysis: {json.dumps(analysis, indent=2)}
        Collected Data: {json.dumps(data, indent=2)}
        
        Current Date: {datetime.now(timezone.utc).isoformat()}
        
        Consider:
        1. Has the deadline passed?
        2. If yes, did the condition specified in the statement occur?
        3. What is your confidence level (0-100)?
        4. What sources support your conclusion?
        
        Respond in JSON format:
        {{
            "resolution": "TRUE|FALSE|PENDING",
            "confidence": 85,
            "summary": "Detailed explanation of your reasoning...",
            "sources": ["source1", "source2"],
            "key_evidence": "What evidence supports this conclusion"
        }}
        """
        
        if self.openai_api_key:
            ai_response = await self._call_openai(reasoning_prompt, response_format="json")
        else:
            # Fallback to basic logic
            ai_response = self._basic_reasoning(statement, analysis, data)
        
        return self._convert_ai_response(statement, ai_response)
    
    async def _call_openai(self, prompt: str, response_format: str = "text") -> Any:
        """Call OpenAI API for reasoning."""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided, using fallback")
            return {
                "resolution": "PENDING",
                "confidence": 30,
                "summary": "OpenAI API key not configured",
                "sources": ["config_error"],
                "key_evidence": "No OpenAI API key available"
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial prediction verification expert. Analyze statements accurately and provide structured responses in the requested JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent responses
                "max_tokens": 1000
            }
            
            if response_format == "json":
                payload["response_format"] = {"type": "json_object"}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post("https://api.openai.com/v1/chat/completions", 
                                      headers=headers, 
                                      json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        if response_format == "json":
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                logger.error("Failed to parse OpenAI JSON response", content=content)
                                return {"error": "Invalid JSON response from OpenAI"}
                        else:
                            return content
                    else:
                        error_text = await response.text()
                        logger.error("OpenAI API error", status=response.status, error=error_text)
                        return {"error": f"OpenAI API error: {response.status}"}
                        
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            return {"error": f"OpenAI API call failed: {str(e)}"}
    
    async def _get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Get cryptocurrency price data."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error("Failed to get crypto price", symbol=symbol, error=str(e))
        
        return {}
    
    async def _get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get stock price data."""
        # Implementation would use Alpha Vantage or similar
        return {}
    
    def _pattern_based_analysis(self, statement: Statement) -> Dict[str, Any]:
        """Fallback analysis using pattern matching."""
        statement_text = statement.statement.lower()
        
        # Bitcoin pattern
        if "bitcoin" in statement_text or "btc" in statement_text:
            target_match = re.search(r'\$([0-9,]+)', statement.statement)
            target_value = float(target_match.group(1).replace(',', '')) if target_match else None
            
            return {
                "prediction_type": "crypto_price",
                "asset_symbol": "bitcoin",
                "target_value": target_value,
                "deadline": statement.end_date,
                "data_sources_needed": ["coingecko", "binance"],
                "verification_strategy": "price_comparison"
            }
        
        # Generic fallback
        return {
            "prediction_type": "unknown",
            "verification_strategy": "date_based"
        }
    
    def _basic_reasoning(self, statement: Statement, analysis: Dict, data: Dict) -> Dict[str, Any]:
        """Basic reasoning fallback when AI is not available."""
        # Check if deadline has passed
        try:
            end_date = datetime.fromisoformat(statement.end_date.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if end_date > now:
                return {
                    "resolution": "PENDING",
                    "confidence": 95,
                    "summary": "Deadline has not yet passed",
                    "sources": ["system_clock"],
                    "key_evidence": f"Current time: {now}, Deadline: {end_date}"
                }
            else:
                # For past deadlines, we'd need to check actual data
                # This is a simplified version
                return {
                    "resolution": "FALSE",  # Conservative default
                    "confidence": 30,
                    "summary": "Deadline passed, but insufficient data for verification",
                    "sources": ["basic_analysis"],
                    "key_evidence": "Limited verification capability without AI"
                }
        except:
            return {
                "resolution": "PENDING",
                "confidence": 0,
                "summary": "Error parsing deadline",
                "sources": ["error"],
                "key_evidence": "Could not parse end_date"
            }
    
    def _convert_brainstorm_response(self, statement: Statement, result: Dict) -> MinerResponse:
        """Convert brainstorm API response to MinerResponse format."""
        return MinerResponse(
            statement=statement.statement,
            resolution=Resolution(result.get("resolution", "PENDING")),
            confidence=result.get("confidence", 50),
            summary=result.get("summary", "Brainstorm API response"),
            sources=result.get("sources", ["brainstorm"]),
            target_value=result.get("target_value"),
            current_value=result.get("current_value"),
            reasoning=f"Brainstorm analysis: {result.get('summary', '')}"
        )
    
    def _convert_ai_response(self, statement: Statement, ai_result: Dict) -> MinerResponse:
        """Convert AI reasoning response to MinerResponse format."""
        return MinerResponse(
            statement=statement.statement,
            resolution=Resolution(ai_result.get("resolution", "PENDING")),
            confidence=ai_result.get("confidence", 50),
            summary=ai_result.get("summary", "AI analysis"),
            sources=ai_result.get("sources", ["ai_reasoning"]),
            reasoning=ai_result.get("key_evidence", "AI-powered analysis")
        )
    
    def _ensemble_results(self, statement: Statement, results: List) -> MinerResponse:
        """Combine multiple results using ensemble methods."""
        # Simple ensemble: average confidence, majority vote on resolution
        resolutions = [result[1].resolution for result in results]
        confidences = [result[1].confidence for result in results]
        summaries = [f"{result[0]}: {result[1].summary}" for result in results]
        sources = []
        for result in results:
            sources.extend(result[1].sources)
        
        # Majority vote
        from collections import Counter
        resolution_counts = Counter(resolutions)
        final_resolution = resolution_counts.most_common(1)[0][0]
        
        # Average confidence
        final_confidence = sum(confidences) / len(confidences)
        
        return MinerResponse(
            statement=statement.statement,
            resolution=final_resolution,
            confidence=final_confidence,
            summary=f"Ensemble result from {len(results)} methods: " + "; ".join(summaries),
            sources=list(set(sources)),
            reasoning=f"Combined analysis from {len(results)} verification methods"
        )
    
    def _create_error_response(self, statement: Statement, error: str) -> MinerResponse:
        """Create error response when verification fails."""
        return MinerResponse(
            statement=statement.statement,
            resolution=Resolution.PENDING,
            confidence=0,
            summary=f"Verification failed: {error}",
            sources=["error"],
            reasoning=f"Error during AI verification: {error}"
        )