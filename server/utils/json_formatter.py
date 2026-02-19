import json
import pandas as pd
from typing import Dict, List, Any
import numpy as np

class JSONFormatter:
    """Format detection results to required JSON structure"""
    
    def format_output(self, transactions_df: pd.DataFrame, rings: List[Dict], 
                     account_scores: Dict[str, float], ring_scores: Dict[str, float],
                     processing_time: float) -> Dict:
        """Format output according to specification"""
        
        # Get all unique accounts
        all_accounts = set(transactions_df['sender_id'].unique()) | set(transactions_df['receiver_id'].unique())
        
        # Build suspicious accounts list
        suspicious_accounts = []
        for ring in rings:
            for account in ring['member_accounts']:
                if account in all_accounts:
                    suspicious_accounts.append({
                        'account_id': str(account),
                        'suspicion_score': round(float(account_scores.get(account, 50.0)), 2),
                        'detected_patterns': ring['detected_patterns'],
                        'ring_id': ring['ring_id']
                    })
        
        # Sort by suspicion score descending
        suspicious_accounts.sort(key=lambda x: x['suspicion_score'], reverse=True)
        
        # Build fraud rings list
        fraud_rings = []
        for ring in rings:
            fraud_rings.append({
                'ring_id': ring['ring_id'],
                'member_accounts': [str(acc) for acc in ring['member_accounts']],
                'pattern_type': ring['pattern_type'],
                'risk_score': round(float(ring_scores.get(ring['ring_id'], 50.0)), 2)
            })
        
        # Build summary
        summary = {
            'total_accounts_analyzed': len(all_accounts),
            'suspicious_accounts_flagged': len(suspicious_accounts),
            'fraud_rings_detected': len(fraud_rings),
            'processing_time_seconds': round(processing_time, 2)
        }
        
        return {
            'suspicious_accounts': suspicious_accounts,
            'fraud_rings': fraud_rings,
            'summary': summary
        }
    
    def to_json_file(self, data: Dict, filepath: str):
        """Write data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def to_json_string(self, data: Dict) -> str:
        """Convert data to JSON string"""
        return json.dumps(data, indent=2)
