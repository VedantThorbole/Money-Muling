from typing import List, Dict, Set
import uuid

class FraudRingBuilder:
    """Build fraud rings from detected patterns"""
    
    def __init__(self):
        self.ring_counter = 0
        self.processed_accounts = set()
        
    def build_rings(self, cycles: List[Dict], fan_patterns: List[Dict], 
                   chains: List[Dict]) -> List[Dict]:
        """Combine all patterns into fraud rings"""
        all_rings = []
        
        # Process cycles
        for cycle in cycles:
            ring = self._create_ring(
                pattern_type=cycle['pattern_type'],
                nodes=cycle['nodes'],
                detected_patterns=[cycle['pattern_type']],
                metadata=cycle
            )
            all_rings.append(ring)
        
        # Process fan patterns
        for fan in fan_patterns:
            ring = self._create_ring(
                pattern_type=fan['pattern_type'],
                nodes=fan['nodes'],
                detected_patterns=['fan_pattern'],
                metadata=fan
            )
            all_rings.append(ring)
        
        # Process chains
        for chain in chains:
            ring = self._create_ring(
                pattern_type=chain['pattern_type'],
                nodes=chain['nodes'],
                detected_patterns=['shell_chain'],
                metadata=chain
            )
            all_rings.append(ring)
        
        # Merge overlapping rings
        all_rings = self._merge_overlapping_rings(all_rings)
        
        return all_rings
    
    def _create_ring(self, pattern_type: str, nodes: List[str], 
                    detected_patterns: List[str], metadata: Dict) -> Dict:
        """Create a fraud ring entry"""
        self.ring_counter += 1
        ring_id = f"RING_{self.ring_counter:03d}"
        
        # Add all nodes to processed set
        for node in nodes:
            self.processed_accounts.add(node)
        
        return {
            'ring_id': ring_id,
            'member_accounts': nodes,
            'pattern_type': pattern_type,
            'detected_patterns': detected_patterns,
            'metadata': metadata
        }
    
    def _merge_overlapping_rings(self, rings: List[Dict]) -> List[Dict]:
        """Merge rings that share accounts"""
        if not rings:
            return rings
        
        # Build account to ring mapping
        account_to_rings = {}
        for i, ring in enumerate(rings):
            for account in ring['member_accounts']:
                if account not in account_to_rings:
                    account_to_rings[account] = []
                account_to_rings[account].append(i)
        
        # Find connected components of rings
        ring_graph = {i: set() for i in range(len(rings))}
        for account, ring_indices in account_to_rings.items():
            if len(ring_indices) > 1:
                for i in ring_indices:
                    for j in ring_indices:
                        if i != j:
                            ring_graph[i].add(j)
        
        # Find connected components
        visited = set()
        components = []
        
        for i in range(len(rings)):
            if i not in visited:
                component = []
                stack = [i]
                visited.add(i)
                
                while stack:
                    current = stack.pop()
                    component.append(current)
                    
                    for neighbor in ring_graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
                
                components.append(component)
        
        # Merge rings in each component
        merged_rings = []
        for component in components:
            if len(component) == 1:
                merged_rings.append(rings[component[0]])
            else:
                merged_ring = self._merge_ring_group([rings[i] for i in component])
                merged_rings.append(merged_ring)
        
        return merged_rings
    
    def _merge_ring_group(self, ring_group: List[Dict]) -> Dict:
        """Merge a group of rings into one"""
        # Collect all accounts and patterns
        all_accounts = set()
        all_patterns = set()
        pattern_types = []
        
        for ring in ring_group:
            all_accounts.update(ring['member_accounts'])
            all_patterns.update(ring.get('detected_patterns', []))
            pattern_types.append(ring['pattern_type'])
        
        # Determine primary pattern type
        if any('cycle' in pt for pt in pattern_types):
            primary_type = 'cycle_with_fan'
        elif any('fan' in pt for pt in pattern_types):
            primary_type = 'fan_with_chain'
        else:
            primary_type = 'complex_network'
        
        # Create merged ring
        self.ring_counter += 1
        return {
            'ring_id': f"RING_{self.ring_counter:03d}",
            'member_accounts': list(all_accounts),
            'pattern_type': primary_type,
            'detected_patterns': list(all_patterns),
            'metadata': {'merged_from': len(ring_group)}
        }
