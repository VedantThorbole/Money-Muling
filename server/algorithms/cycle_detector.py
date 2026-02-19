"""
Cycle Detection Algorithm for Money Muling
Detects circular fund routing patterns (cycles of length 3-5)
"""

import networkx as nx
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import time

class CycleDetector:
    """
    Detects cycles in the transaction graph that indicate money muling.
    Cycles of length 3-5 are considered suspicious as they indicate
    layering to obscure fund origin.
    """
    
    def __init__(self, graph: nx.DiGraph, min_cycle_length: int = 3, max_cycle_length: int = 5):
        """
        Initialize the cycle detector.
        
        Args:
            graph: NetworkX directed graph of transactions
            min_cycle_length: Minimum cycle length to detect (default: 3)
            max_cycle_length: Maximum cycle length to detect (default: 5)
        """
        self.graph = graph
        self.min_len = min_cycle_length
        self.max_len = max_cycle_length
        self.cycles_found = []
        self.processed_rings = set()
        self.cycle_id_counter = 0
        
    def find_all_cycles(self) -> List[Dict]:
        """
        Find all cycles in the graph within length constraints.
        
        Returns:
            List of cycles with their details including nodes, edges, and metadata
        """
        all_cycles = []
        
        # Optimization: Find strongly connected components first
        # Cycles can only exist within SCCs
        sccs = [comp for comp in nx.strongly_connected_components(self.graph) 
                if len(comp) >= self.min_len]
        
        for scc in sccs:
            # Create subgraph for this SCC
            subgraph = self.graph.subgraph(scc)
            
            # Find cycles in this SCC
            scc_cycles = self._find_cycles_in_scc(subgraph)
            all_cycles.extend(scc_cycles)
            
            # Mark nodes in SCC as processed for cycle detection
            for cycle in scc_cycles:
                for node in cycle['nodes']:
                    self.processed_rings.add(node)
        
        return all_cycles
    
    def _find_cycles_in_scc(self, subgraph: nx.DiGraph) -> List[Dict]:
        """
        Find cycles within a strongly connected component using DFS.
        
        Args:
            subgraph: Subgraph of an SCC
            
        Returns:
            List of cycles found in the SCC
        """
        cycles = []
        nodes = list(subgraph.nodes())
        
        for start_node in nodes:
            # DFS stack: (current_node, path, visited_set)
            stack = [(start_node, [start_node], {start_node})]
            
            while stack:
                current, path, visited = stack.pop()
                
                for neighbor in subgraph.successors(current):
                    if neighbor == start_node and len(path) >= self.min_len:
                        # Found a cycle back to start
                        if len(path) <= self.max_len:
                            cycle_dict = self._create_cycle_dict(path)
                            if self._is_valid_cycle(cycle_dict):
                                cycles.append(cycle_dict)
                    
                    elif neighbor not in visited and len(path) < self.max_len:
                        # Continue DFS
                        new_path = path + [neighbor]
                        new_visited = visited | {neighbor}
                        stack.append((neighbor, new_path, new_visited))
        
        return cycles
    
    def _create_cycle_dict(self, cycle_nodes: List[str]) -> Dict:
        """
        Create a cycle dictionary with all required metadata.
        
        Args:
            cycle_nodes: List of nodes in the cycle
            
        Returns:
            Dictionary with cycle details
        """
        self.cycle_id_counter += 1
        
        # Get all edges in the cycle
        edges = []
        total_amount = 0
        timestamps = []
        
        for i in range(len(cycle_nodes)):
            from_node = cycle_nodes[i]
            to_node = cycle_nodes[(i + 1) % len(cycle_nodes)]
            
            if self.graph.has_edge(from_node, to_node):
                edge_data = self.graph.get_edge_data(from_node, to_node)
                
                # Handle both single edge and multiple edges
                if isinstance(edge_data, dict):
                    if 'amount' in edge_data:
                        amount = edge_data['amount']
                        timestamp = edge_data.get('timestamp', '')
                        
                        edges.append({
                            'from': from_node,
                            'to': to_node,
                            'amount': amount,
                            'timestamp': timestamp
                        })
                        total_amount += amount
                        if timestamp:
                            timestamps.append(timestamp)
                    else:
                        # Multiple edges between same nodes
                        for tx_id, tx_data in edge_data.items():
                            if isinstance(tx_data, dict):
                                edges.append({
                                    'from': from_node,
                                    'to': to_node,
                                    'amount': tx_data.get('amount', 0),
                                    'timestamp': tx_data.get('timestamp', ''),
                                    'transaction_id': tx_id
                                })
                                total_amount += tx_data.get('amount', 0)
                                if tx_data.get('timestamp'):
                                    timestamps.append(tx_data['timestamp'])
        
        return {
            'nodes': cycle_nodes,
            'length': len(cycle_nodes),
            'ring_id': f"CYCLE_RING_{self.cycle_id_counter:03d}",
            'pattern_type': f'cycle_length_{len(cycle_nodes)}',
            'edges': edges,
            'total_amount': total_amount,
            'timestamp_range': [min(timestamps), max(timestamps)] if timestamps else [],
            'transaction_count': len(edges),
            'avg_amount_per_edge': total_amount / len(edges) if edges else 0
        }
    
    def _is_valid_cycle(self, cycle: Dict) -> bool:
        """
        Validate that a cycle is legitimate and not a duplicate.
        
        Args:
            cycle: Cycle dictionary to validate
            
        Returns:
            True if cycle is valid, False otherwise
        """
        nodes = cycle['nodes']
        
        # Check minimum length
        if len(nodes) < self.min_len:
            return False
        
        # Check all nodes are distinct (no self-loops)
        if len(nodes) != len(set(nodes)):
            return False
        
        # Check if cycle is already processed (using sorted nodes as key)
        cycle_key = frozenset(nodes)
        if cycle_key in self.processed_rings:
            return False
        
        # Verify all edges exist in the cycle
        for i in range(len(nodes)):
            from_node = nodes[i]
            to_node = nodes[(i + 1) % len(nodes)]
            if not self.graph.has_edge(from_node, to_node):
                return False
        
        self.processed_rings.add(cycle_key)
        return True
    
    def get_cycle_statistics(self) -> Dict:
        """
        Get statistics about detected cycles.
        
        Returns:
            Dictionary with cycle statistics
        """
        stats = {
            'total_cycles': len(self.cycles_found),
            'cycles_by_length': defaultdict(int),
            'total_accounts_involved': 0,
            'total_transaction_volume': 0,
            'average_cycle_length': 0
        }
        
        accounts = set()
        total_length = 0
        
        for cycle in self.cycles_found:
            length = cycle['length']
            stats['cycles_by_length'][f'length_{length}'] += 1
            accounts.update(cycle['nodes'])
            stats['total_transaction_volume'] += cycle['total_amount']
            total_length += length
        
        stats['total_accounts_involved'] = len(accounts)
        if self.cycles_found:
            stats['average_cycle_length'] = total_length / len(self.cycles_found)
        
        return stats