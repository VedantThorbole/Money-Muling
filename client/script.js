// Global state
let graphData = null;
let svg = null;
let simulation = null;
let tooltip = null;
let width, height;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeTooltip();
    window.addEventListener('resize', debounce(handleResize, 250));
});

function initializeEventListeners() {
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
            handleFileUpload(file);
        } else {
            showNotification('Please upload a CSV file', 'error');
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
    
    // Buttons
    document.getElementById('loadSampleBtn').addEventListener('click', loadSampleData);
    document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
    document.getElementById('downloadTemplate').addEventListener('click', (e) => {
        e.preventDefault();
        downloadTemplate();
    });
    
    // Graph controls
    document.getElementById('highlightCycles').addEventListener('click', () => highlightPattern('cycle'));
    document.getElementById('highlightFan').addEventListener('click', () => highlightPattern('fan'));
    document.getElementById('highlightChains').addEventListener('click', () => highlightPattern('chain'));
    document.getElementById('resetView').addEventListener('click', resetGraphView);
}

function initializeTooltip() {
    tooltip = d3.select('body')
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('pointer-events', 'none');
}

async function handleFileUpload(file) {
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

async function loadSampleData() {
    showLoading();
    
    try {
        const response = await fetch('/api/sample');
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load sample');
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
    width = container.clientWidth;
    height = 500;
    
    // Clear previous graph
    d3.select('#graphContainer').selectAll('*').remove();
    
    // Create SVG
    svg = d3.select('#graphContainer')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g');
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            svg.attr('transform', event.transform);
        });
    
    d3.select('#graphContainer svg').call(zoom);
    
    // Build graph data
    const graph = buildGraphFromData(data);
    
    // Create force simulation
    simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-500))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
    
    // Draw links
    const link = svg.append('g')
        .selectAll('line')
        .data(graph.links)
        .enter()
        .append('line')
        .attr('class', d => `link ${d.suspicious ? 'suspicious' : ''}`)
        .attr('stroke-width', d => Math.sqrt(d.value) || 1);
    
    // Draw nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(graph.nodes)
        .enter()
        .append('circle')
        .attr('class', d => {
            let classes = 'node';
            if (d.suspicious) classes += ' suspicious';
            if (d.pattern) classes += ` ${d.pattern}`;
            return classes;
        })
        .attr('r', d => 8 + (d.score / 10))
        .attr('fill', d => getNodeColor(d))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded))
        .on('mouseover', (event, d) => showTooltip(event, d))
        .on('mouseout', hideTooltip)
        .on('click', (event, d) => handleNodeClick(d));
    
    // Add labels for suspicious nodes
    const labels = svg.append('g')
        .selectAll('text')
        .data(graph.nodes.filter(d => d.suspicious))
        .enter()
        .append('text')
        .text(d => d.id.substring(0, 8) + '...')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('text-anchor', 'middle')
        .attr('dy', -15);
    
    // Update positions on tick
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
}

function buildGraphFromData(data) {
    const nodes = new Map();
    const links = [];
    
    // Add suspicious accounts as nodes
    if (data.suspicious_accounts) {
        data.suspicious_accounts.forEach(acc => {
            nodes.set(acc.account_id, {
                id: acc.account_id,
                score: acc.suspicion_score,
                suspicious: true,
                pattern: acc.detected_patterns[0]?.split('_')[0] || 'unknown',
                ring_id: acc.ring_id
            });
        });
    }
    
    // Add ring members that might not be in suspicious_accounts
    if (data.fraud_rings) {
        data.fraud_rings.forEach(ring => {
            ring.member_accounts.forEach(accId => {
                if (!nodes.has(accId)) {
                    nodes.set(accId, {
                        id: accId,
                        score: 0,
                        suspicious: false,
                        pattern: 'normal',
                        ring_id: ring.ring_id
                    });
                }
            });
        });
    }
    
    // Create some sample links for visualization
    // In production, this would come from actual transaction data
    if (data.fraud_rings) {
        data.fraud_rings.forEach(ring => {
            const members = ring.member_accounts;
            for (let i = 0; i < members.length - 1; i++) {
                links.push({
                    source: members[i],
                    target: members[i + 1],
                    value: 1,
                    suspicious: true
                });
            }
        });
    }
    
    return {
        nodes: Array.from(nodes.values()),
        links: links
    };
}

function getNodeColor(d) {
    if (!d.suspicious) return '#4b5563'; // gray
    
    switch(d.pattern) {
        case 'cycle':
            return '#ef4444'; // red
        case 'fan':
            return '#f59e0b'; // orange
        case 'shell':
            return '#10b981'; // green
        default:
            return '#8b5cf6'; // purple
    }
}

