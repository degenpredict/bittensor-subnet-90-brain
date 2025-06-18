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
from miner.agents.resolution_api_client import ResolutionAPIClient
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
        self.strategy = config.get("strategy", "ai_reasoning")  # "ai_reasoning", "hybrid", or "dummy"
        self.timeout = config.get("timeout", 30)
        
        # Resolution API Configuration
        self.api_url = config.get("api_url", "https://api.subnet90.com")
        self.resolution_client = ResolutionAPIClient(self.api_url, timeout=10)
        
        logger.info("AI Agent initialized", 
                   strategy=self.strategy,
                   has_openai=bool(self.openai_api_key),
                   has_anthropic=bool(self.anthropic_api_key),
                   use_brainstorm=self.use_brainstorm)
    
    async def verify_statement(self, statement_or_synapse) -> MinerResponse:
        """
        Main verification method using AI and data sources.
        """
        # Handle both Statement objects and synapse objects
        if hasattr(statement_or_synapse, 'statement'):
            # This is a synapse object
            statement_text = statement_or_synapse.statement
            statement_id = getattr(statement_or_synapse, 'statement_id', None)
            statement = Statement(
                statement=statement_or_synapse.statement,
                end_date=statement_or_synapse.end_date,
                createdAt=getattr(statement_or_synapse, 'created_at', ''),
                id=statement_id
            )
        else:
            # This is a Statement object
            statement = statement_or_synapse
            statement_text = statement.statement
            statement_id = statement.id
        
        logger.info("Starting AI verification", 
                   statement=statement_text[:60] + "...",
                   strategy=self.strategy,
                   statement_id=statement_id)
        
        try:
            if self.strategy == "ai_reasoning":
                # Check if AI keys are configured
                if not self.openai_api_key and not self.anthropic_api_key:
                    logger.warning("AI reasoning requested but no API keys configured")
                    return self._create_basic_pending_response(statement)
                return await self._verify_with_ai_reasoning(statement)
            elif self.strategy == "hybrid":
                return await self._verify_hybrid(statement, statement_id)
            else:
                logger.warning("Unknown strategy, falling back to ai_reasoning", strategy=self.strategy)
                if not self.openai_api_key and not self.anthropic_api_key:
                    return self._create_basic_pending_response(statement)
                return await self._verify_with_ai_reasoning(statement)
                
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
                    "createdAt": statement.createdAt
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
    
    async def _verify_with_resolution_api(self, statement: Statement, statement_id: str) -> Optional[MinerResponse]:
        """
        Use the resolution API to get the official resolution for a statement.
        
        Args:
            statement: Statement to verify
            statement_id: ID of the statement
            
        Returns:
            MinerResponse if resolution found, None otherwise
        """
        try:
            async with self.resolution_client as client:
                api_response = await client.get_resolution(statement_id)
                
                if api_response:
                    # Convert API response to MinerResponse format
                    response_data = client.convert_to_miner_response(api_response, statement.statement)
                    
                    return MinerResponse(
                        statement=response_data["statement"],
                        resolution=Resolution(response_data["resolution"]),
                        confidence=response_data["confidence"],
                        summary=response_data["summary"],
                        sources=response_data["sources"],
                        reasoning=response_data["reasoning"],
                        target_value=response_data.get("target_value"),
                        current_value=response_data.get("current_value")
                    )
                    
        except Exception as e:
            logger.error("Resolution API verification failed", 
                        statement_id=statement_id, 
                        error=str(e))
        
        return None
    
    async def _verify_hybrid(self, statement: Statement, statement_id: Optional[str] = None) -> MinerResponse:
        """
        Hybrid approach: Try resolution API first, then AI reasoning, then ensemble.
        """
        results = []
        
        # First, try the resolution API if we have a statement ID
        if statement_id:
            try:
                api_result = await self._verify_with_resolution_api(statement, statement_id)
                if api_result:
                    results.append(("resolution_api", api_result))
                    logger.info("Resolution found in API", statement_id=statement_id)
            except Exception as e:
                logger.debug("Resolution API failed", statement_id=statement_id, error=str(e))
        
        # Try AI reasoning approach (if API keys are configured)
        if self.openai_api_key or self.anthropic_api_key:
            try:
                ai_result = await self._verify_with_ai_reasoning(statement)
                results.append(("ai_reasoning", ai_result))
            except Exception as e:
                logger.debug("AI reasoning failed", error=str(e))
        else:
            logger.info("No AI API keys configured, skipping AI reasoning")
        
        # If we have multiple results, ensemble them
        if len(results) > 1:
            return self._ensemble_results(statement, results)
        elif len(results) == 1:
            return results[0][1]
        else:
            # If no AI keys are configured and no resolution found, provide a basic response
            if not self.openai_api_key and not self.anthropic_api_key:
                return self._create_basic_pending_response(statement)
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
    
    def _create_basic_pending_response(self, statement: Statement) -> MinerResponse:
        """Create a basic pending response when no AI keys are configured."""
        return MinerResponse(
            statement=statement.statement,
            resolution=Resolution.PENDING,
            confidence=50,
            summary="No AI configuration available, unable to verify independently",
            sources=["basic_analysis"],
            reasoning="This miner requires resolution API data or AI API keys to provide accurate verification"
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