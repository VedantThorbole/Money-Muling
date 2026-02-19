// Global variables
let graphData = null;
let currentGraph = null;
let tooltip;

document.addEventListener('DOMContentLoaded', () => {
    initializeTooltip();
    checkAPI();
    setupEventListeners();
});

function initializeTooltip() {
    tooltip = d3.select('body')
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0);
}

function checkAPI() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            document.getElementById('apiStatus').innerHTML = '✅ API Connected';
            document.getElementById('apiStatus').style.color = '#10b981';
        })
        .catch(error => {
            document.getElementById('apiStatus').innerHTML = '⚠️ API Error (Using Fallback)';
            document.getElementById('apiStatus').style.color = '#f59e0b';
        });
}

function setupEventListeners() {
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) {
            uploadFile(file);
        } else {
            alert('Please upload a CSV file');
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) uploadFile(e.target.files[0]);
    });
    
    // Buttons
    document.getElementById('loadSampleBtn').addEventListener('click', loadSample);
    document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
    document.getElementById('downloadTemplate').addEventListener('click', (e) => {
        e.preventDefault();
        downloadTemplate();
    });
    
    // Graph control buttons - FIXED
    document.getElementById('highlightCycles').addEventListener('click', () => highlightPattern('cycle'));
    document.getElementById('highlightFan').addEventListener('click', () => highlightPattern('fan_pattern'));
    document.getElementById('highlightChains').addEventListener('click', () => highlightPattern('shell_chain'));
    document.getElementById('showAll').addEventListener('click', resetGraphView);
    document.getElementById('resetView').addEventListener('click', resetZoom);
    document.getElementById('exportGraph').addEventListener('click', exportGraph);
}

