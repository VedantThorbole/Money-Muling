"""
Pattern Detection Orchestrator
Coordinates all detection algorithms and manages the detection pipeline
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import pandas as pd
from datetime import datetime
import logging
from collections import defaultdict

from algorithms.cycle_detector import CycleDetector
from algorithms.fan_detector import FanDetector
from algorithms.chain_detector import ChainDetector
from models.ring import FraudRing
from models.transaction import Transaction
from models.account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Orchestrates all pattern detection algorithms.
    Coordinates cycle, fan, and chain detection and combines results.
    """
    
    def __init__(self, graph: nx.MultiDiGraph, transactions_df: pd.DataFrame, 
                 account_stats: Dict):
        """
        Initialize the pattern detector with graph and data.
        
        Args:
            graph: Transaction graph from GraphAnalyzer
            transactions_df: DataFrame with all transactions
            account_stats: Statistics for each account
        """
        self.graph = graph
        self.transactions_df = transactions_df
        self.account_stats = account_stats
        
        # Detection results
        self.cycles = []
        self.fan_patterns = []
        self.chains = []
        self.all_patterns = []
        
        # Pattern-specific detectors
        self.cycle_detector = None
        self.fan_detector = None
        self.chain_detector = None
        
        # Pattern metadata
        self.pattern_summary = {
            'total_patterns': 0,
            'cycles_found': 0,
            'fan_patterns_found': 0,
            'chains_found': 0,
            'accounts_in_patterns': set(),
            'total_transaction_volume': 0.0,
            'detection_time': 0.0
        }
        
    def detect_all_patterns(self, 
                           cycle_min_len: int = 3,
                           cycle_max_len: int = 5,
                           fan_time_window: int = 72,
                           fan_threshold: int = 10,
                           chain_min_len: int = 3,
                           shell_max_tx: int = 5) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Run all detection algorithms and collect results.
        
        Args:
            cycle_min_len: Minimum cycle length
            cycle_max_len: Maximum cycle length
            fan_time_window: Time window for fan patterns (hours)
            fan_threshold: Threshold for fan patterns
            chain_min_len: Minimum chain length
            shell_max_tx: Maximum transactions for shell accounts
            
        Returns:
            Tuple of (cycles, fan_patterns, chains)
        """
        import time
        start_time = time.time()
        
        logger.info("Starting pattern detection...")
        
        # 1. Detect cycles
        logger.info(f"Detecting cycles (length {cycle_min_len}-{cycle_max_len})...")
        self.cycle_detector = CycleDetector(
            self.graph, 
            min_cycle_length=cycle_min_len,
            max_cycle_length=cycle_max_len
        )
        self.cycles = self.cycle_detector.find_all_cycles()
        logger.info(f"Found {len(self.cycles)} cycles")
        
        # 2. Detect fan patterns
        logger.info(f"Detecting fan patterns (window={fan_time_window}h, threshold={fan_threshold})...")
        self.fan_detector = FanDetector(
            self.graph,
            self.transactions_df,
            time_window_hours=fan_time_window,
            threshold=fan_threshold
        )
        self.fan_patterns = self.fan_detector.detect_fan_in() + self.fan_detector.detect_fan_out()
        logger.info(f"Found {len(self.fan_patterns)} fan patterns")
        
        # 3. Detect shell chains
        logger.info(f"Detecting shell chains (min length={chain_min_len})...")
        self.chain_detector = ChainDetector(
            self.graph,
            min_chain_length=chain_min_len,
            max_transactions_per_shell=shell_max_tx
        )
        self.chains = self.chain_detector.detect_shell_chains()
        logger.info(f"Found {len(self.chains)} shell chains")
        
        # Update summary
        self.pattern_summary['cycles_found'] = len(self.cycles)
        self.pattern_summary['fan_patterns_found'] = len(self.fan_patterns)
        self.pattern_summary['chains_found'] = len(self.chains)
        self.pattern_summary['total_patterns'] = len(self.cycles) + len(self.fan_patterns) + len(self.chains)
        self.pattern_summary['detection_time'] = time.time() - start_time
        
        # Collect all patterns
        self.all_patterns = self.cycles + self.fan_patterns + self.chains
        
        # Update accounts in patterns
        for pattern in self.all_patterns:
            if 'nodes' in pattern:
                self.pattern_summary['accounts_in_patterns'].update(pattern['nodes'])
            elif 'member_accounts' in pattern:
                self.pattern_summary['accounts_in_patterns'].update(pattern['member_accounts'])
            
            if 'total_amount' in pattern:
                self.pattern_summary['total_transaction_volume'] += pattern['total_amount']
        
        return self.cycles, self.fan_patterns, self.chains
    
    def convert_to_fraud_rings(self) -> List[FraudRing]:
        """
        Convert detected patterns to FraudRing objects.
        
        Returns:
            List of FraudRing instances
        """
        rings = []
        
        # Convert cycles
        for cycle in self.cycles:
            ring = FraudRing.from_cycle(cycle)
            rings.append(ring)
        
        # Convert fan patterns
        for fan in self.fan_patterns:
            ring = FraudRing.from_fan_pattern(fan)
            rings.append(ring)
        
        # Convert chains
        for chain in self.chains:
            ring = FraudRing.from_chain(chain)
            rings.append(ring)
        
        logger.info(f"Created {len(rings)} fraud rings from patterns")
        return rings
    
    def get_patterns_by_account(self, account_id: str) -> List[Dict]:
        """
        Get all patterns involving a specific account.
        
        Args:
            account_id: Account ID to search for
            
        Returns:
            List of patterns involving the account
        """
        patterns = []
        
        for pattern in self.all_patterns:
            if 'nodes' in pattern and account_id in pattern['nodes']:
                patterns.append(pattern)
            elif 'member_accounts' in pattern and account_id in pattern['member_accounts']:
                patterns.append(pattern)
        
        return patterns
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about detected patterns.
        
        Returns:
            Dictionary with pattern statistics
        """
        # Get individual detector statistics
        cycle_stats = self.cycle_detector.get_cycle_statistics() if self.cycle_detector else {}
        fan_stats = self.fan_detector.get_fan_statistics() if self.fan_detector else {}
        chain_stats = self.chain_detector.get_chain_statistics() if self.chain_detector else {}
        
        # Pattern type distribution
        pattern_types = defaultdict(int)
        for pattern in self.all_patterns:
            pattern_type = pattern.get('pattern_type', 'unknown')
            # Extract base type
            if 'cycle' in pattern_type:
                pattern_types['cycle'] += 1
            elif 'fan' in pattern_type:
                pattern_types['fan'] += 1
            elif 'chain' in pattern_type:
                pattern_types['chain'] += 1
            else:
                pattern_types['other'] += 1
        
        # Account statistics
        accounts_in_patterns = len(self.pattern_summary['accounts_in_patterns'])
        
        return {
            'summary': {
                'total_patterns': self.pattern_summary['total_patterns'],
                'accounts_involved': accounts_in_patterns,
                'total_volume': self.pattern_summary['total_transaction_volume'],
                'detection_time_seconds': round(self.pattern_summary['detection_time'], 3)
            },
            'distribution': dict(pattern_types),
            'cycles': cycle_stats,
            'fan_patterns': fan_stats,
            'chains': chain_stats,
            'patterns_by_type': {
                'cycles': len(self.cycles),
                'fan_in': sum(1 for p in self.fan_patterns if p.get('direction') == 'in'),
                'fan_out': sum(1 for p in self.fan_patterns if p.get('direction') == 'out'),
                'shell_chains': len(self.chains)
            }
        }
    
    def find_overlapping_patterns(self) -> List[Dict]:
        """
        Find accounts that appear in multiple patterns.
        
        Returns:
            List of overlapping pattern information
        """
        account_patterns = defaultdict(list)
        
        for i, pattern in enumerate(self.all_patterns):
            if 'nodes' in pattern:
                for node in pattern['nodes']:
                    account_patterns[node].append({
                        'pattern_index': i,
                        'pattern_type': pattern.get('pattern_type', 'unknown'),
                        'ring_id': pattern.get('ring_id', f'PATTERN_{i}')
                    })
            elif 'member_accounts' in pattern:
                for node in pattern['member_accounts']:
                    account_patterns[node].append({
                        'pattern_index': i,
                        'pattern_type': pattern.get('pattern_type', 'unknown'),
                        'ring_id': pattern.get('ring_id', f'PATTERN_{i}')
                    })
        
        # Find accounts in multiple patterns
        overlaps = []
        for account, patterns in account_patterns.items():
            if len(patterns) > 1:
                overlaps.append({
                    'account_id': account,
                    'pattern_count': len(patterns),
                    'patterns': patterns,
                    'risk_multiplier': 1.0 + (0.2 * (len(patterns) - 1))
                })
        
        return sorted(overlaps, key=lambda x: x['pattern_count'], reverse=True)
    
    def get_pattern_timeline(self) -> List[Dict]:
        """
        Get timeline of pattern detection.
        
        Returns:
            List of pattern detections with timestamps
        """
        timeline = []
        
        for pattern in self.all_patterns:
            # Extract timestamps from pattern
            timestamps = []
            
            if 'timestamp_range' in pattern:
                timestamps = pattern['timestamp_range']
            elif 'edges' in pattern:
                for edge in pattern.get('edges', []):
                    if 'timestamp' in edge and edge['timestamp']:
                        timestamps.append(edge['timestamp'])
            elif 'transactions' in pattern:
                for tx in pattern.get('transactions', []):
                    if 'timestamp' in tx:
                        timestamps.append(tx['timestamp'])
            
            if timestamps:
                timeline.append({
                    'pattern_type': pattern.get('pattern_type', 'unknown'),
                    'ring_id': pattern.get('ring_id', 'unknown'),
                    'first_seen': min(timestamps) if timestamps else None,
                    'last_seen': max(timestamps) if timestamps else None,
                    'transaction_count': len(timestamps),
                    'accounts_involved': len(pattern.get('nodes', pattern.get('member_accounts', [])))
                })
        
        return sorted(timeline, key=lambda x: x['first_seen'] if x['first_seen'] else '')
    
    def export_patterns_json(self) -> Dict:
        """
        Export all patterns in JSON format.
        
        Returns:
            Dictionary with all pattern data
        """
        return {
            'metadata': {
                'total_patterns': self.pattern_summary['total_patterns'],
                'detection_time': self.pattern_summary['detection_time'],
                'graph_nodes': self.graph.number_of_nodes(),
                'graph_edges': self.graph.number_of_edges()
            },
            'cycles': self.cycles,
            'fan_patterns': self.fan_patterns,
            'chains': self.chains,
            'statistics': self.get_pattern_statistics(),
            'overlaps': self.find_overlapping_patterns(),
            'timeline': self.get_pattern_timeline()
        }
    
    def validate_patterns(self) -> Dict[str, List[str]]:
        """
        Validate detected patterns for consistency.
        
        Returns:
            Dictionary with validation results
        """
        issues = defaultdict(list)
        
        # Check for duplicate patterns
        seen_rings = set()
        for pattern in self.all_patterns:
            ring_id = pattern.get('ring_id')
            if ring_id in seen_rings:
                issues['duplicate_rings'].append(ring_id)
            seen_rings.add(ring_id)
        
        # Validate cycle integrity
        for cycle in self.cycles:
            nodes = cycle.get('nodes', [])
            # Check if cycle actually exists in graph
            for i in range(len(nodes)):
                from_node = nodes[i]
                to_node = nodes[(i + 1) % len(nodes)]
                if not self.graph.has_edge(from_node, to_node):
                    issues['broken_cycles'].append(f"{ring_id}: {from_node}->{to_node} missing")
        
        # Validate fan pattern thresholds
        for fan in self.fan_patterns:
            tx_count = fan.get('transaction_count', 0)
            threshold = int(fan.get('pattern_type', '').split('_')[-1]) if 'threshold' in fan.get('pattern_type', '') else 0
            if tx_count < threshold:
                issues['below_threshold'].append(f"{fan.get('ring_id')}: {tx_count} < {threshold}")
        
        return dict(issues)
    
    def clear(self):
        """Clear all detected patterns"""
        self.cycles = []
        self.fan_patterns = []
        self.chains = []
        self.all_patterns = []
        self.pattern_summary = {
            'total_patterns': 0,
            'cycles_found': 0,
            'fan_patterns_found': 0,
            'chains_found': 0,
            'accounts_in_patterns': set(),
            'total_transaction_volume': 0.0,
            'detection_time': 0.0
        }
        logger.info("Pattern detector cleared")