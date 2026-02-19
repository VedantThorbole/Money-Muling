"""
Suspicion Scoring Engine
Calculates suspicion scores for accounts and rings based on multiple factors
"""

import numpy as np
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta
import networkx as nx

class SuspicionScorer:
    """
    Calculates suspicion scores (0-100) for accounts and fraud rings
    based on pattern detection and behavioral analysis.
    """
    
    def __init__(self, graph: nx.MultiDiGraph, account_stats: Dict):
        """
        Initialize the suspicion scorer.
        
        Args:
            graph: Transaction graph
            account_stats: Statistics for each account
        """
        self.graph = graph
        self.account_stats = account_stats
        self.base_weights = {
            'cycle': 0.35,
            'fan_in': 0.25,
            'fan_out': 0.25,
            'shell_chain': 0.30,
            'velocity': 0.15,
            'amount_pattern': 0.10,
            'timing': 0.10,
            'network_position': 0.15
        }
        
    def calculate_scores(self, rings: List[Dict]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Calculate suspicion scores for all accounts in rings.
        
        Args:
            rings: List of detected fraud rings
            
        Returns:
            Tuple of (account_scores, ring_scores)
        """
        account_scores = defaultdict(float)
        ring_scores = {}
        
        # First pass: calculate ring-level scores
        for ring in rings:
            ring_score = self._calculate_ring_score(ring)
            ring_scores[ring['ring_id']] = ring_score
            
            # Distribute ring score to members with individual adjustments
            for account in ring['member_accounts']:
                if account in self.account_stats:
                    individual_score = self._calculate_individual_score(account, ring, ring_score)
                    account_scores[account] = max(account_scores[account], individual_score)
        
        # Second pass: adjust for overlaps and correlations
        account_scores = self._adjust_for_overlaps(account_scores, rings)
        
        return dict(account_scores), ring_scores
    
    def _calculate_ring_score(self, ring: Dict) -> float:
        """
        Calculate base risk score for a ring.
        
        Args:
            ring: Fraud ring dictionary
            
        Returns:
            Risk score 0-100
        """
        score = 50.0  # Base score
        
        pattern_type = ring['pattern_type']
        
        # Pattern-based scoring
        if 'cycle' in pattern_type:
            score += 30.0
            # Longer cycles are more suspicious
            if 'length_3' in pattern_type:
                score += 5.0
            elif 'length_4' in pattern_type:
                score += 10.0
            elif 'length_5' in pattern_type:
                score += 15.0
                
        elif 'fan_in' in pattern_type:
            score += 25.0
            # Extract threshold
            try:
                if 'threshold' in pattern_type:
                    threshold = int(pattern_type.split('_')[-1])
                    if threshold >= 20:
                        score += 15.0
                    elif threshold >= 15:
                        score += 10.0
                    elif threshold >= 10:
                        score += 5.0
            except:
                pass
                
        elif 'fan_out' in pattern_type:
            score += 25.0
            # Similar threshold logic
            try:
                if 'threshold' in pattern_type:
                    threshold = int(pattern_type.split('_')[-1])
                    if threshold >= 20:
                        score += 15.0
                    elif threshold >= 15:
                        score += 10.0
                    elif threshold >= 10:
                        score += 5.0
            except:
                pass
                
        elif 'shell_chain' in pattern_type:
            score += 35.0
            # Longer chains are more suspicious
            if 'length_4' in pattern_type:
                score += 10.0
            elif 'length_5' in pattern_type:
                score += 20.0
            elif 'length_6' in pattern_type:
                score += 25.0
            
            # Pure shell chains are more suspicious
            if 'pure' in pattern_type:
                score += 10.0
        
        # Size-based scoring
        member_count = len(ring.get('member_accounts', []))
        if member_count > 10:
            score += 10.0
        elif member_count > 5:
            score += 5.0
        
        # Transaction volume scoring
        total_volume = ring.get('metadata', {}).get('total_amount', 0)
        if total_volume > 100000:
            score += 15.0
        elif total_volume > 50000:
            score += 10.0
        elif total_volume > 10000:
            score += 5.0
        
        return min(100.0, max(0.0, score))
    
    def _calculate_individual_score(self, account: str, ring: Dict, ring_score: float) -> float:
        """
        Calculate individual account score with behavioral factors.
        
        Args:
            account: Account ID
            ring: Parent fraud ring
            ring_score: Base ring score
            
        Returns:
            Individual suspicion score
        """
        if account not in self.account_stats:
            return ring_score
        
        stats = self.account_stats[account]
        individual_score = ring_score
        
        # 1. Velocity scoring (transaction frequency)
        tx_count = stats.get('in_degree', 0) + stats.get('out_degree', 0)
        if tx_count > 100:
            individual_score += 15.0
        elif tx_count > 50:
            individual_score += 10.0
        elif tx_count > 20:
            individual_score += 5.0
        
        # 2. Amount pattern scoring (round numbers, consistency)
        round_amount_score = self._score_round_amounts(account)
        individual_score += round_amount_score * 10
        
        # 3. In/Out ratio scoring (mules often have near 1:1)
        ratio_score = self._score_in_out_ratio(account)
        individual_score += ratio_score * 8
        
        # 4. Timing anomaly scoring (night transactions, weekend)
        timing_score = self._score_timing_anomalies(account)
        individual_score += timing_score * 7
        
        # 5. Network position scoring
        network_score = self._score_network_position(account)
        individual_score += network_score * 12
        
        # 6. Account age scoring (new accounts are more suspicious)
        age_score = self._score_account_age(account)
        individual_score += age_score * 5
        
        # 7. Counterparty diversity
        diversity_score = self._score_counterparty_diversity(account)
        individual_score += diversity_score * 8
        
        # 8. Amount variance (too consistent or too variable)
        variance_score = self._score_amount_variance(account)
        individual_score += variance_score * 5
        
        return min(100.0, individual_score)
    
    def _score_round_amounts(self, account: str) -> float:
        """Score based on percentage of round-number transactions"""
        stats = self.account_stats[account]
        amounts = stats.get('tx_amounts', [])
        
        if not amounts:
            return 0.0
        
        round_count = sum(1 for amt in amounts 
                         if amt % 1000 == 0 or amt % 500 == 0 or amt % 100 == 0)
        round_pct = round_count / len(amounts)
        
        # Higher score for more round amounts
        if round_pct > 0.8:
            return 1.0
        elif round_pct > 0.6:
            return 0.7
        elif round_pct > 0.4:
            return 0.4
        elif round_pct > 0.2:
            return 0.2
        return 0.0
    
    def _score_in_out_ratio(self, account: str) -> float:
        """Score based on sent/received ratio"""
        stats = self.account_stats[account]
        sent = stats.get('total_sent', 0)
        received = stats.get('total_received', 0)
        
        if sent == 0 or received == 0:
            return 0.0
        
        ratio = sent / received
        # Ideal mule ratio is close to 1:1
        if 0.9 <= ratio <= 1.1:
            return 1.0
        elif 0.8 <= ratio <= 1.2:
            return 0.8
        elif 0.7 <= ratio <= 1.3:
            return 0.5
        elif 0.5 <= ratio <= 1.5:
            return 0.3
        return 0.0
    
    def _score_timing_anomalies(self, account: str) -> float:
        """Score based on unusual transaction timing"""
        stats = self.account_stats[account]
        timestamps = stats.get('tx_timestamps', [])
        
        if len(timestamps) < 5:
            return 0.3  # Not enough data, slightly suspicious
        
        night_count = 0
        weekend_count = 0
        total = len(timestamps)
        
        for ts in timestamps:
            # Night transactions (11 PM - 5 AM)
            if ts.hour >= 23 or ts.hour <= 5:
                night_count += 1
            
            # Weekend transactions
            if ts.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                weekend_count += 1
        
        night_pct = night_count / total
        weekend_pct = weekend_count / total
        
        score = 0.0
        if night_pct > 0.4:
            score += 0.6
        elif night_pct > 0.2:
            score += 0.3
        
        if weekend_pct > 0.3:
            score += 0.4
        elif weekend_pct > 0.15:
            score += 0.2
        
        return min(1.0, score)
    
    def _score_network_position(self, account: str) -> float:
        """Score based on network centrality and position"""
        try:
            # PageRank - higher means more central in flow
            pagerank = nx.pagerank(self.graph, alpha=0.85).get(account, 0)
            
            # Betweenness - higher means more bridging
            betweenness = nx.betweenness_centrality(self.graph).get(account, 0)
            
            # Combine scores
            score = (pagerank * 2 + betweenness) / 3
            
            # Normalize to 0-1 range
            return min(1.0, score * 10)
            
        except:
            return 0.0
    
    def _score_account_age(self, account: str) -> float:
        """Score based on account age"""
        stats = self.account_stats[account]
        first_tx = stats.get('first_tx')
        
        if not first_tx:
            return 0.5  # Unknown age, moderately suspicious
        
        age_days = (datetime.now() - first_tx).days if isinstance(first_tx, datetime) else 30
        
        if age_days < 7:
            return 1.0  # Very new
        elif age_days < 30:
            return 0.7
        elif age_days < 90:
            return 0.4
        elif age_days < 365:
            return 0.2
        return 0.0
    
    def _score_counterparty_diversity(self, account: str) -> float:
        """Score based on counterparty diversity"""
        stats = self.account_stats[account]
        unique_senders = len(stats.get('unique_senders', set()))
        unique_receivers = len(stats.get('unique_receivers', set()))
        total_tx = stats.get('in_degree', 0) + stats.get('out_degree', 0)
        
        if total_tx == 0:
            return 0.0
        
        # Too few unique counterparties for transaction count is suspicious
        unique_total = unique_senders + unique_receivers
        ratio = unique_total / total_tx
        
        if ratio < 0.2:
            return 1.0  # Very concentrated
        elif ratio < 0.4:
            return 0.7
        elif ratio < 0.6:
            return 0.4
        elif ratio < 0.8:
            return 0.2
        return 0.0
    
    def _score_amount_variance(self, account: str) -> float:
        """Score based on amount variance"""
        stats = self.account_stats[account]
        amounts = stats.get('tx_amounts', [])
        
        if len(amounts) < 3:
            return 0.0
        
        std_dev = np.std(amounts)
        mean_amt = np.mean(amounts)
        
        if mean_amt == 0:
            return 0.0
        
        cv = std_dev / mean_amt  # Coefficient of variation
        
        # Too consistent or too variable can be suspicious
        if cv < 0.1:
            return 0.8  # Extremely consistent
        elif cv > 2.0:
            return 0.6  # Extremely variable
        elif cv < 0.2:
            return 0.4
        elif cv > 1.5:
            return 0.3
        return 0.0
    
    def _adjust_for_overlaps(self, account_scores: Dict[str, float], rings: List[Dict]) -> Dict[str, float]:
        """
        Adjust scores for accounts appearing in multiple rings.
        
        Args:
            account_scores: Current account scores
            rings: List of fraud rings
            
        Returns:
            Adjusted account scores
        """
        # Count rings per account
        ring_count = defaultdict(int)
        for ring in rings:
            for account in ring['member_accounts']:
                if account in account_scores:
                    ring_count[account] += 1
        
        # Apply multiplier for multiple rings
        adjusted_scores = {}
        for account, score in account_scores.items():
            multiplier = 1.0 + (0.2 * (ring_count[account] - 1)) if ring_count[account] > 1 else 1.0
            adjusted_scores[account] = min(100.0, score * multiplier)
        
        return adjusted_scores