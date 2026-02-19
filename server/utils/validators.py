import pandas as pd
from typing import Tuple, List

class Validator:
    """Data validator for transaction CSV"""
    
    def validate_transactions(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate transaction data"""
        errors = []
        
        # Check for self-transactions
        self_tx = df[df['sender_id'] == df['receiver_id']]
        if not self_tx.empty:
            errors.append(f"Found {len(self_tx)} self-transactions")
        
        # Check for suspiciously round amounts
        round_amounts = df[df['amount'] % 1000 == 0]
        if len(round_amounts) > len(df) * 0.5:
            errors.append("High proportion of round-number amounts")
        
        # Check timestamp order
        if not df['timestamp'].is_monotonic_increasing:
            errors.append("Timestamps are not in chronological order")
        
        # Check for duplicate transactions
        duplicates = df.duplicated(subset=['transaction_id'])
        if duplicates.any():
            errors.append(f"Found {duplicates.sum()} duplicate transaction IDs")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def validate_output(self, output: dict) -> Tuple[bool, List[str]]:
        """Validate output JSON structure"""
        errors = []
        
        # Check required top-level fields
        required_fields = ['suspicious_accounts', 'fraud_rings', 'summary']
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate suspicious_accounts structure
        for acc in output['suspicious_accounts']:
            if not all(k in acc for k in ['account_id', 'suspicion_score', 'detected_patterns', 'ring_id']):
                errors.append("Invalid suspicious_accounts entry structure")
                break
        
        # Validate fraud_rings structure
        for ring in output['fraud_rings']:
            if not all(k in ring for k in ['ring_id', 'member_accounts', 'pattern_type', 'risk_score']):
                errors.append("Invalid fraud_rings entry structure")
                break
        
        # Validate summary
        summary = output['summary']
        required_summary = ['total_accounts_analyzed', 'suspicious_accounts_flagged', 
                          'fraud_rings_detected', 'processing_time_seconds']
        if not all(k in summary for k in required_summary):
            errors.append("Invalid summary structure")
        
        return len(errors) == 0, errors
