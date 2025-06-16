"""
Fair, community-friendly weight calculation for Bittensor Subnet 90.

This module implements weight strategies that:
1. Give all miners equal opportunity
2. Base weights purely on performance 
3. Avoid any appearance of favoritism
4. Promote decentralization
"""
import asyncio
from typing import Dict, List, Optional
from collections import defaultdict
import numpy as np
import structlog

from shared.types import MinerResponse, Resolution


logger = structlog.get_logger()


class FairWeightsCalculator:
    """
    Calculates weights based purely on merit and performance.
    No pre-determined favorites or static allocations.
    """
    
    def __init__(self, min_responses_for_scoring: int = 3):
        """
        Initialize fair weights calculator.
        
        Args:
            min_responses_for_scoring: Minimum responses needed before scoring a miner
        """
        self.min_responses_for_scoring = min_responses_for_scoring
        self.miner_history = defaultdict(list)
        self.official_resolutions = {}  # From brain-api
        self.response_times = defaultdict(list)
        
    def record_miner_response(self, miner_uid: int, response: MinerResponse, response_time: float):
        """Record a miner response for later scoring."""
        self.miner_history[miner_uid].append(response)
        self.response_times[miner_uid].append(response_time)
        
    def record_official_resolution(self, statement_id: str, official_resolution: str):
        """Record official resolution from brain-api."""
        self.official_resolutions[statement_id] = official_resolution
        
    async def calculate_fair_weights(self) -> Dict[int, float]:
        """
        Calculate weights based purely on performance metrics.
        
        Returns:
            Dictionary mapping miner UIDs to normalized weights.
        """
        logger.info("Calculating fair weights based on performance")
        
        scores = {}
        miners_with_enough_data = []
        
        # Calculate performance scores for miners with sufficient data
        for miner_uid, responses in self.miner_history.items():
            if len(responses) >= self.min_responses_for_scoring:
                score = self._calculate_miner_performance(miner_uid, responses)
                scores[miner_uid] = score
                miners_with_enough_data.append(miner_uid)
                
        # If we don't have enough performance data, use equal weights for responders
        if len(miners_with_enough_data) < 3:
            logger.info("Insufficient performance data, using equal weights for responding miners")
            return self._calculate_equal_weights_for_responders()
            
        # Normalize and return performance-based weights
        logger.info("Using performance-based weights", 
                   miners_scored=len(scores),
                   total_responses=sum(len(responses) for responses in self.miner_history.values()))
        
        return self._normalize_weights(scores)
    
    def _calculate_miner_performance(self, miner_uid: int, responses: List[MinerResponse]) -> float:
        """
        Calculate performance score for a single miner.
        
        Scoring criteria:
        1. Accuracy vs official brain-api resolutions (60%)
        2. Confidence calibration quality (25%)
        3. Response consistency and quality (15%)
        """
        accuracy_score = self._calculate_accuracy_score(responses)
        confidence_score = self._calculate_confidence_score(responses)
        quality_score = self._calculate_quality_score(responses)
        
        total_score = (
            accuracy_score * 0.60 +
            confidence_score * 0.25 +
            quality_score * 0.15
        )
        
        logger.debug("Calculated miner performance",
                    miner_uid=miner_uid,
                    accuracy=accuracy_score,
                    confidence=confidence_score,
                    quality=quality_score,
                    total=total_score)
        
        return total_score
    
    def _calculate_accuracy_score(self, responses: List[MinerResponse]) -> float:
        """Calculate accuracy vs official brain-api resolutions."""
        if not responses:
            return 0.0
            
        correct = 0
        total = 0
        
        for response in responses:
            # Check if we have official resolution for this statement
            statement_key = self._get_statement_key(response)
            if statement_key in self.official_resolutions:
                official_resolution = self.official_resolutions[statement_key]
                if response.resolution.value == official_resolution:
                    correct += 1
                total += 1
        
        if total == 0:
            return 0.5  # Neutral score if no official resolutions available yet
            
        accuracy = correct / total
        logger.debug("Accuracy calculation", correct=correct, total=total, accuracy=accuracy)
        return accuracy
    
    def _calculate_confidence_score(self, responses: List[MinerResponse]) -> float:
        """
        Calculate confidence calibration score.
        
        Good confidence means:
        - High confidence for correct answers
        - Low confidence for incorrect answers  
        - Moderate confidence for uncertain cases
        """
        if not responses:
            return 0.0
            
        calibration_scores = []
        
        for response in responses:
            statement_key = self._get_statement_key(response)
            if statement_key in self.official_resolutions:
                official_resolution = self.official_resolutions[statement_key]
                confidence = response.confidence / 100.0
                
                if response.resolution.value == official_resolution:
                    # Correct answer - reward high confidence
                    calibration_scores.append(confidence)
                elif response.resolution == Resolution.PENDING:
                    # Pending - moderate confidence is good
                    ideal_confidence = 0.5
                    distance = abs(confidence - ideal_confidence)
                    calibration_scores.append(1.0 - distance)
                else:
                    # Wrong answer - reward low confidence
                    calibration_scores.append(1.0 - confidence)
        
        if not calibration_scores:
            return 0.5  # Neutral score
            
        return np.mean(calibration_scores)
    
    def _calculate_quality_score(self, responses: List[MinerResponse]) -> float:
        """
        Calculate overall response quality score.
        
        Factors:
        - Response completeness (has summary, sources)
        - Source diversity and quality
        - Reasoning clarity
        """
        if not responses:
            return 0.0
            
        quality_scores = []
        
        for response in responses:
            score = 0.0
            
            # Check for summary quality
            if response.summary and len(response.summary.strip()) > 10:
                score += 0.4
                
            # Check for sources
            if response.sources and len(response.sources) > 0:
                score += 0.3
                # Bonus for multiple diverse sources
                if len(response.sources) >= 2:
                    score += 0.2
                    
            # Reasonable confidence bounds
            if 10 <= response.confidence <= 95:
                score += 0.1
                
            quality_scores.append(score)
        
        return np.mean(quality_scores) if quality_scores else 0.0
    
    def _calculate_equal_weights_for_responders(self) -> Dict[int, float]:
        """Give equal weights to all miners who are responding."""
        responding_miners = [
            uid for uid, responses in self.miner_history.items() 
            if len(responses) > 0
        ]
        
        if not responding_miners:
            return {}
            
        equal_weight = 1.0 / len(responding_miners)
        weights = {uid: equal_weight for uid in responding_miners}
        
        logger.info("Using equal weights for early phase",
                   miners=len(responding_miners),
                   weight_per_miner=equal_weight)
        
        return weights
    
    def _normalize_weights(self, scores: Dict[int, float]) -> Dict[int, float]:
        """Normalize scores to sum to 1.0."""
        if not scores:
            return {}
            
        total_score = sum(scores.values())
        if total_score == 0:
            # All zeros - give equal weights
            equal_weight = 1.0 / len(scores)
            return {uid: equal_weight for uid in scores.keys()}
            
        normalized = {uid: score / total_score for uid, score in scores.items()}
        
        logger.debug("Normalized weights", 
                    total_miners=len(normalized),
                    weight_distribution=normalized)
        
        return normalized
    
    def _get_statement_key(self, response: MinerResponse) -> str:
        """Generate a key to match responses with official resolutions."""
        # Use statement text hash or ID if available
        return response.statement[:100]  # First 100 chars as key
    
    def get_performance_summary(self) -> Dict:
        """Get summary of current performance tracking."""
        return {
            "total_miners_tracked": len(self.miner_history),
            "total_responses": sum(len(responses) for responses in self.miner_history.values()),
            "miners_with_sufficient_data": len([
                uid for uid, responses in self.miner_history.items()
                if len(responses) >= self.min_responses_for_scoring
            ]),
            "official_resolutions_available": len(self.official_resolutions)
        }