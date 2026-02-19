"""
Graph Analysis Engine
Builds and analyzes transaction graphs for money muling detection
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict
from datetime import datetime
import numpy as np

class GraphAnalyzer:
    """
    Main graph analysis engine that builds the transaction graph
    and provides methods for graph traversal and analysis.
    """
    
    def __init__(self):
        """Initialize the graph analyzer"""
        self.graph = nx.MultiDiGraph()  # Use MultiDiGraph to handle multiple edges
        self.transactions = []
        self.account_stats = defaultdict(lambda: {
            'in_degree': 0,
            'out_degree': 0,
            'total_sent': 0.0,
            'total_received': 0.0,
            'unique_senders': set(),
            'unique_receivers': set(),
            'tx_timestamps': [],
            'tx_amounts': [],
            'avg_amount': 0.0,
            'std_amount': 0.0,
            'first_tx': None,
            'last_tx': None
        })
        self.node_attributes = {}
        self.edge_attributes = {}
        
    def build_graph_from_csv(self, df: pd.DataFrame) -> nx.MultiDiGraph:
        """
        Build a directed multigraph from transaction dataframe.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            NetworkX MultiDiGraph
        """
        # Reset stats
        self.account_stats.clear()
        
        for _, row in df.iterrows():
            sender = str(row['sender_id']).strip()
            receiver = str(row['receiver_id']).strip()
            amount = float(row['amount'])
            timestamp = row['timestamp']
            tx_id = str(row['transaction_id']).strip()
            
            # Convert timestamp if string
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
            
            # Add nodes with attributes
            self._add_node_with_attributes(sender)
            self._add_node_with_attributes(receiver)
            
            # Add edge with transaction data
            self.graph.add_edge(
                sender, 
                receiver, 
                key=tx_id,
                amount=amount,
                timestamp=timestamp,
                transaction_id=tx_id
            )
            
            # Update statistics
            self._update_stats(sender, receiver, amount, timestamp, tx_id)
        
        # Calculate derived statistics
        self._calculate_derived_stats()
        
        return self.graph
    
    def _add_node_with_attributes(self, node_id: str):
        """Add node with default attributes if not exists"""
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, 
                              total_sent=0.0,
                              total_received=0.0,
                              transaction_count=0,
                              first_seen=None,
                              last_seen=None)
    
    def _update_stats(self, sender: str, receiver: str, amount: float, 
                     timestamp: pd.Timestamp, tx_id: str):
        """Update account statistics"""
        # Sender stats
        self.account_stats[sender]['out_degree'] += 1
        self.account_stats[sender]['total_sent'] += amount
        self.account_stats[sender]['unique_receivers'].add(receiver)
        self.account_stats[sender]['tx_timestamps'].append(timestamp)
        self.account_stats[sender]['tx_amounts'].append(amount)
        
        # Receiver stats
        self.account_stats[receiver]['in_degree'] += 1
        self.account_stats[receiver]['total_received'] += amount
        self.account_stats[receiver]['unique_senders'].add(sender)
        self.account_stats[receiver]['tx_timestamps'].append(timestamp)
        self.account_stats[receiver]['tx_amounts'].append(amount)
        
        # Update first/last seen
        for account in [sender, receiver]:
            if (self.account_stats[account]['first_tx'] is None or 
                timestamp < self.account_stats[account]['first_tx']):
                self.account_stats[account]['first_tx'] = timestamp
            
            if (self.account_stats[account]['last_tx'] is None or 
                timestamp > self.account_stats[account]['last_tx']):
                self.account_stats[account]['last_tx'] = timestamp
    
    def _calculate_derived_stats(self):
        """Calculate derived statistics for all accounts"""
        for account, stats in self.account_stats.items():
            # Calculate average and std of amounts
            amounts = stats['tx_amounts']
            if amounts:
                stats['avg_amount'] = np.mean(amounts)
                stats['std_amount'] = np.std(amounts) if len(amounts) > 1 else 0
                stats['min_amount'] = min(amounts)
                stats['max_amount'] = max(amounts)
            
            # Calculate time-based metrics
            timestamps = stats['tx_timestamps']
            if len(timestamps) > 1:
                time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 
                            for i in range(len(timestamps)-1)]
                stats['avg_time_gap_hours'] = np.mean(time_diffs)
                stats['max_time_gap_hours'] = max(time_diffs)
                stats['min_time_gap_hours'] = min(time_diffs)
                stats['total_activity_days'] = (max(timestamps) - min(timestamps)).total_seconds() / (24*3600)
            
            # Calculate ratios
            if stats['total_received'] > 0:
                stats['sent_received_ratio'] = stats['total_sent'] / stats['total_received']
            else:
                stats['sent_received_ratio'] = float('inf') if stats['total_sent'] > 0 else 0
            
            # Update node attributes in graph
            if self.graph.has_node(account):
                for key, value in stats.items():
                    if key not in ['unique_senders', 'unique_receivers', 'tx_timestamps', 'tx_amounts']:
                        self.graph.nodes[account][key] = value
    
    def get_graph_metrics(self) -> Dict[str, Any]:
        """Get comprehensive graph metrics"""
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'num_transactions': self.graph.size(),
            'is_directed': self.graph.is_directed(),
            'is_multigraph': self.graph.is_multigraph(),
            'density': nx.density(self.graph),
            'num_strongly_connected_components': nx.number_strongly_connected_components(self.graph),
            'num_weakly_connected_components': nx.number_weakly_connected_components(self.graph),
            'average_clustering': nx.average_clustering(self.graph.to_undirected()) if self.graph.number_of_nodes() > 1 else 0,
            'total_transaction_volume': sum(stats['total_sent'] for stats in self.account_stats.values()),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            'max_degree': max(dict(self.graph.degree()).values()) if self.graph.number_of_nodes() > 0 else 0
        }
    
    def get_subgraph(self, nodes: List[str]) -> nx.MultiDiGraph:
        """Get induced subgraph for given nodes"""
        return self.graph.subgraph(nodes)
    
    def get_transaction_path(self, start: str, end: str, max_length: int = 10) -> List[List[str]]:
        """Find all paths between two accounts"""
        try:
            paths = list(nx.all_simple_paths(self.graph, start, end, cutoff=max_length))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def get_account_ego_network(self, account: str, radius: int = 2) -> nx.MultiDiGraph:
        """Get ego network for an account"""
        return nx.ego_graph(self.graph, account, radius=radius, undirected=True)
    
    def get_account_summary(self, account: str) -> Dict[str, Any]:
        """Get comprehensive summary for a single account"""
        if account not in self.account_stats:
            return {}
        
        stats = self.account_stats[account].copy()
        
        # Convert sets to lists for JSON serialization
        stats['unique_senders'] = list(stats['unique_senders'])
        stats['unique_receivers'] = list(stats['unique_receivers'])
        
        # Add graph-based metrics
        if self.graph.has_node(account):
            stats['pagerank'] = nx.pagerank(self.graph, alpha=0.85).get(account, 0)
            stats['betweenness'] = nx.betweenness_centrality(self.graph).get(account, 0)
            stats['closeness'] = nx.closeness_centrality(self.graph).get(account, 0)
        
        # Convert timestamps to strings
        if stats['first_tx']:
            stats['first_tx'] = stats['first_tx'].strftime('%Y-%m-%d %H:%M:%S')
        if stats['last_tx']:
            stats['last_tx'] = stats['last_tx'].strftime('%Y-%m-%d %H:%M:%S')
        
        return stats
    
    def export_to_cytoscape(self) -> Dict:
        """Export graph to Cytoscape.js format for visualization"""
        elements = []
        
        # Add nodes
        for node, data in self.graph.nodes(data=True):
            stats = self.account_stats.get(node, {})
            elements.append({
                'data': {
                    'id': node,
                    'label': node[:10] + '...' if len(node) > 10 else node,
                    'total_sent': stats.get('total_sent', 0),
                    'total_received': stats.get('total_received', 0),
                    'transaction_count': stats.get('in_degree', 0) + stats.get('out_degree', 0)
                }
            })
        
        # Add edges
        for u, v, key, data in self.graph.edges(data=True, keys=True):
            elements.append({
                'data': {
                    'id': f"{u}-{v}-{key}",
                    'source': u,
                    'target': v,
                    'amount': data.get('amount', 0),
                    'timestamp': data.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if isinstance(data.get('timestamp'), pd.Timestamp) else str(data.get('timestamp', '')),
                    'transaction_id': data.get('transaction_id', '')
                }
            })
        
        return {'elements': elements}