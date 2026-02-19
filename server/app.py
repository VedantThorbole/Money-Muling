from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import time
import json
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback

from core.graph_analyzer import GraphAnalyzer
from algorithms.cycle_detector import CycleDetector
from algorithms.fan_detector import FanDetector
from algorithms.chain_detector import ChainDetector
from core.suspicion_scorer import SuspicionScorer
from core.fraud_ring_builder import FraudRingBuilder
from utils.csv_parser import CSVParser
from utils.json_formatter import JSONFormatter
from utils.validators import Validator

app = Flask(__name__, 
            static_folder='../client',
            static_url_path='')
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['SECRET_KEY'] = 'rift-2026-hackathon-money-muling'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class MoneyMulingDetector:
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all detection state"""
        self.graph_analyzer = GraphAnalyzer()
        self.transactions_df = None
        self.cycles = []
        self.fan_patterns = []
        self.chains = []
        self.all_rings = []
        self.account_scores = {}
        self.ring_scores = {}
        self.processing_time = 0
        self.validator = Validator()
        
    def process_csv(self, file_path):
        """Main processing pipeline"""
        start_time = time.time()
        
        try:
            # Step 1: Parse and validate CSV
            parser = CSVParser()
            self.transactions_df = parser.parse(file_path)
            
            # Validate data structure
            is_valid, errors = self.validator.validate_transactions(self.transactions_df)
            if not is_valid:
                raise ValueError(f"Invalid CSV format: {', '.join(errors)}")
            
            # Step 2: Build graph
            self.graph_analyzer.build_graph_from_csv(self.transactions_df)
            
            # Step 3: Detect cycles (length 3-5)
            cycle_detector = CycleDetector(
                self.graph_analyzer.graph, 
                min_cycle_length=3, 
                max_cycle_length=5
            )
            self.cycles = cycle_detector.find_all_cycles()
            
            # Step 4: Detect fan patterns (smurfing)
            fan_detector = FanDetector(
                self.graph_analyzer.graph, 
                self.transactions_df,
                time_window_hours=72,  # 3 days window
                threshold=10  # 10+ transactions
            )
            self.fan_patterns = fan_detector.detect_fan_in() + fan_detector.detect_fan_out()
            
            # Step 5: Detect shell chains
            chain_detector = ChainDetector(
                self.graph_analyzer.graph,
                min_chain_length=3,
                min_transactions=2
            )
            self.chains = chain_detector.detect_shell_chains()
            
            # Step 6: Build fraud rings
            ring_builder = FraudRingBuilder()
            self.all_rings = ring_builder.build_rings(
                cycles=self.cycles,
                fan_patterns=self.fan_patterns,
                chains=self.chains
            )
            
            # Step 7: Calculate suspicion scores
            scorer = SuspicionScorer(
                self.graph_analyzer.graph,
                self.graph_analyzer.account_stats
            )
            self.account_scores, self.ring_scores = scorer.calculate_scores(self.all_rings)
            
            # Step 8: Format output
            self.processing_time = time.time() - start_time
            return self._generate_output()
            
        except Exception as e:
            print(f"Error processing CSV: {str(e)}")
            traceback.print_exc()
            raise
    
    def _generate_output(self):
        """Generate final output in required JSON format"""
        formatter = JSONFormatter()
        return formatter.format_output(
            transactions_df=self.transactions_df,
            rings=self.all_rings,
            account_scores=self.account_scores,
            ring_scores=self.ring_scores,
            processing_time=self.processing_time
        )

# Global detector instance
detector = MoneyMulingDetector()

@app.route('/')
def index():
    """Serve the main application"""
    return app.send_static_file('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    try:
        # Generate unique filename
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        output_data = detector.process_csv(filepath)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(output_data)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset detector state"""
    detector.reset()
    return jsonify({'status': 'reset successful'})

@app.route('/api/download/json', methods=['GET'])
def download_json():
    """Download results as JSON file"""
    try:
        output_data = detector._generate_output()
        
        # Create temporary file
        filename = f"fraud_detection_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        response = send_file(
            filepath, 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/json'
        )
        
        # Clean up after sending
        @response.call_on_close
        def cleanup():
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/template', methods=['GET'])
def download_template():
    """Download CSV template"""
    template_data = """transaction_id,sender_id,receiver_id,amount,timestamp
TXN001,ACC_A,ACC_B,5000,2026-02-18 10:00:00
TXN002,ACC_B,ACC_C,4800,2026-02-18 11:00:00
TXN003,ACC_C,ACC_A,4700,2026-02-18 12:00:00
TXN004,ACC_D,ACC_E,10000,2026-02-18 13:00:00
TXN005,ACC_E,ACC_F,9500,2026-02-18 14:00:00"""
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'template.csv')
    with open(filepath, 'w') as f:
        f.write(template_data)
    
    return send_file(filepath, as_attachment=True, download_name='transaction_template.csv')

