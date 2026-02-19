"""
Shell Chain Detection Algorithm for Money Muling
Detects layered networks where intermediate nodes have low activity
"""

import networkx as nx
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import numpy as np

class ChainDetector:
    """
    Detects shell chains where money flows through multiple accounts
    with intermediate nodes showing low transaction activity.
    These are typical in layered money muling networks.
    """
    
    def __init__(self, graph: nx.DiGraph, min_chain_length: int = 3, 
                 max_transactions_per_shell: int = 5):
        """
        Initialize the chain detector.
        
        Args:
            graph: NetworkX directed graph
            min_chain_length: Minimum chain length to detect (default: 3)
            max_transactions_per_shell: Max transactions for shell accounts (default: 5)
        """
        self.graph = graph
        self.min_length = min_chain_length
        self.max_shell_tx = max_transactions_per_shell
        self.chains_found = []
        self.chain_id_counter = 0
        self.shell_accounts = self._identify_shell_accounts()
    
    def _identify_shell_accounts(self) -> Set[str]:
        """
        Identify potential shell accounts based on low transaction activity.
        
        Returns:
            Set of account IDs that are likely shell accounts
        """
        shell_accounts = set()
        
        for node in self.graph.nodes():
            # Count total transactions (in + out)
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            total_tx = in_degree + out_degree
            
            # Check if account has low activity
            if 1 <= total_tx <= self.max_shell_tx:
                # Also check if amounts are consistently similar
                amounts = self._get_transaction_amounts(node)
                if amounts and self._are_amounts_similar(amounts):
                    shell_accounts.add(node)
        
        return shell_accounts
    
    def _get_transaction_amounts(self, node: str) -> List[float]:
        """
        Get all transaction amounts involving a node.
        
        Args:
            node: Account ID
            
        Returns:
            List of transaction amounts
        """
        amounts = []
        
        # Incoming transactions
        for predecessor in self.graph.predecessors(node):
            edge_data = self.graph.get_edge_data(predecessor, node)
            if isinstance(edge_data, dict):
                if 'amount' in edge_data:
                    amounts.append(edge_data['amount'])
                else:
                    for tx_data in edge_data.values():
                        if isinstance(tx_data, dict) and 'amount' in tx_data:
                            amounts.append(tx_data['amount'])
        
        # Outgoing transactions
        for successor in self.graph.successors(node):
            edge_data = self.graph.get_edge_data(node, successor)
            if isinstance(edge_data, dict):
                if 'amount' in edge_data:
                    amounts.append(edge_data['amount'])
                else:
                    for tx_data in edge_data.values():
                        if isinstance(tx_data, dict) and 'amount' in tx_data:
                            amounts.append(tx_data['amount'])
        
        return amounts
    
    def _are_amounts_similar(self, amounts: List[float], tolerance: float = 0.2) -> bool:
        """
        Check if amounts are within tolerance (shell accounts often pass similar amounts).
        
        Args:
            amounts: List of amounts
            tolerance: Relative tolerance for similarity (default: 0.2 or 20%)
            
        Returns:
            True if amounts are similar
        """
        if len(amounts) < 2:
            return True
        
        mean_amount = np.mean(amounts)
        if mean_amount == 0:
            return False
        
        max_deviation = max(abs(a - mean_amount) / mean_amount for a in amounts)
        return max_deviation <= tolerance
    
    def detect_shell_chains(self) -> List[Dict]:
        """
        Detect shell chains in the graph.
        
        Returns:
            List of shell chains detected
        """
        shell_chains = []
        
        # Start from each shell account
        for start_node in self.shell_accounts:
            # Find all paths starting from this node
            paths = self._find_paths_from_node(start_node, [start_node])
            
            for path in paths:
                if len(path) >= self.min_length and self._is_shell_chain(path):
                    chain_dict = self._create_chain_dict(path)
                    shell_chains.append(chain_dict)
                    self.chains_found.append(chain_dict)
        
        return shell_chains
    
    def _find_paths_from_node(self, current_node: str, current_path: List[str]) -> List[List[str]]:
        """
        DFS to find all paths from current_node.
        
        Args:
            current_node: Current node in DFS
            current_path: Path taken so far
            
        Returns:
            List of all paths found
        """
        paths = []
        
        # If we've reached minimum length, record the path
        if len(current_path) >= self.min_length:
            paths.append(current_path.copy())
        
        # Stop if path is getting too long (avoid exponential explosion)
        if len(current_path) >= self.min_length * 3:
            return paths
        
        # Explore successors
        for successor in self.graph.successors(current_node):
            # Avoid cycles in path
            if successor not in current_path:
                new_path = current_path + [successor]
                paths.extend(self._find_paths_from_node(successor, new_path))
        
        return paths
    
    def _is_shell_chain(self, path: List[str]) -> bool:
        """
        Check if a path forms a valid shell chain.
        
        Args:
            path: List of nodes in the path
            
        Returns:
            True if path is a valid shell chain
        """
        if len(path) < self.min_length:
            return False
        
        # First node can be any type, but intermediate nodes must be shells
        for i in range(1, len(path) - 1):  # Exclude first and last
            node = path[i]
            
            # Check if node is a shell account
            if node not in self.shell_accounts:
                return False
            
            # Check if node only appears in this chain context
            if self._node_in_multiple_chains(node, path):
                return False
        
        # Last node should have higher activity (money destination)
        last_node = path[-1]
        last_node_tx = self.graph.in_degree(last_node) + self.graph.out_degree(last_node)
        if last_node_tx <= self.max_shell_tx:
            # If last node is also a shell, chain might be incomplete
            # Still flag as suspicious but with lower confidence
            pass
        
        return True
    
    def _node_in_multiple_chains(self, node: str, current_path: List[str]) -> bool:
        """
        Check if a node appears in multiple chain contexts.
        
        Args:
            node: Node to check
            current_path: Current path being considered
            
        Returns:
            True if node appears in other chains
        """
        # Count occurrences in already found chains
        count = 0
        for chain in self.chains_found:
            if node in chain['nodes']:
                count += 1
        
        return count > 1
    
    def _create_chain_dict(self, path: List[str]) -> Dict:
        """
        Create a chain dictionary with metadata.
        
        Args:
            path: List of nodes in the chain
            
        Returns:
            Dictionary with chain details
        """
        self.chain_id_counter += 1
        
        # Get all edges in the chain
        edges = []
        total_amount = 0
        timestamps = []
        shell_nodes = []
        
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            
            if from_node in self.shell_accounts:
                shell_nodes.append(from_node)
            
            if self.graph.has_edge(from_node, to_node):
                edge_data = self.graph.get_edge_data(from_node, to_node)
                
                if isinstance(edge_data, dict):
                    if 'amount' in edge_data:
                        edges.append({
                            'from': from_node,
                            'to': to_node,
                            'amount': edge_data['amount'],
                            'timestamp': edge_data.get('timestamp', '')
                        })
                        total_amount += edge_data['amount']
                        if edge_data.get('timestamp'):
                            timestamps.append(edge_data['timestamp'])
                    else:
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
        
        # Classify chain type
        if len(shell_nodes) >= len(path) - 2:  # All intermediates are shells
            chain_type = 'pure_shell_chain'
        else:
            chain_type = 'mixed_shell_chain'
        
        return {
            'nodes': path,
            'length': len(path),
            'ring_id': f"CHAIN_RING_{self.chain_id_counter:03d}",
            'pattern_type': f'{chain_type}_length_{len(path)}',
            'shell_nodes': shell_nodes,
            'shell_count': len(shell_nodes),
            'edges': edges,
            'total_amount': total_amount,
            'transaction_count': len(edges),
            'avg_amount_per_transaction': total_amount / len(edges) if edges else 0,
            'timestamp_range': [min(timestamps), max(timestamps)] if timestamps else []
        }
    
    def get_chain_statistics(self) -> Dict:
        """
        Get statistics about detected shell chains.
        
        Returns:
            Dictionary with chain statistics
        """
        stats = {
            'total_chains': len(self.chains_found),
            'chains_by_length': defaultdict(int),
            'pure_shell_chains': 0,
            'mixed_shell_chains': 0,
            'total_accounts_involved': 0,
            'total_shell_accounts': len(self.shell_accounts),
            'shell_accounts_used': set(),
            'total_transaction_volume': 0,
            'average_chain_length': 0
        }
        
        accounts = set()
        total_length = 0
        
        for chain in self.chains_found:
            length = chain['length']
            stats['chains_by_length'][f'length_{length}'] += 1
            
            if 'pure_shell' in chain['pattern_type']:
                stats['pure_shell_chains'] += 1
            else:
                stats['mixed_shell_chains'] += 1
            
            accounts.update(chain['nodes'])
            stats['shell_accounts_used'].update(chain['shell_nodes'])
            stats['total_transaction_volume'] += chain['total_amount']
            total_length += length
        
        stats['total_accounts_involved'] = len(accounts)
        stats['shell_accounts_used'] = len(stats['shell_accounts_used'])
        
        if self.chains_found:
            stats['average_chain_length'] = total_length / len(self.chains_found)
        
        return stats