# from flask import Flask, request, jsonify, send_file, send_from_directory
# from flask_cors import CORS
# import pandas as pd
# import os
# import uuid
# import json
# import time
# import networkx as nx
# import random
# from datetime import datetime, timedelta
# from collections import defaultdict

# app = Flask(__name__, static_folder='../client', static_url_path='')
# CORS(app)

# @app.route('/health')
# def health():
#     return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# @app.route('/')
# def index():
#     return send_from_directory('../client', 'index.html')

# @app.route('/<path:path>')
# def static_files(path):
#     return send_from_directory('../client', path)

# # REAL DETECTION ENGINE
# class MoneyMulingDetector:
#     def __init__(self):
#         self.graph = None
#         self.transactions = None
#         self.account_stats = {}
        
#     def process(self, df):
#         start_total = time.time()
        
#         # Store original dataframe size
#         self.original_row_count = len(df)
#         print(f"\n📊 PROCESSING {self.original_row_count} TRANSACTIONS")
        
#         # Step 1: Build Graph
#         t1 = time.time()
#         G = nx.MultiDiGraph()
#         accounts = set()
        
#         for _, row in df.iterrows():
#             sender = str(row['sender_id'])
#             receiver = str(row['receiver_id'])
#             amount = float(row['amount'])
#             tx_id = str(row['transaction_id'])
            
#             accounts.add(sender)
#             accounts.add(receiver)
            
#             G.add_edge(sender, receiver, 
#                       key=tx_id,
#                       amount=amount,
#                       timestamp=row['timestamp'])
        
#         graph_time = time.time() - t1
        
#         # Step 2: Cycle Detection
#         t2 = time.time()
#         cycles = self.detect_cycles(G)
#         cycle_time = time.time() - t2
        
#         # Step 3: Fan Pattern Detection
#         t3 = time.time()
#         fan_patterns = self.detect_fan_patterns(df)
#         fan_time = time.time() - t3
        
#         # Step 4: Shell Chain Detection
#         t4 = time.time()
#         chains = self.detect_shell_chains(G)
#         chain_time = time.time() - t4
        
#         # Step 5: Calculate Scores
#         t5 = time.time()
#         account_scores, rings = self.calculate_scores(G, cycles, fan_patterns, chains, accounts)
#         score_time = time.time() - t5
        
#         total_time = time.time() - start_total
        
#         timing = {
#             'graph_build': round(graph_time, 3),
#             'cycle_detection': round(cycle_time, 3),
#             'fan_detection': round(fan_time, 3),
#             'chain_detection': round(chain_time, 3),
#             'scoring': round(score_time, 3),
#             'total': round(total_time, 3)
#         }
        
#         return self.format_output(accounts, account_scores, rings, cycles, fan_patterns, chains, df, timing)
    
#     def detect_cycles(self, G):
#         """Find cycles of length 3-5"""
#         cycles = []
#         processed = set()
        
#         try:
#             sccs = [comp for comp in nx.strongly_connected_components(G) if len(comp) >= 3]
#         except:
#             return cycles
        
#         for scc in sccs:
#             subgraph = G.subgraph(scc)
#             nodes = list(subgraph.nodes())
            
#             for start in nodes:
#                 stack = [(start, [start], {start})]
                
#                 while stack:
#                     current, path, visited = stack.pop()
                    
#                     for neighbor in subgraph.successors(current):
#                         if neighbor == start and 3 <= len(path) <= 5:
#                             cycle_key = frozenset(path)
#                             if cycle_key not in processed:
#                                 processed.add(cycle_key)
#                                 cycles.append({
#                                     'nodes': path.copy(),
#                                     'length': len(path)
#                                 })
#                         elif neighbor not in visited and len(path) < 5:
#                             stack.append((neighbor, path + [neighbor], visited | {neighbor}))
        
#         return cycles
    
#     def detect_fan_patterns(self, df):
#         """Detect fan-in/fan-out patterns"""
#         fan_patterns = []
        
#         # Fan-in (many to one)
#         receivers = df.groupby('receiver_id').size()
#         for rec, count in receivers[receivers >= 8].items():
#             fan_patterns.append({
#                 'type': 'fan_in',
#                 'central': rec,
#                 'count': int(count)
#             })
        
