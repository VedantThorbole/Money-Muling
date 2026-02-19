"""
Transaction Model
Represents a single financial transaction between accounts
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

@dataclass
class Transaction:
    """
    Data model for a financial transaction.
    
    Attributes:
        transaction_id: Unique identifier for the transaction
        sender_id: Account ID of the sender
        receiver_id: Account ID of the receiver
        amount: Transaction amount
        timestamp: When the transaction occurred
        metadata: Additional transaction metadata
    """
    
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate transaction data after initialization"""
        if self.amount <= 0:
            raise ValueError(f"Transaction amount must be positive: {self.amount}")
        
        if self.sender_id == self.receiver_id:
            raise ValueError(f"Self-transaction detected: {self.transaction_id}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Create a Transaction from a dictionary.
        
        Args:
            data: Dictionary with transaction data
            
        Returns:
            Transaction instance
        """
        # Parse timestamp if it's a string
        timestamp = data['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        return cls(
            transaction_id=str(data['transaction_id']),
            sender_id=str(data['sender_id']),
            receiver_id=str(data['receiver_id']),
            amount=float(data['amount']),
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Transaction to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'transaction_id': self.transaction_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'amount': self.amount,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'metadata': self.metadata
        }
    
    def to_json_compatible(self) -> Dict[str, Any]:
        """Return JSON-serializable dictionary"""
        return self.to_dict()
    
    @property
    def is_suspicious_amount(self) -> bool:
        """Check if amount is suspicious (round number)"""
        return self.amount % 1000 == 0 or self.amount % 500 == 0
    
    @property
    def is_night_transaction(self) -> bool:
        """Check if transaction occurred at night (11 PM - 5 AM)"""
        return self.timestamp.hour >= 23 or self.timestamp.hour <= 5
    
    @property
    def is_weekend_transaction(self) -> bool:
        """Check if transaction occurred on weekend"""
        return self.timestamp.weekday() >= 5
    
    def __hash__(self) -> int:
        return hash(self.transaction_id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Transaction):
            return False
        return self.transaction_id == other.transaction_id