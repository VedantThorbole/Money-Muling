"""
Unit tests for cycle detection algorithm
"""

import pytest
import networkx as nx
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.algorithms.cycle_detector import CycleDetector
from server.core.graph_analyzer import GraphAnalyzer

class TestCycleDetection:
    """Test cases for cycle detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = GraphAnalyzer()
        self.detector = None
        
    def create_test_graph(self, edges):
        """Create a test graph from edge list"""
        df = pd.DataFrame(edges, columns=['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'])
        return self.analyzer.build_graph_from_csv(df)
    
    def test_detect_simple_cycle(self):
        """Test detection of a simple 3-node cycle"""
        edges = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'A', 100, '2026-02-18 12:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph, min_cycle_length=3, max_cycle_length=3)
        cycles = detector.find_all_cycles()
        
        assert len(cycles) == 1
        assert set(cycles[0]['nodes']) == {'A', 'B', 'C'}
        assert cycles[0]['length'] == 3
    
    def test_detect_4_node_cycle(self):
        """Test detection of a 4-node cycle"""
        edges = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 100, '2026-02-18 12:00:00'],
            ['T4', 'D', 'A', 100, '2026-02-18 13:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph, min_cycle_length=3, max_cycle_length=4)
        cycles = detector.find_all_cycles()
        
        assert len(cycles) == 1
        assert set(cycles[0]['nodes']) == {'A', 'B', 'C', 'D'}
        assert cycles[0]['length'] == 4
    
    def test_no_cycle_detected(self):
        """Test when no cycles exist"""
        edges = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'D', 100, '2026-02-18 12:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph)
        cycles = detector.find_all_cycles()
        
        assert len(cycles) == 0
    
    def test_multiple_cycles(self):
        """Test detection of multiple cycles in same graph"""
        edges = [
            # Cycle 1: A-B-C-A
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'A', 100, '2026-02-18 12:00:00'],
            # Cycle 2: X-Y-Z-X
            ['T4', 'X', 'Y', 200, '2026-02-18 13:00:00'],
            ['T5', 'Y', 'Z', 200, '2026-02-18 14:00:00'],
            ['T6', 'Z', 'X', 200, '2026-02-18 15:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph)
        cycles = detector.find_all_cycles()
        
        assert len(cycles) == 2
        
        cycle_sets = [set(c['nodes']) for c in cycles]
        assert {'A', 'B', 'C'} in cycle_sets
        assert {'X', 'Y', 'Z'} in cycle_sets
    
    def test_cycle_length_filtering(self):
        """Test filtering cycles by length"""
        edges = [
            # 3-node cycle
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'A', 100, '2026-02-18 12:00:00'],
            # 4-node cycle
            ['T4', 'X', 'Y', 100, '2026-02-18 13:00:00'],
            ['T5', 'Y', 'Z', 100, '2026-02-18 14:00:00'],
            ['T6', 'Z', 'W', 100, '2026-02-18 15:00:00'],
            ['T7', 'W', 'X', 100, '2026-02-18 16:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        
        # Detect only 3-node cycles
        detector = CycleDetector(graph, min_cycle_length=3, max_cycle_length=3)
        cycles = detector.find_all_cycles()
        assert len(cycles) == 1
        assert set(cycles[0]['nodes']) == {'A', 'B', 'C'}
        
        # Detect cycles up to length 4
        detector = CycleDetector(graph, min_cycle_length=3, max_cycle_length=4)
        cycles = detector.find_all_cycles()
        assert len(cycles) == 2
    
    def test_cycle_with_multiple_edges(self):
        """Test cycle detection with multiple edges between nodes"""
        edges = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'A', 'B', 200, '2026-02-18 11:00:00'],  # Second edge A->B
            ['T3', 'B', 'C', 100, '2026-02-18 12:00:00'],
            ['T4', 'C', 'A', 100, '2026-02-18 13:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph)
        cycles = detector.find_all_cycles()
        
        assert len(cycles) == 1
        assert cycles[0]['transaction_count'] >= 3  # Should count multiple edges
    
    def test_get_statistics(self):
        """Test cycle statistics generation"""
        edges = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'A', 100, '2026-02-18 12:00:00']
        ]
        
        graph = self.create_test_graph(edges)
        detector = CycleDetector(graph)
        cycles = detector.find_all_cycles()
        
        stats = detector.get_cycle_statistics()
        assert stats['total_cycles'] == 1
        assert stats['cycles_by_length']['length_3'] == 1
        assert stats['total_accounts_involved'] == 3
        assert stats['total_transaction_volume'] > 0

if __name__ == '__main__':
    pytest.main(['-v', __file__])