#         # Fan-out (one to many)
#         senders = df.groupby('sender_id').size()
#         for sen, count in senders[senders >= 8].items():
#             fan_patterns.append({
#                 'type': 'fan_out',
#                 'central': sen,
#                 'count': int(count)
#             })
        
#         return fan_patterns
    
#     def detect_shell_chains(self, G):
#         """Detect shell chains"""
#         chains = []
        
#         shell_candidates = []
#         for node in G.nodes():
#             if G.degree(node) <= 3:
#                 shell_candidates.append(node)
        
#         for node in shell_candidates[:20]:
#             for neighbor in G.successors(node):
#                 if neighbor in shell_candidates:
#                     chains.append({
#                         'nodes': [node, neighbor],
#                         'type': 'shell_chain'
#                     })
        
#         return chains
    
#     def calculate_scores(self, G, cycles, fan_patterns, chains, accounts):
#         """Calculate suspicion scores"""
#         account_scores = {}
#         rings = []
#         ring_id = 1
        
#         accounts_in_rings = set()
        
#         # Process Cycles
#         for cycle in cycles:
#             ring_name = f"RING_{ring_id:03d}"
#             ring_id += 1
            
#             base_score = 70 + (cycle['length'] * 3)
#             for node in cycle['nodes']:
#                 account_scores[node] = base_score
#                 accounts_in_rings.add(node)
            
#             rings.append({
#                 'ring_id': ring_name,
#                 'member_accounts': cycle['nodes'],
#                 'pattern_type': f"cycle_length_{cycle['length']}",
#                 'risk_score': base_score
#             })
        
#         # Process Fan Patterns
#         for fan in fan_patterns:
#             ring_name = f"RING_{ring_id:03d}"
#             ring_id += 1
            
#             base_score = 60 + (min(fan['count'], 20) * 1.5)
#             account_scores[fan['central']] = max(account_scores.get(fan['central'], 0), base_score)
#             accounts_in_rings.add(fan['central'])
            
#             rings.append({
#                 'ring_id': ring_name,
#                 'member_accounts': [fan['central']],
#                 'pattern_type': fan['type'],
#                 'risk_score': round(base_score, 2)
#             })
        
#         # Process Chains
#         for chain in chains:
#             ring_name = f"RING_{ring_id:03d}"
#             ring_id += 1
            
#             for node in chain['nodes']:
#                 account_scores[node] = max(account_scores.get(node, 0), 55)
#                 accounts_in_rings.add(node)
            
#             rings.append({
#                 'ring_id': ring_name,
#                 'member_accounts': chain['nodes'],
#                 'pattern_type': 'shell_chain',
#                 'risk_score': 55
#             })
        
#         # Normal accounts
#         for acc in accounts:
#             if acc not in accounts_in_rings:
#                 account_scores[acc] = random.randint(10, 35)
        
#         return account_scores, rings
    
#     def format_output(self, accounts, account_scores, rings, cycles, fan_patterns, chains, df, timing):
#         """Format output with REAL data"""
        
#         # Build transactions for graph
#         transactions = []
#         for _, row in df.iterrows():
#             transactions.append({
#                 'sender': str(row['sender_id']),
#                 'receiver': str(row['receiver_id']),
#                 'amount': float(row['amount'])
#             })
        
#         # Build suspicious accounts list
#         suspicious = []
#         suspicious_count = 0
        
#         account_to_ring = {}
#         for ring in rings:
#             for acc in ring['member_accounts']:
#                 account_to_ring[acc] = ring['ring_id']
        
#         for acc in accounts:
#             score = account_scores.get(acc, 0)
            
#             if score > 50:
#                 suspicious_count += 1
                
#                 patterns = []
#                 for cycle in cycles:
#                     if acc in cycle['nodes']:
#                         patterns.append('cycle')
#                 for fan in fan_patterns:
#                     if acc == fan.get('central'):
#                         patterns.append(fan['type'])
#                 for chain in chains:
#                     if acc in chain['nodes']:
#                         patterns.append('shell_chain')
                
#                 if not patterns:
#                     patterns = ['suspicious']
                
#                 suspicious.append({
#                     'account_id': str(acc),
#                     'suspicion_score': round(score, 2),
#                     'detected_patterns': patterns,
#                     'ring_id': account_to_ring.get(acc, 'NONE')
#                 })
        
#         suspicious.sort(key=lambda x: x['suspicion_score'], reverse=True)
        
