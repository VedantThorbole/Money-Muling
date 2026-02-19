"""
Fraud Ring Model
Represents a detected money muling ring
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import uuid

@dataclass
class FraudRing:
    """
    Data model for a detected fraud ring.
    
    Attributes:
        ring_id: Unique identifier for the ring
        member_accounts: List of account IDs in the ring
        pattern_type: Type of pattern detected
        detection_patterns: List of specific patterns
        risk_score: Calculated risk score (0-100)
        metadata: Additional ring metadata
    """
    
    ring_id: str
    member_accounts: List[str]
    pattern_type: str
    detection_patterns: List[str] = field(default_factory=list)
    risk_score: float = 50.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields
    central_account: Optional[str] = None
    total_volume: float = 0.0
    transaction_count: int = 0
    first_detected: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate ring data after initialization"""
        if not self.ring_id:
            self.ring_id = f"RING_{uuid.uuid4().hex[:8].upper()}"
        
        if not self.member_accounts:
            raise ValueError("Ring must have at least one member account")
        
        # Ensure unique accounts
        self.member_accounts = list(set(self.member_accounts))
    
    @classmethod
    def from_cycle(cls, cycle_data: Dict[str, Any]) -> 'FraudRing':
        """
        Create a fraud ring from cycle detection data.
        
        Args:
            cycle_data: Cycle detection output
            
        Returns:
            FraudRing instance
        """
        return cls(
            ring_id=cycle_data.get('ring_id', f"CYCLE_{uuid.uuid4().hex[:8]}"),
            member_accounts=cycle_data['nodes'],
            pattern_type=cycle_data['pattern_type'],
            detection_patterns=['cycle_detection'],
            metadata={
                'cycle_length': cycle_data['length'],
                'edges': cycle_data.get('edges', []),
                'total_amount': cycle_data.get('total_amount', 0),
                'transaction_count': cycle_data.get('transaction_count', 0)
            }
        )
    
    @classmethod
    def from_fan_pattern(cls, fan_data: Dict[str, Any]) -> 'FraudRing':
        """
        Create a fraud ring from fan pattern detection data.
        
        Args:
            fan_data: Fan pattern detection output
            
        Returns:
            FraudRing instance
        """
        return cls(
            ring_id=fan_data.get('ring_id', f"FAN_{uuid.uuid4().hex[:8]}"),
            member_accounts=fan_data['member_accounts'],
            pattern_type=fan_data['pattern_type'],
            detection_patterns=['fan_pattern'],
            central_account=fan_data['central_node'],
            metadata={
                'direction': fan_data['direction'],
                'transaction_count': fan_data['transaction_count'],
                'total_amount': fan_data['total_amount'],
                'time_span_hours': fan_data.get('time_span_hours', 0),
                'avg_amount': fan_data.get('avg_amount', 0),
                'transaction_rate': fan_data.get('transaction_rate_per_hour', 0)
            }
        )
    
    @classmethod
    def from_chain(cls, chain_data: Dict[str, Any]) -> 'FraudRing':
        """
        Create a fraud ring from shell chain detection data.
        
        Args:
            chain_data: Chain detection output
            
        Returns:
            FraudRing instance
        """
        return cls(
            ring_id=chain_data.get('ring_id', f"CHAIN_{uuid.uuid4().hex[:8]}"),
            member_accounts=chain_data['nodes'],
            pattern_type=chain_data['pattern_type'],
            detection_patterns=['shell_chain'],
            metadata={
                'chain_length': chain_data['length'],
                'shell_nodes': chain_data.get('shell_nodes', []),
                'shell_count': chain_data.get('shell_count', 0),
                'edges': chain_data.get('edges', []),
                'total_amount': chain_data.get('total_amount', 0),
                'transaction_count': chain_data.get('transaction_count', 0)
            }
        )
    
    @property
    def size(self) -> int:
        """Get ring size (number of accounts)"""
        return len(self.member_accounts)
    
    @property
    def is_cycle(self) -> bool:
        """Check if ring is a cycle pattern"""
        return 'cycle' in self.pattern_type
    
    @property
    def is_fan(self) -> bool:
        """Check if ring is a fan pattern"""
        return 'fan' in self.pattern_type
    
    @property
    def is_chain(self) -> bool:
        """Check if ring is a shell chain"""
        return 'chain' in self.pattern_type
    
    def merge_with(self, other: 'FraudRing') -> 'FraudRing':
        """
        Merge this ring with another ring.
        
        Args:
            other: Another fraud ring
            
        Returns:
            New merged ring
        """
        # Combine member accounts
        all_accounts = list(set(self.member_accounts + other.member_accounts))
        
        # Combine patterns
        all_patterns = list(set(self.detection_patterns + other.detection_patterns))
        
        # Determine new pattern type
        if self.is_cycle or other.is_cycle:
            pattern_type = 'cycle_with_fan'
        elif self.is_fan or other.is_fan:
            pattern_type = 'fan_with_chain'
        else:
            pattern_type = 'complex_network'
        
        # Combine metadata
        merged_metadata = {
            'merged_from': [self.ring_id, other.ring_id],
            'original_rings': 2,
            **self.metadata,
            **other.metadata
        }
        
        return FraudRing(
            ring_id=f"RING_MERGED_{uuid.uuid4().hex[:8].upper()}",
            member_accounts=all_accounts,
            pattern_type=pattern_type,
            detection_patterns=all_patterns,
            metadata=merged_metadata,
            total_volume=self.total_volume + other.total_volume,
            transaction_count=self.transaction_count + other.transaction_count
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return {
            'ring_id': self.ring_id,
            'member_accounts': self.member_accounts,
            'pattern_type': self.pattern_type,
            'detected_patterns': self.detection_patterns,
            'risk_score': round(self.risk_score, 2),
            'size': self.size,
            'metadata': self.metadata
        }
    
    def to_json_compatible(self) -> Dict[str, Any]:
        """Return JSON-serializable dictionary (required format)"""
        return {
            'ring_id': self.ring_id,
            'member_accounts': self.member_accounts,
            'pattern_type': self.pattern_type,
            'risk_score': round(self.risk_score, 2)
        }
    
    def __hash__(self) -> int:
        return hash(self.ring_id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, FraudRing):
            return False
        return self.ring_id == other.ring_id