"""
Weights calculation and scoring logic for validators.
"""
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np
import structlog

from shared.types import Statement, MinerResponse, Resolution, ValidationResult


logger = structlog.get_logger()


class WeightsCalculator:
    """
    Calculates miner weights based on response accuracy and quality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize weights calculator.
        
        Config options:
            - accuracy_weight: Weight for accuracy in scoring (0-1)
            - confidence_weight: Weight for confidence in scoring (0-1)
            - consistency_weight: Weight for consistency with consensus (0-1)
            - source_quality_weight: Weight for source quality (0-1)
        """
        config = config or {}
        self.accuracy_weight = config.get("accuracy_weight", 0.4)
        self.confidence_weight = config.get("confidence_weight", 0.2)
        self.consistency_weight = config.get("consistency_weight", 0.3)
        self.source_quality_weight = config.get("source_quality_weight", 0.1)
        
        # Normalize weights
        total_weight = (self.accuracy_weight + self.confidence_weight + 
                       self.consistency_weight + self.source_quality_weight)
        if total_weight > 0:
            self.accuracy_weight /= total_weight
            self.confidence_weight /= total_weight
            self.consistency_weight /= total_weight
            self.source_quality_weight /= total_weight
        
        # Track accumulated miner scores for weight setting
        self.accumulated_scores = defaultdict(list)
    
    def calculate_scores(
        self,
        statement: Statement,
        responses: List[MinerResponse],
        ground_truth: Optional[Resolution] = None
    ) -> Dict[int, float]:
        """
        Calculate scores for each miner based on their responses.
        
        Args:
            statement: The statement being evaluated
            responses: List of miner responses
            ground_truth: Known correct answer (if available)
            
        Returns:
            Dictionary mapping miner UID to score (0-1)
        """
        if not responses:
            return {}
        
        # Calculate consensus if ground truth not available
        consensus = ground_truth or self._calculate_consensus(responses)
        
        # Calculate individual scores
        scores = {}
        for response in responses:
            if response.miner_uid is not None:
                score = self._score_response(response, consensus, responses)
                scores[response.miner_uid] = score
        
        # Normalize scores
        scores = self._normalize_scores(scores)
        
        logger.info("Calculated miner scores",
                   num_miners=len(scores),
                   consensus=consensus.value if consensus else None)
        
        return scores
    
    def _calculate_consensus(self, responses: List[MinerResponse]) -> Optional[Resolution]:
        """
        Calculate consensus resolution from miner responses.
        
        Uses confidence-weighted voting.
        """
        if not responses:
            return None
        
        # Count votes weighted by confidence
        vote_weights = defaultdict(float)
        
        for response in responses:
            weight = response.confidence / 100.0
            vote_weights[response.resolution] += weight
        
        # Find resolution with highest weight
        if vote_weights:
            consensus = max(vote_weights.items(), key=lambda x: x[1])[0]
            return consensus
        
        return None
    
    def _score_response(
        self,
        response: MinerResponse,
        consensus: Optional[Resolution],
        all_responses: List[MinerResponse]
    ) -> float:
        """
        Score an individual response.
        
        Components:
        1. Accuracy: How close to consensus/truth
        2. Confidence: Appropriate confidence level
        3. Consistency: Agreement with other high-quality responses
        4. Source Quality: Quality and diversity of sources
        """
        scores = []
        
        # 1. Accuracy score
        accuracy_score = self._calculate_accuracy_score(response, consensus)
        scores.append(accuracy_score * self.accuracy_weight)
        
        # 2. Confidence score
        confidence_score = self._calculate_confidence_score(response, consensus)
        scores.append(confidence_score * self.confidence_weight)
        
        # 3. Consistency score
        consistency_score = self._calculate_consistency_score(response, all_responses)
        scores.append(consistency_score * self.consistency_weight)
        
        # 4. Source quality score
        source_score = self._calculate_source_score(response)
        scores.append(source_score * self.source_quality_weight)
        
        # Combine scores
        total_score = sum(scores)
        
        return min(max(total_score, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _calculate_accuracy_score(
        self,
        response: MinerResponse,
        consensus: Optional[Resolution]
    ) -> float:
        """Calculate accuracy score based on agreement with consensus."""
        if not consensus:
            return 0.5  # Neutral score if no consensus
        
        if response.resolution == consensus:
            return 1.0
        elif response.resolution == Resolution.PENDING:
            return 0.5  # Partial credit for being uncertain
        else:
            return 0.0
    
    def _calculate_confidence_score(
        self,
        response: MinerResponse,
        consensus: Optional[Resolution]
    ) -> float:
        """
        Calculate confidence score.
        
        Rewards appropriate confidence levels:
        - High confidence for clear resolutions
        - Lower confidence for PENDING
        - Penalizes overconfidence on wrong answers
        """
        confidence = response.confidence / 100.0
        
        if response.resolution == consensus:
            # Correct answer - reward high confidence
            return confidence
        elif response.resolution == Resolution.PENDING:
            # Pending - moderate confidence is good
            target_confidence = 0.5
            distance = abs(confidence - target_confidence)
            return 1.0 - distance
        else:
            # Wrong answer - penalize high confidence
            return 1.0 - confidence
    
    def _calculate_consistency_score(
        self,
        response: MinerResponse,
        all_responses: List[MinerResponse]
    ) -> float:
        """
        Calculate consistency with other high-confidence responses.
        """
        if len(all_responses) < 2:
            return 1.0  # No comparison possible
        
        # Find high-confidence responses (>80%)
        high_conf_responses = [
            r for r in all_responses 
            if r.confidence > 80 and r != response
        ]
        
        if not high_conf_responses:
            return 1.0  # No high-confidence peers
        
        # Calculate agreement rate
        agreements = sum(
            1 for r in high_conf_responses 
            if r.resolution == response.resolution
        )
        
        return agreements / len(high_conf_responses)
    
    def _calculate_source_score(self, response: MinerResponse) -> float:
        """
        Calculate source quality score.
        
        Considers:
        - Number of sources
        - Source diversity
        - Known reliable sources
        """
        if not response.sources:
            return 0.0
        
        # Reliable source patterns
        reliable_sources = [
            "coingecko", "coinmarketcap", "yahoo", "bloomberg",
            "reuters", "binance", "coinbase", "kraken"
        ]
        
        # Count sources
        num_sources = len(response.sources)
        source_count_score = min(num_sources / 3.0, 1.0)  # Max benefit at 3 sources
        
        # Check for reliable sources
        reliable_count = sum(
            1 for source in response.sources
            if any(reliable in source.lower() for reliable in reliable_sources)
        )
        reliability_score = min(reliable_count / 2.0, 1.0)  # Max at 2 reliable
        
        # Combine scores
        return (source_count_score + reliability_score) / 2.0
    
    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """
        Normalize scores to sum to 1.0 for weight setting.
        """
        if not scores:
            return {}
        
        total = sum(scores.values())
        if total == 0:
            # Equal weights if all scores are 0
            equal_weight = 1.0 / len(scores)
            return {uid: equal_weight for uid in scores}
        
        # Normalize
        return {uid: score / total for uid, score in scores.items()}
    
    def calculate_consensus(
        self,
        statement: Statement,
        responses: List[MinerResponse]
    ) -> ValidationResult:
        """
        Calculate consensus result from miner responses.
        
        Returns:
            ValidationResult with consensus information
        """
        if not responses:
            return ValidationResult(
                consensus_resolution=Resolution.PENDING,
                consensus_confidence=0.0,
                total_responses=0,
                valid_responses=0
            )
        
        # Filter valid responses
        valid_responses = [r for r in responses if r.is_valid()]
        
        # Calculate consensus
        consensus = self._calculate_consensus(valid_responses)
        
        # Calculate average confidence for consensus resolution
        consensus_responses = [
            r for r in valid_responses 
            if r.resolution == consensus
        ]
        
        avg_confidence = 0.0
        if consensus_responses:
            avg_confidence = sum(r.confidence for r in consensus_responses) / len(consensus_responses)
        
        # Calculate miner scores
        scores = self.calculate_scores(statement, valid_responses)
        
        # Collect unique sources
        all_sources = set()
        for response in valid_responses:
            all_sources.update(response.sources)
        
        # Store scores for weight calculation
        for miner_uid, score in scores.items():
            self.accumulated_scores[miner_uid].append(score)
            # Keep only recent scores (last 100)
            if len(self.accumulated_scores[miner_uid]) > 100:
                self.accumulated_scores[miner_uid] = self.accumulated_scores[miner_uid][-100:]
        
        return ValidationResult(
            consensus_resolution=consensus or Resolution.PENDING,
            consensus_confidence=avg_confidence,
            total_responses=len(responses),
            valid_responses=len(valid_responses),
            miner_scores=scores,
            consensus_sources=list(all_sources)[:10]  # Top 10 sources
        )
    
    def get_miner_scores(self) -> Dict[int, float]:
        """
        Get accumulated miner scores for weight setting.
        
        Returns:
            Dictionary mapping miner UID to average score
        """
        if not self.accumulated_scores:
            return {}
        
        # Calculate average scores
        avg_scores = {}
        for miner_uid, scores in self.accumulated_scores.items():
            if scores:
                avg_scores[miner_uid] = sum(scores) / len(scores)
        
        # Normalize scores for weight setting
        return self._normalize_scores(avg_scores)