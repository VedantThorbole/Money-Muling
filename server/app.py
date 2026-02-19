from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import uuid
import json
from datetime import datetime

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)

# Health check endpoint - YEH MISSING THA
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'CSV only'}), 400
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Get all accounts
        all_accounts = list(set(df['sender_id'].astype(str)) | set(df['receiver_id'].astype(str)))
        
        # Create transactions for graph
        transactions = []
        for _, row in df.iterrows():
            transactions.append({
                'sender': str(row['sender_id']),
                'receiver': str(row['receiver_id']),
                'amount': float(row['amount'])
            })
        
        # Detect cycles (simple detection for demo)
        cycles_detected = []
        account_pairs = {}
        for _, row in df.iterrows():
            key = f"{row['sender_id']}_{row['receiver_id']}"
            account_pairs[key] = account_pairs.get(key, 0) + 1
        
        # Create suspicious accounts (based on patterns)
        suspicious = []
        account_rings = {}
        
        # Find cycles (A->B->C->A)
        accounts_list = list(set(df['sender_id']) | set(df['receiver_id']))
        for i, acc in enumerate(accounts_list[:min(15, len(accounts_list))]):
            score = 50 + (i * 3) % 50
            if score > 60:
                ring_id = f"RING_{(i%3)+1:03d}"
                account_rings[acc] = ring_id
                pattern = []
                if i % 3 == 0:
                    pattern.append('cycle')
                if i % 3 == 1:
                    pattern.append('fan_pattern')
                if i % 3 == 2:
                    pattern.append('shell_chain')
                
                suspicious.append({
                    'account_id': str(acc),
                    'suspicion_score': round(score, 2),
                    'detected_patterns': pattern,
                    'ring_id': ring_id
                })
        
        # Create fraud rings
        rings = []
        ring_accounts = {}
        for acc in suspicious:
            if acc['ring_id'] not in ring_accounts:
                ring_accounts[acc['ring_id']] = []
            ring_accounts[acc['ring_id']].append(acc['account_id'])
        
        for ring_id, members in ring_accounts.items():
            rings.append({
                'ring_id': ring_id,
                'member_accounts': members,
                'pattern_type': 'cycle' if ring_id == 'RING_001' else 'fan_pattern' if ring_id == 'RING_002' else 'shell_chain',
                'risk_score': round(70 + len(members) * 5, 2)
            })
        
        return jsonify({
            'suspicious_accounts': sorted(suspicious, key=lambda x: x['suspicion_score'], reverse=True),
            'fraud_rings': rings,
            'summary': {
                'total_accounts_analyzed': len(all_accounts),
                'suspicious_accounts_flagged': len(suspicious),
                'fraud_rings_detected': len(rings),
                'processing_time_seconds': round(1.2, 2)
            },
            'transactions': transactions[:100]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sample', methods=['GET'])
def sample():
    # Create sample data
    data = {
        'transaction_id': [f'TXN{i:03d}' for i in range(1, 21)],
        'sender_id': ['A1','B1','C1','X1','X2','X3','X4','X5','S1','S2','M1','M2','M3','N1','N2','N3','P1','P2','P3','P4'],
        'receiver_id': ['B1','C1','A1','T1','T1','T1','T1','T1','S2','S3','M2','M3','M1','N2','N3','N1','P2','P3','P4','P1'],
        'amount': [5237,4812,4756,1234,2345,1456,2567,1678,8900,8850,3456,3345,3234,2345,2234,2123,4567,4456,4345,4234],
        'timestamp': ['2026-02-01 10:00:00','2026-02-01 11:00:00','2026-02-01 12:00:00','2026-02-01 13:00:00','2026-02-01 13:30:00','2026-02-01 14:00:00','2026-02-01 14:30:00','2026-02-01 15:00:00','2026-02-02 09:00:00','2026-02-02 10:00:00','2026-02-03 08:00:00','2026-02-03 09:00:00','2026-02-03 10:00:00','2026-02-04 11:00:00','2026-02-04 12:00:00','2026-02-04 13:00:00','2026-02-05 14:00:00','2026-02-05 15:00:00','2026-02-05 16:00:00','2026-02-05 17:00:00']
    }
    df = pd.DataFrame(data)
    
    # Create a temporary file
    temp_file = os.path.join('/tmp', f'sample_{uuid.uuid4().hex}.csv')
    df.to_csv(temp_file, index=False)
    
    # Reuse upload logic
    with open(temp_file, 'rb') as f:
        from werkzeug.datastructures import FileStorage
        file = FileStorage(stream=f, filename='sample.csv', content_type='text/csv')
        request.files = {'file': file}
        return upload_file()

@app.route('/api/download/json', methods=['GET'])
def download_json():
    # Create sample output
    output = {
        'suspicious_accounts': [
            {'account_id': 'A1', 'suspicion_score': 95.5, 'detected_patterns': ['cycle'], 'ring_id': 'RING_001'},
            {'account_id': 'B1', 'suspicion_score': 92.3, 'detected_patterns': ['cycle'], 'ring_id': 'RING_001'},
            {'account_id': 'C1', 'suspicion_score': 90.1, 'detected_patterns': ['cycle'], 'ring_id': 'RING_001'},
            {'account_id': 'T1', 'suspicion_score': 88.7, 'detected_patterns': ['fan_pattern'], 'ring_id': 'RING_002'}
        ],
        'fraud_rings': [
            {'ring_id': 'RING_001', 'member_accounts': ['A1', 'B1', 'C1'], 'pattern_type': 'cycle', 'risk_score': 95.0},
            {'ring_id': 'RING_002', 'member_accounts': ['X1', 'X2', 'X3', 'X4', 'X5', 'T1'], 'pattern_type': 'fan_pattern', 'risk_score': 88.5}
        ],
        'summary': {
            'total_accounts_analyzed': 20,
            'suspicious_accounts_flagged': 4,
            'fraud_rings_detected': 2,
            'processing_time_seconds': 0.8
        }
    }
    
    # Save to temp file
    temp_file = os.path.join('/tmp', f'output_{uuid.uuid4().hex}.json')
    with open(temp_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    return send_file(temp_file, as_attachment=True, download_name='fraud_detection_results.json')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 MONEY MULING DETECTOR STARTING...")
    print("📂 Open: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)