@app.route('/api/sample', methods=['GET'])
def get_sample():
    """Load and process sample data"""
    try:
        # Create sample data with known patterns
        sample_data = {
            "transactions": [
                # Cycle of length 3
                {"transaction_id": "CYC1", "sender_id": "A1", "receiver_id": "B1", "amount": 5000, "timestamp": "2026-02-18 10:00:00"},
                {"transaction_id": "CYC2", "sender_id": "B1", "receiver_id": "C1", "amount": 4800, "timestamp": "2026-02-18 11:00:00"},
                {"transaction_id": "CYC3", "sender_id": "C1", "receiver_id": "A1", "amount": 4700, "timestamp": "2026-02-18 12:00:00"},
                
                # Fan-in pattern (smurfing)
                {"transaction_id": "FIN1", "sender_id": "X1", "receiver_id": "TARGET", "amount": 1000, "timestamp": "2026-02-18 10:00:00"},
                {"transaction_id": "FIN2", "sender_id": "X2", "receiver_id": "TARGET", "amount": 2000, "timestamp": "2026-02-18 11:00:00"},
                {"transaction_id": "FIN3", "sender_id": "X3", "receiver_id": "TARGET", "amount": 1500, "timestamp": "2026-02-18 12:00:00"},
                {"transaction_id": "FIN4", "sender_id": "X4", "receiver_id": "TARGET", "amount": 3000, "timestamp": "2026-02-18 13:00:00"},
                {"transaction_id": "FIN5", "sender_id": "X5", "receiver_id": "TARGET", "amount": 2500, "timestamp": "2026-02-18 14:00:00"},
                {"transaction_id": "FIN6", "sender_id": "X6", "receiver_id": "TARGET", "amount": 1800, "timestamp": "2026-02-18 15:00:00"},
                {"transaction_id": "FIN7", "sender_id": "X7", "receiver_id": "TARGET", "amount": 2200, "timestamp": "2026-02-18 16:00:00"},
                {"transaction_id": "FIN8", "sender_id": "X8", "receiver_id": "TARGET", "amount": 2700, "timestamp": "2026-02-18 17:00:00"},
                {"transaction_id": "FIN9", "sender_id": "X9", "receiver_id": "TARGET", "amount": 1900, "timestamp": "2026-02-18 18:00:00"},
                {"transaction_id": "FIN10", "sender_id": "X10", "receiver_id": "TARGET", "amount": 2100, "timestamp": "2026-02-18 19:00:00"},
                {"transaction_id": "FIN11", "sender_id": "X11", "receiver_id": "TARGET", "amount": 2300, "timestamp": "2026-02-18 20:00:00"},
                
                # Shell chain
                {"transaction_id": "CHN1", "sender_id": "S1", "receiver_id": "S2", "amount": 5000, "timestamp": "2026-02-18 10:00:00"},
                {"transaction_id": "CHN2", "sender_id": "S2", "receiver_id": "S3", "amount": 4900, "timestamp": "2026-02-18 11:00:00"},
                {"transaction_id": "CHN3", "sender_id": "S3", "receiver_id": "S4", "amount": 4800, "timestamp": "2026-02-18 12:00:00"},
                {"transaction_id": "CHN4", "sender_id": "S2", "receiver_id": "S5", "amount": 100, "timestamp": "2026-02-18 13:00:00"},  # Low activity node
                {"transaction_id": "CHN5", "sender_id": "S3", "receiver_id": "S6", "amount": 200, "timestamp": "2026-02-18 14:00:00"},  # Low activity node
                
                # Legitimate high-volume account (should NOT be flagged)
                {"transaction_id": "LEG1", "sender_id": "MERCHANT", "receiver_id": "CUST1", "amount": 50, "timestamp": "2026-02-18 09:00:00"},
                {"transaction_id": "LEG2", "sender_id": "MERCHANT", "receiver_id": "CUST2", "amount": 75, "timestamp": "2026-02-18 09:05:00"},
                {"transaction_id": "LEG3", "sender_id": "MERCHANT", "receiver_id": "CUST3", "amount": 100, "timestamp": "2026-02-18 09:10:00"},
            ]
        }
        
        # Create temporary CSV
        df = pd.DataFrame(sample_data["transactions"])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'sample.csv')
        df.to_csv(filepath, index=False)
        
        # Process the sample
        output_data = detector.process_csv(filepath)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(output_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
