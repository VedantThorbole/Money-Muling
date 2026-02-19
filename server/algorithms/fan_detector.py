"""
Fan Pattern Detection Algorithm for Money Muling
Detects smurfing (fan-in) and dispersion (fan-out) patterns
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
import pandas as pd
import numpy as np

class FanDetector:
    """
    Detects fan-in (many-to-one) and fan-out (one-to-many) patterns
    within specified time windows. These patterns indicate smurfing
    where money is aggregated or dispersed to avoid detection.
    """
    
    def __init__(self, graph, transactions_df: pd.DataFrame, 
                 time_window_hours: int = 72, threshold: int = 10):
        """
        Initialize the fan detector.
        
        Args:
            graph: NetworkX directed graph
            transactions_df: DataFrame with all transactions
            time_window_hours: Time window for pattern detection (default: 72 hours)
            threshold: Minimum number of transactions to qualify as pattern (default: 10)
        """
        self.graph = graph
        self.transactions = transactions_df
        self.time_window = time_window_hours
        self.threshold = threshold
        self.fan_id_counter = 0
        self.detected_patterns = []
        
        # Convert timestamps to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(self.transactions['timestamp']):
            self.transactions['timestamp'] = pd.to_datetime(self.transactions['timestamp'])
    
    def detect_fan_in(self) -> List[Dict]:
        """
        Detect fan-in patterns (multiple accounts sending to single receiver).
        
        Returns:
            List of fan-in patterns detected
        """
        fan_in_patterns = []
        
        # Group transactions by receiver
        receiver_groups = self.transactions.groupby('receiver_id')
        
        for receiver, group in receiver_groups:
            if len(group) < self.threshold:
                continue
            
            # Sort by timestamp
            group = group.sort_values('timestamp')
            
            # Find time windows with high concentration
            windows = self._find_dense_windows(group)
            
            for window_txs in windows:
                if len(window_txs) >= self.threshold:
                    pattern = self._create_fan_pattern(
                        central_node=receiver,
                        transactions=window_txs,
                        direction='in'
                    )
                    fan_in_patterns.append(pattern)
                    self.detected_patterns.append(pattern)
        
        return fan_in_patterns
    
    def detect_fan_out(self) -> List[Dict]:
        """
        Detect fan-out patterns (single sender to multiple receivers).
        
        Returns:
            List of fan-out patterns detected
        """
        fan_out_patterns = []
        
        # Group transactions by sender
        sender_groups = self.transactions.groupby('sender_id')
        
        for sender, group in sender_groups:
            if len(group) < self.threshold:
                continue
            
            # Sort by timestamp
            group = group.sort_values('timestamp')
            
            # Find time windows with high concentration
            windows = self._find_dense_windows(group)
            
            for window_txs in windows:
                if len(window_txs) >= self.threshold:
                    pattern = self._create_fan_pattern(
                        central_node=sender,
                        transactions=window_txs,
                        direction='out'
                    )
                    fan_out_patterns.append(pattern)
                    self.detected_patterns.append(pattern)
        
        return fan_out_patterns
    
    def _find_dense_windows(self, transactions: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Find time windows with dense transaction activity.
        
        Args:
            transactions: DataFrame of transactions for a single account
            
        Returns:
            List of DataFrames, each representing a dense window
        """
        if len(transactions) < self.threshold:
            return []
        
        windows = []
        timestamps = transactions['timestamp'].values
        window_size = pd.Timedelta(hours=self.time_window)
        
        # Sliding window approach
        for i in range(len(transactions)):
            window_start = timestamps[i]
            window_end = window_start + window_size
            
            # Find all transactions in this window
            window_mask = (transactions['timestamp'] >= window_start) & \
                         (transactions['timestamp'] <= window_end)
            window_txs = transactions[window_mask]
            
            if len(window_txs) >= self.threshold:
                # Check if this window is already included
                is_new = True
                for existing_window in windows:
                    if set(window_txs.index) & set(existing_window.index):
                        # Merge if overlapping
                        combined = pd.concat([existing_window, window_txs]).drop_duplicates()
                        if len(combined) <= len(existing_window) + len(window_txs):
                            windows.remove(existing_window)
                            windows.append(combined)
                            is_new = False
                            break
                
                if is_new:
                    windows.append(window_txs)
        
        # Remove duplicate windows
        unique_windows = []
        seen_indices = set()
        
        for window in windows:
            indices = frozenset(window.index)
            if indices not in seen_indices:
                seen_indices.add(indices)
                unique_windows.append(window)
        
        return unique_windows
    
    def _create_fan_pattern(self, central_node: str, transactions: pd.DataFrame, 
                           direction: str) -> Dict:
        """
        Create a fan pattern dictionary with metadata.
        
        Args:
            central_node: The central account (receiver for fan-in, sender for fan-out)
            transactions: Transactions in this pattern
            direction: 'in' for fan-in, 'out' for fan-out
            
        Returns:
            Dictionary with pattern details
        """
        self.fan_id_counter += 1
        
        # Get all involved accounts
        if direction == 'in':
            # Fan-in: multiple senders to one receiver
            other_accounts = transactions['sender_id'].unique().tolist()
            member_accounts = [central_node] + other_accounts
            pattern_name = f'fan_in_threshold_{self.threshold}'
        else:
            # Fan-out: one sender to multiple receivers
            other_accounts = transactions['receiver_id'].unique().tolist()
            member_accounts = other_accounts + [central_node]
            pattern_name = f'fan_out_threshold_{self.threshold}'
        
        # Calculate statistics
        total_amount = transactions['amount'].sum()
        avg_amount = transactions['amount'].mean()
        std_amount = transactions['amount'].std()
        
        # Time analysis
        timestamps = transactions['timestamp']
        time_span = (timestamps.max() - timestamps.min()).total_seconds() / 3600  # in hours
        transaction_rate = len(transactions) / time_span if time_span > 0 else len(transactions)
        
        # Detect if amounts are unusually round (suspicious)
        round_amounts = sum(1 for amt in transactions['amount'] if amt % 1000 == 0 or amt % 500 == 0)
        round_percentage = (round_amounts / len(transactions)) * 100
        
        return {
            'ring_id': f"FAN_RING_{self.fan_id_counter:03d}",
            'central_node': central_node,
            'direction': direction,
            'pattern_type': pattern_name,
            'member_accounts': member_accounts,
            'member_count': len(member_accounts),
            'transaction_count': len(transactions),
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'std_amount': std_amount if not np.isnan(std_amount) else 0,
            'time_span_hours': round(time_span, 2),
            'transaction_rate_per_hour': round(transaction_rate, 2),
            'round_amount_percentage': round(round_percentage, 2),
            'timestamp_start': timestamps.min().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp_end': timestamps.max().strftime('%Y-%m-%d %H:%M:%S'),
            'transactions': transactions.to_dict('records')
        }
    
    def get_fan_statistics(self) -> Dict:
        """
        Get statistics about detected fan patterns.
        
        Returns:
            Dictionary with fan pattern statistics
        """
        stats = {
            'total_fan_patterns': len(self.detected_patterns),
            'fan_in_count': sum(1 for p in self.detected_patterns if p['direction'] == 'in'),
            'fan_out_count': sum(1 for p in self.detected_patterns if p['direction'] == 'out'),
            'total_accounts_involved': 0,
            'total_transaction_volume': 0,
            'average_pattern_size': 0,
            'average_time_span': 0
        }
        
        accounts = set()
        total_size = 0
        total_time = 0
        
        for pattern in self.detected_patterns:
            accounts.update(pattern['member_accounts'])
            stats['total_transaction_volume'] += pattern['total_amount']
            total_size += pattern['member_count']
            total_time += pattern['time_span_hours']
        
        stats['total_accounts_involved'] = len(accounts)
        if self.detected_patterns:
            stats['average_pattern_size'] = total_size / len(self.detected_patterns)
            stats['average_time_span'] = total_time / len(self.detected_patterns)
        
        return stats