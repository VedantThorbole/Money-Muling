"""
Unit tests for fan pattern detection algorithm
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.algorithms.fan_detector import FanDetector
from server.core.graph_analyzer import GraphAnalyzer

class TestFanDetection:
    """Test cases for fan pattern detection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = GraphAnalyzer()
        self.detector = None
        
    def create_test_data(self, transactions):
        """Create test DataFrame from transactions"""
        return pd.DataFrame(transactions, columns=['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'])
    
    def test_detect_fan_in(self):
        """Test detection of fan-in pattern (many-to-one)"""
        transactions = [
            ['T1', 'X1', 'TARGET', 1000, '2026-02-18 10:00:00'],
            ['T2', 'X2', 'TARGET', 1000, '2026-02-18 11:00:00'],
            ['T3', 'X3', 'TARGET', 1000, '2026-02-18 12:00:00'],
            ['T4', 'X4', 'TARGET', 1000, '2026-02-18 13:00:00'],
            ['T5', 'X5', 'TARGET', 1000, '2026-02-18 14:00:00'],
            ['T6', 'X6', 'TARGET', 1000, '2026-02-18 15:00:00'],
            ['T7', 'X7', 'TARGET', 1000, '2026-02-18 16:00:00'],
            ['T8', 'X8', 'TARGET', 1000, '2026-02-18 17:00:00'],
            ['T9', 'X9', 'TARGET', 1000, '2026-02-18 18:00:00'],
            ['T10', 'X10', 'TARGET', 1000, '2026-02-18 19:00:00'],
            ['T11', 'X11', 'TARGET', 1000, '2026-02-18 20:00:00']  # 11 transactions
        ]
        
        df = self.create_test_data(transactions)
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, time_window_hours=24, threshold=10)
        fan_in = detector.detect_fan_in()
        
        assert len(fan_in) >= 1
        assert fan_in[0]['direction'] == 'in'
        assert fan_in[0]['central_node'] == 'TARGET'
        assert fan_in[0]['transaction_count'] >= 10
    
    def test_detect_fan_out(self):
        """Test detection of fan-out pattern (one-to-many)"""
        transactions = [
            ['T1', 'SOURCE', 'Y1', 100, '2026-02-18 10:00:00'],
            ['T2', 'SOURCE', 'Y2', 100, '2026-02-18 10:05:00'],
            ['T3', 'SOURCE', 'Y3', 100, '2026-02-18 10:10:00'],
            ['T4', 'SOURCE', 'Y4', 100, '2026-02-18 10:15:00'],
            ['T5', 'SOURCE', 'Y5', 100, '2026-02-18 10:20:00'],
            ['T6', 'SOURCE', 'Y6', 100, '2026-02-18 10:25:00'],
            ['T7', 'SOURCE', 'Y7', 100, '2026-02-18 10:30:00'],
            ['T8', 'SOURCE', 'Y8', 100, '2026-02-18 10:35:00'],
            ['T9', 'SOURCE', 'Y9', 100, '2026-02-18 10:40:00'],
            ['T10', 'SOURCE', 'Y10', 100, '2026-02-18 10:45:00'],
            ['T11', 'SOURCE', 'Y11', 100, '2026-02-18 10:50:00']
        ]
        
        df = self.create_test_data(transactions)
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, time_window_hours=1, threshold=10)
        fan_out = detector.detect_fan_out()
        
        assert len(fan_out) >= 1
        assert fan_out[0]['direction'] == 'out'
        assert fan_out[0]['central_node'] == 'SOURCE'
        assert fan_out[0]['transaction_count'] >= 10
    
    def test_no_fan_pattern(self):
        """Test when no fan patterns exist"""
        transactions = [
            ['T1', 'A', 'B', 100, '2026-02-18 10:00:00'],
            ['T2', 'B', 'C', 100, '2026-02-18 11:00:00'],
            ['T3', 'C', 'A', 100, '2026-02-18 12:00:00']
        ]
        
        df = self.create_test_data(transactions)
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, threshold=5)
        fan_in = detector.detect_fan_in()
        fan_out = detector.detect_fan_out()
        
        assert len(fan_in) == 0
        assert len(fan_out) == 0
    
    def test_time_window_filtering(self):
        """Test that patterns outside time window are not detected"""
        transactions = [
            # Within 24 hours
            ['T1', 'X1', 'TARGET', 100, '2026-02-18 10:00:00'],
            ['T2', 'X2', 'TARGET', 100, '2026-02-18 12:00:00'],
            ['T3', 'X3', 'TARGET', 100, '2026-02-18 14:00:00'],
            ['T4', 'X4', 'TARGET', 100, '2026-02-18 16:00:00'],
            ['T5', 'X5', 'TARGET', 100, '2026-02-18 18:00:00'],
            ['T6', 'X6', 'TARGET', 100, '2026-02-18 20:00:00'],
            ['T7', 'X7', 'TARGET', 100, '2026-02-18 22:00:00'],
            ['T8', 'X8', 'TARGET', 100, '2026-02-19 00:00:00'],
            ['T9', 'X9', 'TARGET', 100, '2026-02-19 02:00:00'],
            ['T10', 'X10', 'TARGET', 100, '2026-02-19 04:00:00'],
            # Outside 24 hour window (next day)
            ['T11', 'X11', 'TARGET', 100, '2026-02-20 10:00:00']
        ]
        
        df = self.create_test_data(transactions)
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, time_window_hours=24, threshold=10)
        fan_in = detector.detect_fan_in()
        
        # Should detect first 10 transactions as a pattern
        assert len(fan_in) >= 1
        assert fan_in[0]['transaction_count'] == 10
    
    def test_multiple_windows(self):
        """Test detection of patterns in multiple time windows"""
        transactions = []
        
        # First window: 10 transactions
        for i in range(10):
            transactions.append([f'T{i}', f'X{i}', 'TARGET', 100, f'2026-02-18 {10+i}:00:00'])
        
        # Second window: 10 transactions
        for i in range(10):
            transactions.append([f'T{i+10}', f'Y{i}', 'TARGET', 100, f'2026-02-19 {10+i}:00:00'])
        
        df = self.create_test_data(transactions)
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, time_window_hours=24, threshold=10)
        fan_in = detector.detect_fan_in()
        
        assert len(fan_in) == 2
    
    def test_round_amount_detection(self):
        """Test detection of round amounts in fan patterns"""
        transactions = [
            ['T1', 'X1', 'TARGET', 1000, '2026-02-18 10:00:00'],  # Round
            ['T2', 'X2', 'TARGET', 2000, '2026-02-18 11:00:00'],  # Round
            ['T3', 'X3', 'TARGET', 1500, '2026-02-18 12:00:00'],  # Round
            ['T4', 'X4', 'TARGET', 2500, '2026-02-18 13:00:00'],  # Round
            ['T5', 'X5', 'TARGET', 1234, '2026-02-18 14:00:00'],  # Not round
        ] * 3  # Make 15 transactions
        
        df = self.create_test_data(transactions[:15])
        graph = self.analyzer.build_graph_from_csv(df)
        
        detector = FanDetector(graph, df, threshold=10)
        fan_in = detector.detect_fan_in()
        
        assert len(fan_in) > 0
        assert fan_in[0]['round_amount_percentage'] > 50  # Most amounts are round

if __name__ == '__main__':
    pytest.main(['-v', __file__])