async function uploadFile(file) {
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const data = await response.json();
        graphData = data;
        
        updateDashboard(data);
        renderGraph(data);
        updateTables(data);
        showDashboard();
        showNotification('File processed successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function loadSample() {
    showLoading();
    
    try {
        const response = await fetch('/api/sample');
        
        if (!response.ok) {
            throw new Error('Failed to load sample');
        }
        
        const data = await response.json();
        graphData = data;
        
        updateDashboard(data);
        renderGraph(data);
        updateTables(data);
        showDashboard();
        showNotification('Sample data loaded!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function renderGraph(data) {
    const container = document.getElementById('graphContainer');
    const width = container.clientWidth;
    const height = 500;
    
    // Clear previous graph
    d3.select(container).selectAll('*').remove();
    
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    const g = svg.append('g');
    
    // Add zoom
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create nodes and links
    const nodes = new Map();
    const links = [];
    
    // Add nodes from transactions
    if (data.transactions) {
        data.transactions.forEach(tx => {
            if (!nodes.has(tx.sender)) {
                nodes.set(tx.sender, {
                    id: tx.sender,
                    suspicious: data.suspicious_accounts.some(a => a.account_id === tx.sender),
                    score: data.suspicious_accounts.find(a => a.account_id === tx.sender)?.suspicion_score || 0,
                    patterns: data.suspicious_accounts.find(a => a.account_id === tx.sender)?.detected_patterns || []
                });
            }
            if (!nodes.has(tx.receiver)) {
                nodes.set(tx.receiver, {
                    id: tx.receiver,
                    suspicious: data.suspicious_accounts.some(a => a.account_id === tx.receiver),
                    score: data.suspicious_accounts.find(a => a.account_id === tx.receiver)?.suspicion_score || 0,
                    patterns: data.suspicious_accounts.find(a => a.account_id === tx.receiver)?.detected_patterns || []
                });
            }
            
            links.push({
                source: tx.sender,
                target: tx.receiver,
                value: tx.amount
            });
        });
    }
    
    const graph = {
        nodes: Array.from(nodes.values()),
        links: links
    };
    
    // Force simulation
    const simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.links).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
    
    // Draw links
    const link = g.append('g')
        .selectAll('line')
        .data(graph.links)
        .enter()
        .append('line')
        .attr('stroke', d => {
            if (d.source.suspicious || d.target.suspicious) return '#ef4444';
            return '#94a3b8';
        })
        .attr('stroke-opacity', d => (d.source.suspicious || d.target.suspicious) ? 0.8 : 0.3)
        .attr('stroke-width', d => (d.source.suspicious || d.target.suspicious) ? 2 : 1);
    
    // Draw nodes
    const node = g.append('g')
        .selectAll('circle')
        .data(graph.nodes)
        .enter()
        .append('circle')
        .attr('r', d => d.suspicious ? 12 + (d.score / 20) : 8)
        .attr('fill', d => {
            if (!d.suspicious) return '#94a3b8';
            if (d.patterns.includes('cycle')) return '#ef4444';
            if (d.patterns.includes('fan_pattern')) return '#f59e0b';
            if (d.patterns.includes('shell_chain')) return '#10b981';
            return '#3b82f6';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .attr('class', d => {
            let classes = 'node';
            if (d.suspicious) classes += ' suspicious';
            if (d.patterns.includes('cycle')) classes += ' cycle';
            if (d.patterns.includes('fan_pattern')) classes += ' fan';
            if (d.patterns.includes('shell_chain')) classes += ' chain';
            return classes;
        })
        .call(d3.drag()
            .on('start', (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }))
        .on('mouseover', (event, d) => {
            tooltip.transition().duration(200).style('opacity', 0.9);
            tooltip.html(`
                <strong>Account:</strong> ${d.id}<br>
                <strong>Score:</strong> ${d.score.toFixed(2)}<br>
                <strong>Patterns:</strong> ${d.patterns.join(', ') || 'none'}<br>
                <strong>Suspicious:</strong> ${d.suspicious ? 'Yes' : 'No'}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', () => {
            tooltip.transition().duration(500).style('opacity', 0);
        });
    
    // Add labels for suspicious nodes
    const labels = g.append('g')
        .selectAll('text')
        .data(graph.nodes.filter(d => d.suspicious))
        .enter()
        .append('text')
        .text(d => d.id.length > 8 ? d.id.substring(0, 6) + '..' : d.id)
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('text-anchor', 'middle')
        .attr('dy', -15)
        .attr('font-weight', 'bold');
    
    // Update positions
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    currentGraph = { svg, zoom, simulation };
}

function highlightPattern(pattern) {
    if (!currentGraph) return;
    
    d3.selectAll('.node')
        .transition()
        .duration(300)
        .attr('r', d => {
            if (d.patterns && d.patterns.includes(pattern)) return 18;
            return d.suspicious ? 12 : 8;
        })
        .attr('stroke', d => {
            if (d.patterns && d.patterns.includes(pattern)) return '#fbbf24';
            return '#fff';
        })
        .attr('stroke-width', d => {
            if (d.patterns && d.patterns.includes(pattern)) return 4;
            return 2;
        });
}

function resetGraphView() {
    if (!currentGraph) return;
    
    d3.selectAll('.node')
        .transition()
        .duration(300)
        .attr('r', d => d.suspicious ? 12 + (d.score / 20) : 8)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
}

function resetZoom() {
    if (!currentGraph) return;
    
    const svg = d3.select('#graphContainer svg');
    svg.transition().duration(750).call(
        currentGraph.zoom.transform,
        d3.zoomIdentity
    );
}

function exportGraph() {
    const container = document.getElementById('graphContainer');
    const svg = container.querySelector('svg');
    
    if (!svg) return;
    
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svg);
    
    const blob = new Blob([source], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'graph_export.svg';
    link.click();
    
    URL.revokeObjectURL(url);
}

function updateDashboard(data) {
    document.getElementById('totalAccounts').textContent = data.summary.total_accounts_analyzed;
    document.getElementById('suspiciousAccounts').textContent = data.summary.suspicious_accounts_flagged;
    document.getElementById('fraudRings').textContent = data.summary.fraud_rings_detected;
    document.getElementById('processingTime').textContent = data.summary.processing_time_seconds + 's';
}

function updateTables(data) {
    // Rings table
    const ringsBody = document.getElementById('ringsTableBody');
    ringsBody.innerHTML = '';
    
    data.fraud_rings.forEach(ring => {
        const row = ringsBody.insertRow();
        row.insertCell().textContent = ring.ring_id;
        row.insertCell().textContent = ring.pattern_type;
        row.insertCell().textContent = ring.member_accounts.length;
        
        const riskCell = row.insertCell();
        riskCell.textContent = ring.risk_score;
        if (ring.risk_score > 80) riskCell.style.color = '#ef4444';
        else if (ring.risk_score > 60) riskCell.style.color = '#f59e0b';
        else riskCell.style.color = '#10b981';
        
        row.insertCell().textContent = ring.member_accounts.slice(0, 3).join(', ') + 
            (ring.member_accounts.length > 3 ? ` +${ring.member_accounts.length - 3}` : '');
    });
    
    // Suspicious accounts table
    const suspiciousBody = document.getElementById('suspiciousTableBody');
    suspiciousBody.innerHTML = '';
    
    data.suspicious_accounts.slice(0, 15).forEach(acc => {
        const row = suspiciousBody.insertRow();
        row.insertCell().textContent = acc.account_id;
        
        const scoreCell = row.insertCell();
        scoreCell.textContent = acc.suspicion_score;
        if (acc.suspicion_score > 80) scoreCell.style.color = '#ef4444';
        else if (acc.suspicion_score > 60) scoreCell.style.color = '#f59e0b';
        else scoreCell.style.color = '#3b82f6';
        
        row.insertCell().textContent = acc.detected_patterns.join(', ');
        row.insertCell().textContent = acc.ring_id;
        
        const riskCell = row.insertCell();
        if (acc.suspicion_score > 80) riskCell.textContent = 'HIGH';
        else if (acc.suspicion_score > 60) riskCell.textContent = 'MEDIUM';
        else riskCell.textContent = 'LOW';
    });
}

function showDashboard() {
    document.getElementById('dashboard').style.display = 'block';
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        border-radius: 6px;
        z-index: 1001;
        animation: slideIn 0.3s;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

async function downloadJson() {
    if (!graphData) {
        showNotification('No data to download', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/download/json');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fraud_detection_results.json';
        a.click();
        window.URL.revokeObjectURL(url);
        showNotification('JSON downloaded!', 'success');
    } catch (error) {
        showNotification('Download failed', 'error');
    }
}

function downloadTemplate() {
    const csv = 'transaction_id,sender_id,receiver_id,amount,timestamp\nTXN001,ACC_A,ACC_B,5237,2026-02-18 10:00:00\nTXN002,ACC_B,ACC_C,4812,2026-02-18 11:00:00\nTXN003,ACC_C,ACC_A,4756,2026-02-18 12:00:00';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}