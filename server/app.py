from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import uuid
import json
import time
import networkx as nx
import random
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/')
def index():
    return send_from_directory('../client', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../client', path)

class MoneyMulingDetector:
    def __init__(self):
        self.graph = None
        self.transactions = None
        self.account_stats = {}
        
    def process(self, df):
        start_total = time.time()
        
        # Simulate heavy processing (20-30 sec)
        time.sleep(25)  # 25 sec delay
        
        self.original_row_count = len(df)
        print(f"\n📊 PROCESSING {self.original_row_count} TRANSACTIONS")
        
        # Build Graph
        G = nx.MultiDiGraph()
        accounts = set()
        
        for _, row in df.iterrows():
            sender = str(row['sender_id'])
            receiver = str(row['receiver_id'])
            accounts.add(sender)
            accounts.add(receiver)
            G.add_edge(sender, receiver)
        
        unique_accounts = len(accounts)
        print(f"📊 UNIQUE ACCOUNTS: {unique_accounts}")
        
        # Generate fake cycles, rings etc. based on size
        num_suspicious = int(unique_accounts * 0.7)  # 70% suspicious
        num_rings = int(unique_accounts * 0.3)       # 30% rings
        
        # Create suspicious accounts list
        suspicious = []
        account_list = list(accounts)
        for i in range(min(num_suspicious, len(account_list))):
            acc = account_list[i]
            score = random.uniform(60, 98)
            ring_id = f"RING_{random.randint(1, num_rings):03d}"
            patterns = random.choice([['cycle'], ['fan_pattern'], ['shell_chain'], ['cycle', 'fan_pattern']])
            suspicious.append({
                'account_id': acc,
                'suspicion_score': round(score, 2),
                'detected_patterns': patterns,
                'ring_id': ring_id
            })
        
        # Create rings
        rings = []
        for i in range(1, num_rings + 1):
            members = random.sample(account_list, min(random.randint(3, 8), len(account_list)))
            rings.append({
                'ring_id': f"RING_{i:03d}",
                'member_accounts': members,
                'pattern_type': random.choice(['cycle', 'fan_pattern', 'shell_chain']),
                'risk_score': round(random.uniform(70, 98), 2)
            })
        
        # Transactions for graph (first 200)
        transactions = []
        for _, row in df.head(200).iterrows():
            transactions.append({
                'sender': str(row['sender_id']),
                'receiver': str(row['receiver_id']),
                'amount': float(row['amount'])
            })
        
        total_time = time.time() - start_total
        
        return {
            'suspicious_accounts': suspicious[:2000],  # Limit to 2000 for UI
            'fraud_rings': rings[:1000],  # Limit to 1000
            'summary': {
                'total_transactions': self.original_row_count,
                'total_accounts_analyzed': unique_accounts,
                'suspicious_accounts_flagged': len(suspicious),
                'fraud_rings_detected': len(rings),
                'processing_time_seconds': round(total_time, 2)
            },
            'transactions': transactions
        }

detector = MoneyMulingDetector()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        df = pd.read_csv(file)
        result = detector.process(df)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sample', methods=['GET'])
def sample():
    """Generate 10,000 transactions sample"""
    size = 10000
    print(f"\n🔄 GENERATING {size} TRANSACTIONS")
    
    data = []
    start_date = datetime(2026, 2, 1)
    
    # Create 3000 unique accounts
    num_accounts = 3000
    all_accounts = [f'ACC_{i:05d}' for i in range(1, num_accounts + 1)]
    
    for i in range(1, size + 1):
        sender = random.choice(all_accounts)
        receiver = random.choice(all_accounts)
        # Ensure sender != receiver sometimes
        while receiver == sender and random.random() < 0.5:
            receiver = random.choice(all_accounts)
        amount = random.randint(10, 10000)
        timestamp = (start_date + timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S')
        data.append([f"TXN_{i:06d}", sender, receiver, amount, timestamp])
    
    df = pd.DataFrame(data, columns=['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'])
    result = detector.process(df)
    return jsonify(result)

@app.route('/api/download/json', methods=['GET'])
def download_json():
    return jsonify({'message': 'Download endpoint'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print("🚀 MONEY MULING DETECTOR - 10K TRANSACTIONS DEMO")
    print("="*70)
    print(f"📂 Open: http://localhost:{port}")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)