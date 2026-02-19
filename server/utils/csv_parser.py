import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, List, Dict

class CSVParser:
    """CSV parsing and validation utility"""
    
    REQUIRED_COLUMNS = ['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp']
    
    def parse(self, file_path: str) -> pd.DataFrame:
        """Parse CSV file and return validated DataFrame"""
        
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Validate columns
        self._validate_columns(df)
        
        # Clean data
        df = self._clean_data(df)
        
        # Validate data types
        df = self._validate_data_types(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['transaction_id'])
        
        return df
    
    def _validate_columns(self, df: pd.DataFrame):
        """Check if all required columns exist"""
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data"""
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['sender_id', 'receiver_id', 'amount'])
        
        # Strip whitespace from string columns
        for col in ['transaction_id', 'sender_id', 'receiver_id']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Convert amount to float, handle errors
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['amount'])
        df = df[df['amount'] > 0]  # Remove zero/negative amounts
        
        return df
    
    def _validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and convert data types"""
        
        # Convert timestamp
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except:
            raise ValueError("Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS")
        
        # Ensure IDs are strings
        df['sender_id'] = df['sender_id'].astype(str)
        df['receiver_id'] = df['receiver_id'].astype(str)
        df['transaction_id'] = df['transaction_id'].astype(str)
        
        return df
    
    def generate_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics"""
        return {
            'total_transactions': len(df),
            'unique_senders': df['sender_id'].nunique(),
            'unique_receivers': df['receiver_id'].nunique(),
            'unique_accounts': len(set(df['sender_id'].unique()) | set(df['receiver_id'].unique())),
            'total_amount': df['amount'].sum(),
            'avg_amount': df['amount'].mean(),
            'max_amount': df['amount'].max(),
            'min_amount': df['amount'].min(),
            'date_range': {
                'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