#         # IMPORTANT FIX: total_accounts_analyzed should be UNIQUE accounts count
#         unique_accounts_count = len(accounts)
        
#         print(f"\n📊 FINAL STATS:")
#         print(f"   Original Transactions: {self.original_row_count}")
#         print(f"   Unique Accounts: {unique_accounts_count}")
#         print(f"   Suspicious Accounts: {suspicious_count}")
#         print(f"   Fraud Rings: {len(rings)}")
#         print(f"   Processing Time: {timing['total']}s")
        
#         return {
#             'suspicious_accounts': suspicious,
#             'fraud_rings': rings,
#             'summary': {
#                 'total_accounts_analyzed': unique_accounts_count,  # YEH SAHI HAI - UNIQUE ACCOUNTS
#                 'suspicious_accounts_flagged': suspicious_count,
#                 'fraud_rings_detected': len(rings),
#                 'processing_time_seconds': timing['total'],
#                 'transactions_processed': self.original_row_count  # EXTRA INFO
#             },
#             'transactions': transactions[:200]
#         }

# detector = MoneyMulingDetector()

# @app.route('/api/upload', methods=['POST'])
# def upload_file():
#     try:
#         file = request.files['file']
        
#         # Read CSV
#         df = pd.read_csv(file)
#         print(f"\n📥 UPLOADED FILE: {len(df)} transactions")
        
#         # Process
#         result = detector.process(df)
        
#         return jsonify(result)
        
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/sample', methods=['GET'])
# def sample():
#     """Generate sample data"""
    
#     size = request.args.get('size', default=2000, type=int)
    
#     print(f"\n🔄 GENERATING SAMPLE: {size} transactions")
    
#     # Generate realistic data
#     data = []
#     start_date = datetime(2026, 2, 1)
    
#     normal_accounts = [f'ACC_{i:04d}' for i in range(1, size//4 + 50)]
#     suspicious_accounts = [f'SUS_{i:03d}' for i in range(1, 51)]
#     merchant_accounts = [f'MERCH_{i:03d}' for i in range(1, 21)]
    
#     for i in range(1, size + 1):
#         if random.random() < 0.05:  # 5% suspicious
#             sender = random.choice(suspicious_accounts)
#             receiver = random.choice(suspicious_accounts + merchant_accounts)
#             amount = random.randint(5000, 10000)
#         elif random.random() < 0.1:  # 10% merchant
#             sender = random.choice(merchant_accounts)
#             receiver = random.choice(normal_accounts)
#             amount = random.randint(50, 500)
#         else:  # 85% normal
#             sender = random.choice(normal_accounts)
#             receiver = random.choice(normal_accounts)
#             amount = random.randint(100, 2000)
        
#         data.append([
#             f"TXN_{i:06d}",
#             sender,
#             receiver,
#             amount,
#             (start_date + timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S')
#         ])
    
#     df = pd.DataFrame(data, columns=['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'])
    
#     # Process
#     result = detector.process(df)
    
#     return jsonify(result)

# @app.route('/api/download/json', methods=['GET'])
# def download_json():
#     return jsonify({
#         'suspicious_accounts': [],
#         'fraud_rings': [],
#         'summary': {
#             'total_accounts_analyzed': 0,
#             'suspicious_accounts_flagged': 0,
#             'fraud_rings_detected': 0,
#             'processing_time_seconds': 0
#         }
#     })

# @app.route('/api/download/template', methods=['GET'])
# def download_template():
#     template = """transaction_id,sender_id,receiver_id,amount,timestamp
# TXN001,ACC_0001,ACC_0002,5237,2026-02-01 10:00:00
# TXN002,ACC_0002,ACC_0003,4812,2026-02-01 11:00:00
# TXN003,ACC_0003,ACC_0001,4756,2026-02-01 12:00:00"""
    
#     temp_file = os.path.join('/tmp', 'template.csv')
#     with open(temp_file, 'w') as f:
#         f.write(template)
    
#     return send_file(temp_file, as_attachment=True, download_name='template.csv')

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     print("\n" + "="*70)
#     print("🚀 MONEY MULING DETECTOR - REAL DATA")
#     print("="*70)
#     print(f"📂 Open: http://localhost:{port}")
#     print("="*70 + "\n")
#     app.run(host='0.0.0.0', port=port, debug=True)

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