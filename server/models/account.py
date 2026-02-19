"""
Account Model
Represents a bank account involved in transactions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, List, Dict, Any, Optional
from collections import defaultdict

@dataclass
class Account:
    """
    Data model for a bank account.
    
    Attributes:
        account_id: Unique identifier for the account
        transactions: Set of transaction IDs involving this account
        first_seen: First transaction timestamp
        last_seen: Last transaction timestamp
        total_sent: Total amount sent
        total_received: Total amount received
        metadata: Additional account metadata
    """
    
    account_id: str
    transactions: Set[str] = field(default_factory=set)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_sent: float = 0.0
    total_received: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Internal caches
    _senders: Set[str] = field(default_factory=set, repr=False)
    _receivers: Set[str] = field(default_factory=set, repr=False)
    _amounts: List[float] = field(default_factory=list, repr=False)
    _timestamps: List[datetime] = field(default_factory=list, repr=False)
    
    def add_transaction(self, transaction_id: str, amount: float, 
                       timestamp: datetime, is_sender: bool, counterparty: str):
        """
        Add a transaction to this account's history.
        
        Args:
            transaction_id: ID of the transaction
            amount: Transaction amount
            timestamp: When transaction occurred
            is_sender: True if this account was the sender
            counterparty: The other account involved
        """
        self.transactions.add(transaction_id)
        self._amounts.append(amount)
        self._timestamps.append(timestamp)
        
        if is_sender:
            self.total_sent += amount
            self._receivers.add(counterparty)
        else:
            self.total_received += amount
            self._senders.add(counterparty)
        
        # Update first/last seen
        if self.first_seen is None or timestamp < self.first_seen:
            self.first_seen = timestamp
        if self.last_seen is None or timestamp > self.last_seen:
            self.last_seen = timestamp
    
    @property
    def transaction_count(self) -> int:
        """Get total number of transactions"""
        return len(self.transactions)
    
    @property
    def unique_senders(self) -> int:
        """Get number of unique senders to this account"""
        return len(self._senders)
    
    @property
    def unique_receivers(self) -> int:
        """Get number of unique receivers from this account"""
        return len(self._receivers)
    
    @property
    def avg_amount(self) -> float:
        """Get average transaction amount"""
        if not self._amounts:
            return 0.0
        return sum(self._amounts) / len(self._amounts)
    
    @property
    def total_volume(self) -> float:
        """Get total transaction volume (sent + received)"""
        return self.total_sent + self.total_received
    
    @property
    def net_flow(self) -> float:
        """Get net flow (received - sent)"""
        return self.total_received - self.total_sent
    
    @property
    def activity_days(self) -> float:
        """Get number of days between first and last transaction"""
        if not self.first_seen or not self.last_seen:
            return 0.0
        delta = self.last_seen - self.first_seen
        return delta.total_seconds() / (24 * 3600)
    
    @property
    def transaction_rate(self) -> float:
        """Get average transactions per day"""
        days = self.activity_days
        if days == 0:
            return self.transaction_count
        return self.transaction_count / days
    
    def get_suspicion_indicators(self) -> Dict[str, float]:
        """
        Calculate suspicion indicators for this account.
        
        Returns:
            Dictionary of indicator scores (0-1)
        """
        indicators = {}
        
        # Round amount indicator
        if self._amounts:
            round_count = sum(1 for amt in self._amounts 
                            if amt % 1000 == 0 or amt % 500 == 0)
            indicators['round_amounts'] = round_count / len(self._amounts)
        
        # In/out ratio indicator
        if self.total_received > 0 and self.total_sent > 0:
            ratio = self.total_sent / self.total_received
            indicators['balanced_flow'] = 1.0 - abs(1.0 - ratio)  # Closer to 1 is higher
        
        # Night transaction indicator
        if self._timestamps:
            night_count = sum(1 for ts in self._timestamps 
                            if ts.hour >= 23 or ts.hour <= 5)
            indicators['night_transactions'] = night_count / len(self._timestamps)
        
        # Weekend transaction indicator
        if self._timestamps:
            weekend_count = sum(1 for ts in self._timestamps if ts.weekday() >= 5)
            indicators['weekend_transactions'] = weekend_count / len(self._timestamps)
        
        # Counterparty concentration
        total_counterparties = self.unique_senders + self.unique_receivers
        if total_counterparties > 0:
            indicators['concentration'] = 1.0 - (total_counterparties / self.transaction_count)
        
        return indicators
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'account_id': self.account_id,
            'transaction_count': self.transaction_count,
            'first_seen': self.first_seen.strftime('%Y-%m-%d %H:%M:%S') if self.first_seen else None,
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S') if self.last_seen else None,
            'total_sent': self.total_sent,
            'total_received': self.total_received,
            'net_flow': self.net_flow,
            'total_volume': self.total_volume,
            'avg_amount': self.avg_amount,
            'unique_senders': self.unique_senders,
            'unique_receivers': self.unique_receivers,
            'activity_days': round(self.activity_days, 2),
            'transaction_rate': round(self.transaction_rate, 2),
            'suspicion_indicators': self.get_suspicion_indicators()
        }
    
    def __hash__(self) -> int:
        return hash(self.account_id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Account):
            return False
        return self.account_id == other.account_id