function showTooltip(event, d) {
    tooltip.transition()
        .duration(200)
        .style('opacity', 0.9);
    
    let patterns = '';
    if (d.pattern && d.pattern !== 'normal') {
        patterns = `<p><strong>Pattern:</strong> ${d.pattern}</p>`;
    }
    
    tooltip.html(`
        <h4>Account: ${d.id}</h4>
        <p><strong>Suspicion Score:</strong> ${d.score.toFixed(2)}</p>
        ${patterns}
        <p><strong>Ring ID:</strong> ${d.ring_id || 'None'}</p>
    `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
}

function hideTooltip() {
    tooltip.transition()
        .duration(500)
        .style('opacity', 0);
}

function handleNodeClick(d) {
    console.log('Node clicked:', d);
    // Could expand to show more details
}

function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function updateDashboard(data) {
    document.getElementById('totalAccounts').textContent = data.summary.total_accounts_analyzed;
    document.getElementById('suspiciousAccounts').textContent = data.summary.suspicious_accounts_flagged;
    document.getElementById('fraudRings').textContent = data.summary.fraud_rings_detected;
    document.getElementById('processingTime').textContent = data.summary.processing_time_seconds + 's';
}

function updateTables(data) {
    // Update fraud rings table
    const ringsBody = document.getElementById('ringsTableBody');
    ringsBody.innerHTML = '';
    
    data.fraud_rings.forEach(ring => {
        const row = ringsBody.insertRow();
        
        // Ring ID
        row.insertCell().textContent = ring.ring_id;
        
        // Pattern Type
        row.insertCell().textContent = ring.pattern_type;
        
        // Member Count
        row.insertCell().textContent = ring.member_accounts.length;
        
        // Risk Score
        const scoreCell = row.insertCell();
        const score = ring.risk_score;
        scoreCell.textContent = score.toFixed(2);
        
        // Add risk class
        if (score >= 80) scoreCell.className = 'risk-high';
        else if (score >= 50) scoreCell.className = 'risk-medium';
        else scoreCell.className = 'risk-low';
        
        // Member Accounts (first 3)
        const members = ring.member_accounts.slice(0, 3).join(', ');
        const remaining = ring.member_accounts.length - 3;
        row.insertCell().textContent = members + (remaining > 0 ? ` +${remaining} more` : '');
    });
    
    // Update suspicious accounts table
    const suspiciousBody = document.getElementById('suspiciousTableBody');
    suspiciousBody.innerHTML = '';
    
    data.suspicious_accounts.slice(0, 20).forEach(acc => { // Show top 20
        const row = suspiciousBody.insertRow();
        
        row.insertCell().textContent = acc.account_id;
        
        // Suspicion Score
        const scoreCell = row.insertCell();
        scoreCell.textContent = acc.suspicion_score.toFixed(2);
        
        // Add risk class
        if (acc.suspicion_score >= 80) scoreCell.className = 'risk-high';
        else if (acc.suspicion_score >= 50) scoreCell.className = 'risk-medium';
        else scoreCell.className = 'risk-low';
        
        row.insertCell().textContent = acc.detected_patterns.join(', ');
        row.insertCell().textContent = acc.ring_id;
    });
}

function highlightPattern(pattern) {
    if (!graphData) return;
    
    // Reset all nodes
    d3.selectAll('.node')
        .attr('r', d => 8 + (d.score / 10))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
    
    // Highlight pattern
    d3.selectAll('.node')
        .filter(d => d.pattern === pattern)
        .attr('r', d => 15 + (d.score / 10))
        .attr('stroke', '#fbbf24')
        .attr('stroke-width', 3);
}

function resetGraphView() {
    if (!simulation) return;
    
    // Reset zoom
    d3.select('#graphContainer svg')
        .transition()
        .duration(750)
        .call(d3.zoom().transform, d3.zoomIdentity);
    
    // Reset node sizes
    d3.selectAll('.node')
        .attr('r', d => 8 + (d.score / 10))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
}

function handleResize() {
    if (!graphData) return;
    
    const container = document.getElementById('graphContainer');
    width = container.clientWidth;
    
    d3.select('#graphContainer svg')
        .attr('width', width);
    
    simulation.force('center', d3.forceCenter(width / 2, height / 2));
    simulation.alpha(0.3).restart();
}

async function downloadJson() {
    if (!graphData) {
        showNotification('No data to download', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/download/json');
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fraud_detection_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('JSON downloaded!', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showNotification('Failed to download JSON', 'error');
    }
}

function downloadTemplate() {
    fetch('/api/download/template')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'transaction_template.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
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

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        z-index: 1001;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
