"""
API Routes for Money Muling Detection
Defines all REST endpoints for the application
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import time
import json
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
from .middleware import require_api_key, validate_content_type, log_request_data, cache_response

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global detector instance (will be set by app)
detector = None

def init_routes(app_detector):
    """Initialize routes with detector instance"""
    global detector
    detector = app_detector

@api_bp.route('/health', methods=['GET'])
@cache_response(timeout=60)
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'Money Muling Detector'
    })

@api_bp.route('/upload', methods=['POST'])
@validate_content_type(['multipart/form-data'])
@log_request_data
def upload_file():
    """Handle CSV file upload and processing"""
    if not detector:
        return jsonify({'error': 'Detector not initialized'}), 500
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    # Validate file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': f'File too large. Max size: {current_app.config["MAX_CONTENT_LENGTH"] / (1024*1024)}MB'}), 413
    
    try:
        # Generate unique filename
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        start_time = time.time()
        output_data = detector.process_csv(filepath)
        processing_time = time.time() - start_time
        
        # Add processing time to output
        output_data['summary']['processing_time_seconds'] = round(processing_time, 2)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(output_data)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/reset', methods=['POST'])
@require_api_key
def reset():
    """Reset detector state"""
    if not detector:
        return jsonify({'error': 'Detector not initialized'}), 500
    
    detector.reset()
    return jsonify({
        'status': 'reset successful',
        'timestamp': datetime.now().isoformat()
    })

@api_bp.route('/download/json', methods=['GET'])
def download_json():
    """Download results as JSON file"""
    if not detector:
        return jsonify({'error': 'Detector not initialized'}), 500
    
    try:
        output_data = detector._generate_output()
        
        # Create temporary file
        filename = f"fraud_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
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

@api_bp.route('/download/template', methods=['GET'])
def download_template():
    """Download CSV template"""
    template_data = """transaction_id,sender_id,receiver_id,amount,timestamp
TXN001,ACC_A,ACC_B,5000,2026-02-18 10:00:00
TXN002,ACC_B,ACC_C,4800,2026-02-18 11:00:00
TXN003,ACC_C,ACC_A,4700,2026-02-18 12:00:00
TXN004,ACC_D,ACC_E,10000,2026-02-18 13:00:00
TXN005,ACC_E,ACC_F,9500,2026-02-18 14:00:00"""
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'template.csv')
    with open(filepath, 'w') as f:
        f.write(template_data)
    
    return send_file(filepath, as_attachment=True, download_name='transaction_template.csv')

@api_bp.route('/sample', methods=['GET'])
def get_sample():
    """Load and process sample data"""
    if not detector:
        return jsonify({'error': 'Detector not initialized'}), 500
    
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
                
                # Shell chain
                {"transaction_id": "CHN1", "sender_id": "S1", "receiver_id": "S2", "amount": 5000, "timestamp": "2026-02-18 10:00:00"},
                {"transaction_id": "CHN2", "sender_id": "S2", "receiver_id": "S3", "amount": 4900, "timestamp": "2026-02-18 11:00:00"},
                {"transaction_id": "CHN3", "sender_id": "S3", "receiver_id": "S4", "amount": 4800, "timestamp": "2026-02-18 12:00:00"},
                
                # Legitimate transactions (should not be flagged)
                {"transaction_id": "LEG1", "sender_id": "MERCHANT", "receiver_id": "CUST1", "amount": 50, "timestamp": "2026-02-18 09:00:00"},
                {"transaction_id": "LEG2", "sender_id": "MERCHANT", "receiver_id": "CUST2", "amount": 75, "timestamp": "2026-02-18 09:05:00"},
                {"transaction_id": "LEG3", "sender_id": "MERCHANT", "receiver_id": "CUST3", "amount": 100, "timestamp": "2026-02-18 09:10:00"},
            ]
        }
        
        # Create temporary CSV
        import pandas as pd
        df = pd.DataFrame(sample_data["transactions"])
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sample.csv')
        df.to_csv(filepath, index=False)
        
        # Process the sample
        output_data = detector.process_csv(filepath)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(output_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
@cache_response(timeout=30)
def get_statistics():
    """Get detection statistics"""
    if not detector or not detector.transactions_df is None:
        return jsonify({'error': 'No data processed yet'}), 400
    
    try:
        stats = {
            'graph_metrics': detector.graph_analyzer.get_graph_metrics(),
            'cycle_stats': detector.cycle_stats if hasattr(detector, 'cycle_stats') else {},
            'fan_stats': detector.fan_stats if hasattr(detector, 'fan_stats') else {},
            'chain_stats': detector.chain_stats if hasattr(detector, 'chain_stats') else {},
            'total_rings': len(detector.all_rings) if detector.all_rings else 0
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/validate', methods=['POST'])
@validate_content_type(['application/json'])
def validate_json():
    """Validate JSON output format"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    validator = Validator()
    is_valid, errors = validator.validate_output(data)
    
    return jsonify({
        'is_valid': is_valid,
        'errors': errors,
        'format': 'Required JSON format verified' if is_valid else 'Invalid format'
    })