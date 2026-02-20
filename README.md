# 🕵️ Money Muling Detection Engine | RIFT 2026 Hackathon

![Graph Theory](https://img.shields.io/badge/Graph-Theory-blue)
![Financial Crime](https://img.shields.io/badge/Financial-Crime-red)
![Python](https://img.shields.io/badge/Python-3.9-green)
![Flask](https://img.shields.io/badge/Flask-2.3-lightgrey)

## 🏆 Live Demo
[View Live Application](your-deployed-url.herokuapp.com)

## 📋 Problem Statement
Build a Financial Forensics Engine that processes transaction data and exposes money muling networks through graph analysis and visualization.

### What is Money Muling?
Money muling involves using networks of individuals ("mules") to transfer and layer illicit funds through multiple accounts, making detection difficult with traditional database queries.

## 🎯 Key Features
- **CSV Upload**: Upload transaction data in specified format
- **Graph Visualization**: Interactive D3.js graph showing transaction flows
- **Pattern Detection**:
  - 🔄 Circular routing (cycles length 3-5)
  - 📊 Fan-in/Fan-out (smurfing patterns)
  - ⛓️ Shell chains (layered networks)
- **Suspicion Scoring**: ML-inspired heuristic scoring (0-100)
- **JSON Export**: Download results in required format
- **Responsive UI**: Works on desktop and mobile

## 🏗️ System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│  Graph      │
│   (HTML/JS) │◀────│   (Flask)    │◀────│  Analysis   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │                     │
       ▼                   ▼                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Interactive │     │   Pattern    │     │  Suspicion  │
│  Graph (D3) │     │  Detection   │     │   Scoring   │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 🧮 Algorithm Approach

### 1. Graph Construction
- **Time Complexity**: O(V + E)
- Build directed graph from transactions
- Each account becomes a node
- Each transaction becomes a directed edge

### 2. Cycle Detection (Length 3-5)
- **Algorithm**: Modified DFS with path tracking
- **Time Complexity**: O((V+E) * L) where L = max cycle length
- Detect money flowing in loops

### 3. Fan Pattern Detection
- **Algorithm**: Sliding window with aggregation
- **Time Complexity**: O(V * T) where T = transactions per account
- Detect smurfing (many-to-one) and dispersion (one-to-many)

### 4. Shell Chain Detection
- **Algorithm**: Path finding with node degree analysis
- **Time Complexity**: O(V * D^L) where D = max degree
- Detect layered networks with low-activity intermediates

## 📊 Suspicion Score Methodology

Scores are calculated on a scale of 0-100 based on:

### Ring-Level Factors (40%)
- **Pattern Type**:
  - Cycles: +30 base
  - Fan patterns: +25 base
  - Shell chains: +35 base
- **Size/Complexity**:
  - Longer cycles: +5-15
  - Higher thresholds: +5-15
  - Longer chains: +10-20

### Account-Level Factors (60%)
- **Transaction Velocity**: +5-15 based on frequency
- **Round Amounts**: +5-10 if >50% round numbers
- **In/Out Ratio**: +8 if near 1:1 (typical mule behavior)
- **Unusual Timing**: +7 if >30% transactions at night

### False Positive Prevention
- High-volume merchants (1000+ transactions) get reduced scores
- Consistent patterns over time reduce suspicion
- Isolated incidents get lower weights

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js (optional, for development)

### Backend Setup
```bash
# Clone repository
git clone https://github.com/your-team/money-muling-detector.git
cd money-muling-detector

# Install Python dependencies
pip install -r requirements.txt

# Run Flask server
python server/app.py
```

### Frontend Setup
```bash
# Serve frontend (in another terminal)
cd client
python -m http.server 8000
```

### Access Application
```
http://localhost:8000
```

## 📖 Usage Instructions

1. **Upload CSV**: Click upload area or drag & drop
2. **View Graph**: Interactive visualization loads automatically
3. **Analyze Patterns**: 
   - Red nodes = Cycle patterns
   - Orange nodes = Fan patterns
   - Green nodes = Shell chains
4. **Check Tables**: View detected rings and suspicious accounts
5. **Export Results**: Click "Download JSON Output"

### CSV Format Example
```csv
transaction_id,sender_id,receiver_id,amount,timestamp
TXN001,ACC_A,ACC_B,5000,2026-02-18 10:00:00
TXN002,ACC_B,ACC_C,4800,2026-02-18 11:00:00
TXN003,ACC_C,ACC_A,4700,2026-02-18 12:00:00
```

## 🧪 Test Cases

### Test Case 1: Cycle Detection
```
Input: A→B→C→A (3 transactions)
Expected: Ring detected with all 3 accounts
```

### Test Case 2: Fan-In Pattern
```
Input: 12 different accounts → X within 72h
Expected: X flagged as suspicious, ring created
```

### Test Case 3: Shell Chain
```
Input: A→B→C→D with B,C low activity
Expected: Chain detected as suspicious
```

## 🔍 Known Limitations

1. **Performance**: Large graphs (>10k nodes) may experience lag
2. **False Positives**: Legitimate high-volume accounts might be flagged
3. **Temporal Analysis**: Limited to 72-hour windows for fan patterns
4. **Memory Usage**: Graph stored entirely in RAM

## 🛠️ Tech Stack

- **Backend**: Python, Flask, NetworkX, Pandas
- **Frontend**: HTML5, CSS3, JavaScript, D3.js
- **Deployment**: Heroku/GCP/AWS
- **Testing**: Pytest

## 👥 Team Members

- Vedant Thorbole - Graph Algorithms
- Om Shinde - Backend Development
- Harshal Sonar - Frontend & Visualization
- Kruturaj Shinde - Testing & Deployment

## 📝 Submission Checklist

- [x] Live web application deployed
- [x] CSV upload functionality
- [x] Interactive graph visualization
- [x] Suspicious nodes highlighted
- [x] JSON download with exact format
- [x] Fraud ring summary table
- [x] Public GitHub repository
- [x] Comprehensive README
- [x] Demo video on LinkedIn

## 📬 Contact

For questions or feedback:
- GitHub Issues: https://github.com/VedantThorbole
- Email: - vedantthorbole9@gmail.com

## 📄 License

MIT License - See LICENSE file

---

**Made with ❤️ for RIFT 2026 Hackathon**
