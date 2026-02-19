"""
Unit tests for shell chain detection algorithm
"""

import pytest
import networkx as nx
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.algorithms.chain_detector import ChainDetector
from server.core.graph_analyzer import GraphAnalyzer

class TestChainDetection:
    """Test cases for shell chain detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = GraphAnalyzer()
        self.detector = None
        
    def create_test_graph(self, edges):
        """Create a test graph from edge list"""
        df = pd.DataFrame(edges, columns=['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'])
        return self.analyzer.build_graph_from_csv(df)
    
    def test_detect_simple_shell_chain(self):
        """Test detection of a simple shell chain"""
        edges = [
            ['T1', 'A', 'B', 1000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 990, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 980, '2026-02-18 12:00:00'],
            # B and C have low activity (only these transactions)
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph, min_chain_length=3, max_transactions_per_shell=2)
        chains = detector.detect_shell_chains()
        
        assert len(chains) >= 1
        assert chains[0]['length'] >= 3
        assert 'B' in chains[0]['shell_nodes']
        assert 'C' in chains[0]['shell_nodes']
    
    def test_no_shell_chain(self):
        """Test when no shell chain exists"""
        edges = [
            ['T1', 'A', 'B', 1000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 990, '2026-02-18 11:00:00'],
            ['T3', 'B', 'D', 500, '2026-02-18 12:00:00'],  # B has multiple transactions
            ['T4', 'C', 'E', 400, '2026-02-18 13:00:00'],  # C has multiple
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph, max_transactions_per_shell=1)
        chains = detector.detect_shell_chains()
        
        assert len(chains) == 0
    
    def test_longer_shell_chain(self):
        """Test detection of longer shell chain"""
        edges = [
            ['T1', 'A', 'B', 5000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 4900, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 4800, '2026-02-18 12:00:00'],
            ['T4', 'D', 'E', 4700, '2026-02-18 13:00:00'],
            ['T5', 'E', 'F', 4600, '2026-02-18 14:00:00'],
            # B, C, D, E are shells (only these transactions)
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph, min_chain_length=4, max_transactions_per_shell=2)
        chains = detector.detect_shell_chains()
        
        assert len(chains) >= 1
        assert chains[0]['length'] >= 4
        assert len(chains[0]['shell_nodes']) >= 3
    
    def test_shell_account_identification(self):
        """Test identification of shell accounts"""
        edges = [
            # Shell accounts (low activity)
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            
            # High activity account (not shell)
            ['T3', 'X', 'Y', 1000, '2026-02-18 12:00:00'],
            ['T4', 'X', 'Z', 2000, '2026-02-18 13:00:00'],
            ['T5', 'Y', 'X', 1500, '2026-02-18 14:00:00'],
            ['T6', 'Z', 'X', 2500, '2026-02-18 15:00:00'],
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph, max_transactions_per_shell=2)
        
        # Check shell accounts set
        assert 'B' in detector.shell_accounts
        assert 'C' in detector.shell_accounts
        assert 'X' not in detector.shell_accounts
        assert 'Y' not in detector.shell_accounts
    
    def test_amount_similarity(self):
        """Test amount similarity detection for shell accounts"""
        edges = [
            # Similar amounts (suspicious)
            ['T1', 'A', 'B', 1000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 1000, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 1000, '2026-02-18 12:00:00'],
            
            # Different amounts (less suspicious)
            ['T4', 'X', 'Y', 1000, '2026-02-18 13:00:00'],
            ['T5', 'Y', 'Z', 500, '2026-02-18 14:00:00'],
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph)
        
        # Check B and C should be shells (similar amounts)
        assert 'B' in detector.shell_accounts
        assert 'C' in detector.shell_accounts
        
        # Y might not be shell due to different amounts
        assert 'Y' not in detector.shell_accounts
    
    def test_multiple_chains(self):
        """Test detection of multiple shell chains"""
        edges = [
            # Chain 1: A-B-C-D
            ['T1', 'A', 'B', 1000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 990, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 980, '2026-02-18 12:00:00'],
            
            # Chain 2: X-Y-Z-W
            ['T4', 'X', 'Y', 2000, '2026-02-18 13:00:00'],
            ['T5', 'Y', 'Z', 1900, '2026-02-18 14:00:00'],
            ['T6', 'Z', 'W', 1800, '2026-02-18 15:00:00'],
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph)
        chains = detector.detect_shell_chains()
        
        assert len(chains) >= 2
        
        chain_accounts = [set(c['nodes']) for c in chains]
        assert {'A', 'B', 'C', 'D'} in chain_accounts or {'A', 'B', 'C'} in chain_accounts
        assert {'X', 'Y', 'Z', 'W'} in chain_accounts or {'X', 'Y', 'Z'} in chain_accounts
    
    def test_get_statistics(self):
        """Test chain statistics generation"""
        edges = [
            ['T1', 'A', 'B', 1000, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 990, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 980, '2026-02-18 12:00:00'],
        ]
        
        graph = self.create_test_graph(edges)
        detector = ChainDetector(graph)
        chains = detector.detect_shell_chains()
        
        stats = detector.get_chain_statistics()
        assert stats['total_chains'] >= 1
        assert stats['total_shell_accounts'] >= 2
        assert stats['total_transaction_volume'] > 0

if __name__ == '__main__':
    pytest.main(['-v', __file__])