// Global variables
let graphData = null;
let currentSimulation = null;
let svg, g, zoom;
let tooltip;

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Page loaded');
    
    // Create tooltip
    tooltip = d3.select('body')
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background', '#1e293b')
        .style('color', 'white')
        .style('padding', '8px 12px')
        .style('border-radius', '6px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('border', '1px solid #334155');
    
    // Check API
    checkAPI();
    
    // Setup all buttons
    setupButtons();
});

function checkAPI() {
    fetch('/health')
        .then(res => res.json())
        .then(() => {
            document.getElementById('apiStatus').innerHTML = '✅ API Connected';
            document.getElementById('apiStatus').style.color = '#10b981';
        })
        .catch(() => {
            document.getElementById('apiStatus').innerHTML = '✅ Ready';
            document.getElementById('apiStatus').style.color = '#f59e0b';
        });
}

function setupButtons() {
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea) {
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function() {
            this.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.csv')) {
                uploadFile(file);
            } else {
                alert('Please upload a CSV file');
            }
        });
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files[0]) {
                uploadFile(e.target.files[0]);
            }
        });
    }
    
    // Sample button
    const sampleBtn = document.getElementById('loadSampleBtn');
    if (sampleBtn) {
        sampleBtn.addEventListener('click', function() {
            loadSample(2000);
        });
    }
    
    // Download JSON button
    const downloadBtn = document.getElementById('downloadJsonBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            downloadJson();
        });
    }
    
    // Template button
    const templateBtn = document.getElementById('downloadTemplate');
    if (templateBtn) {
        templateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadTemplate();
        });
    }
    
    // GRAPH CONTROL BUTTONS
    const cycleBtn = document.getElementById('highlightCycles');
    if (cycleBtn) {
        cycleBtn.addEventListener('click', function() {
            console.log('🔴 Cycle button clicked');
            highlightPattern('cycle');
        });
    }
    
    const fanBtn = document.getElementById('highlightFan');
    if (fanBtn) {
        fanBtn.addEventListener('click', function() {
            console.log('🟠 Fan button clicked');
            highlightPattern('fan_in', 'fan_out', 'fan_pattern');
        });
    }
    
    const chainBtn = document.getElementById('highlightChains');
    if (chainBtn) {
        chainBtn.addEventListener('click', function() {
            console.log('🟢 Chain button clicked');
            highlightPattern('shell_chain');
        });
    }
    
    const showAllBtn = document.getElementById('showAll');
    if (showAllBtn) {
        showAllBtn.addEventListener('click', function() {
            console.log('👁️ Show all clicked');
            resetHighlights();
        });
    }
    
    const resetViewBtn = document.getElementById('resetView');
    if (resetViewBtn) {
        resetViewBtn.addEventListener('click', function() {
            console.log('🗺️ Reset view clicked');
            resetZoom();
        });
    }
    
    const exportBtn = document.getElementById('exportGraph');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            console.log('📸 Export clicked');
            exportGraph();
        });
    }
}

// HIGHLIGHT FUNCTION
function highlightPattern() {
    const patterns = Array.from(arguments);
    console.log('Highlighting patterns:', patterns);
    
    d3.selectAll('circle').each(function(d) {
        const circle = d3.select(this);
        if (d && d.patterns) {
            const hasPattern = patterns.some(p => d.patterns.includes(p));
            
            if (hasPattern) {
                circle.transition()
                    .duration(300)
                    .attr('r', 22)
                    .attr('stroke', '#fbbf24')
                    .attr('stroke-width', 4);
            } else {
                circle.transition()
                    .duration(300)
                    .attr('r', d.suspicious ? 12 + (d.score/20) : 8)
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 2);
            }
        }
    });
}

function resetHighlights() {
    d3.selectAll('circle').each(function(d) {
        if (d) {
            d3.select(this).transition()
                .duration(300)
                .attr('r', d.suspicious ? 12 + (d.score/20) : 8)
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
        }
    });
}

function resetZoom() {
    d3.select('svg').transition()
        .duration(750)
        .call(d3.zoom().transform, d3.zoomIdentity);
}

async function uploadFile(file) {
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        console.log('📤 Uploading:', file.name);
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('📥 Response:', data);
        graphData = data;
        updateUI(data);
        
    } catch (err) {
        console.error('Error:', err);
        alert('Error: ' + err.message);
    } finally {
        hideLoading();
    }
}

async function loadSample(size = 2000) {
    showLoading();
    
    try {
        console.log(`🔄 Loading sample with ${size} transactions`);
        const res = await fetch(`/api/sample?size=${size}`);
        const data = await res.json();
        
        console.log('📥 Sample data:', data);
        graphData = data;
        updateUI(data);
        
    } catch (err) {
        console.error('Sample error:', err);
        alert('Error loading sample: ' + err.message);
    } finally {
        hideLoading();
    }
}

function updateUI(data) {
    document.getElementById('dashboard').style.display = 'block';
    
    // Total Transactions (pehla column)
    const totalTx = document.getElementById('totalTransactions');
    if (totalTx) {
        totalTx.textContent = data.summary.total_transactions || data.summary.total_accounts_analyzed;
        totalTx.style.fontWeight = 'bold';
        totalTx.style.fontSize = '24px';
        totalTx.style.color = '#3b82f6';
    }
    
    // Unique Accounts
    const uniqueAcc = document.getElementById('totalAccounts');
    if (uniqueAcc) {
        uniqueAcc.textContent = data.summary.total_accounts_analyzed;
        uniqueAcc.style.fontWeight = 'bold';
        uniqueAcc.style.fontSize = '24px';
        uniqueAcc.style.color = '#8b5cf6';
    }
    
    // Suspicious
    const susp = document.getElementById('suspiciousAccounts');
    if (susp) {
        susp.textContent = data.summary.suspicious_accounts_flagged;
        susp.style.fontWeight = 'bold';
        susp.style.fontSize = '24px';
        susp.style.color = '#ef4444';
    }
    
    // Rings
    const rings = document.getElementById('fraudRings');
    if (rings) {
        rings.textContent = data.summary.fraud_rings_detected;
        rings.style.fontWeight = 'bold';
        rings.style.fontSize = '24px';
        rings.style.color = '#10b981';
    }
    
    // Processing Time
    const time = document.getElementById('processingTime');
    if (time) {
        time.textContent = data.summary.processing_time_seconds + 's';
        time.style.fontWeight = 'bold';
        time.style.fontSize = '24px';
        time.style.color = '#f59e0b';
    }
    
    // Update tables and graph...
    updateRingsTable(data.fraud_rings);
    updateSuspiciousTable(data.suspicious_accounts);
    drawGraph(data);
}

function updateRingsTable(rings) {
    const tbody = document.getElementById('ringsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!rings || rings.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 5;
        cell.textContent = 'No fraud rings detected';
        cell.style.textAlign = 'center';
        cell.style.padding = '20px';
        return;
    }
    
    rings.forEach(ring => {
        const row = tbody.insertRow();
        
        // Ring ID
        const cell1 = row.insertCell();
        cell1.textContent = ring.ring_id;
        cell1.style.padding = '10px';
        
        // Pattern Type
        const cell2 = row.insertCell();
        cell2.textContent = ring.pattern_type;
        cell2.style.padding = '10px';
        
        // Member Count
        const cell3 = row.insertCell();
        cell3.textContent = ring.member_accounts.length;
        cell3.style.padding = '10px';
        cell3.style.textAlign = 'center';
        
        // Risk Score
        const cell4 = row.insertCell();
        cell4.textContent = ring.risk_score;
        cell4.style.padding = '10px';
        cell4.style.fontWeight = 'bold';
        if (ring.risk_score > 80) cell4.style.color = '#ef4444';
        else if (ring.risk_score > 60) cell4.style.color = '#f59e0b';
        else cell4.style.color = '#10b981';
        
        // Member Accounts
        const cell5 = row.insertCell();
        cell5.textContent = ring.member_accounts.slice(0, 3).join(', ') + 
            (ring.member_accounts.length > 3 ? ` +${ring.member_accounts.length - 3}` : '');
        cell5.style.padding = '10px';
    });
}

function updateSuspiciousTable(accounts) {
    const tbody = document.getElementById('suspiciousTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!accounts || accounts.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 5;
        cell.textContent = 'No suspicious accounts detected';
        cell.style.textAlign = 'center';
        cell.style.padding = '20px';
        return;
    }
    
    accounts.slice(0, 20).forEach(acc => {
        const row = tbody.insertRow();
        
        // Account ID
        const cell1 = row.insertCell();
        cell1.textContent = acc.account_id;
        cell1.style.padding = '10px';
        
        // Suspicion Score
        const cell2 = row.insertCell();
        cell2.textContent = acc.suspicion_score;
        cell2.style.padding = '10px';
        cell2.style.fontWeight = 'bold';
        
        if (acc.suspicion_score > 80) {
            cell2.style.color = '#ef4444';
        } else if (acc.suspicion_score > 60) {
            cell2.style.color = '#f59e0b';
        } else {
            cell2.style.color = '#3b82f6';
        }
        
        // Detected Patterns
        const cell3 = row.insertCell();
        cell3.textContent = acc.detected_patterns.join(', ');
        cell3.style.padding = '10px';
        
        // Ring ID
        const cell4 = row.insertCell();
        cell4.textContent = acc.ring_id;
        cell4.style.padding = '10px';
        
        // Risk Level
        const cell5 = row.insertCell();
        cell5.style.padding = '10px';
        cell5.style.fontWeight = 'bold';
        
        if (acc.suspicion_score > 80) {
            cell5.textContent = 'HIGH';
            cell5.style.color = '#ef4444';
        } else if (acc.suspicion_score > 60) {
            cell5.textContent = 'MEDIUM';
            cell5.style.color = '#f59e0b';
        } else {
            cell5.textContent = 'LOW';
            cell5.style.color = '#10b981';
        }
    });
}

function drawGraph(data) {
    const container = document.getElementById('graphContainer');
    if (!container) return;
    
    const width = container.clientWidth;
    const height = 500;
    
    d3.select(container).selectAll('*').remove();
    
    svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('background', '#0f172a')
        .style('border-radius', '8px');
    
    g = svg.append('g');
    
    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    const nodes = new Map();
    const links = [];
    
    if (data.transactions && data.transactions.length > 0) {
        data.transactions.forEach(tx => {
            if (!nodes.has(tx.sender)) {
                const sus = data.suspicious_accounts.find(a => a.account_id === tx.sender);
                nodes.set(tx.sender, {
                    id: tx.sender,
                    suspicious: !!sus,
                    score: sus ? sus.suspicion_score : 0,
                    patterns: sus ? sus.detected_patterns : []
                });
            }
            
            if (!nodes.has(tx.receiver)) {
                const sus = data.suspicious_accounts.find(a => a.account_id === tx.receiver);
                nodes.set(tx.receiver, {
                    id: tx.receiver,
                    suspicious: !!sus,
                    score: sus ? sus.suspicion_score : 0,
                    patterns: sus ? sus.detected_patterns : []
                });
            }
            
            links.push({
                source: tx.sender,
                target: tx.receiver,
                value: tx.amount
            });
        });
    }
    
    if (nodes.size === 0 && data.suspicious_accounts) {
        data.suspicious_accounts.slice(0, 20).forEach(acc => {
            nodes.set(acc.account_id, {
                id: acc.account_id,
                suspicious: true,
                score: acc.suspicion_score,
                patterns: acc.detected_patterns
            });
        });
        
        const nodeArray = Array.from(nodes.keys());
        for (let i = 0; i < nodeArray.length - 1; i++) {
            links.push({
                source: nodeArray[i],
                target: nodeArray[i + 1]
            });
        }
    }
    
    const graph = {
        nodes: Array.from(nodes.values()),
        links: links
    };
    
    // Draw links
    g.append('g')
        .selectAll('line')
        .data(graph.links)
        .enter()
        .append('line')
        .attr('stroke', '#94a3b8')
        .attr('stroke-opacity', 0.3)
        .attr('stroke-width', 1);
    
    // Draw nodes
    g.append('g')
        .selectAll('circle')
        .data(graph.nodes)
        .enter()
        .append('circle')
        .attr('r', d => d.suspicious ? 12 + (d.score/20) : 8)
        .attr('fill', d => {
            if (!d.suspicious) return '#94a3b8';
            if (d.patterns.includes('cycle')) return '#ef4444';
            if (d.patterns.includes('fan_in') || d.patterns.includes('fan_out')) return '#f59e0b';
            if (d.patterns.includes('shell_chain')) return '#10b981';
            return '#3b82f6';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .on('mouseover', function(event, d) {
            tooltip.transition().duration(200).style('opacity', 0.9);
            tooltip.html(`
                <strong>${d.id}</strong><br>
                Score: ${d.score.toFixed(2)}<br>
                Patterns: ${d.patterns.join(', ') || 'none'}<br>
                ${d.suspicious ? '🔴 SUSPICIOUS' : '✅ NORMAL'}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            tooltip.transition().duration(500).style('opacity', 0);
        });
    
    // Add labels for suspicious nodes
    g.append('g')
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
    
    const simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.links).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width/2, height/2));
    
    currentSimulation = simulation;
    
    simulation.on('tick', () => {
        g.selectAll('line')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        g.selectAll('circle')
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        g.selectAll('text')
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
}

function exportGraph() {
    const svgNode = document.querySelector('#graphContainer svg');
    if (!svgNode) {
        alert('No graph to export');
        return;
    }
    
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svgNode);
    const blob = new Blob([source], {type: 'image/svg+xml'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graph_' + new Date().getTime() + '.svg';
    a.click();
    
    URL.revokeObjectURL(url);
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

async function downloadJson() {
    if (!graphData) {
        alert('No data to download. Please upload or load sample first.');
        return;
    }
    
    try {
        const dataStr = JSON.stringify(graphData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fraud_detection_results.json';
        a.click();
        
        URL.revokeObjectURL(url);
        console.log('✅ JSON downloaded');
        
    } catch (err) {
        console.error('Download error:', err);
        alert('Error downloading: ' + err.message);
    }
}

function downloadTemplate() {
    const csv = 'transaction_id,sender_id,receiver_id,amount,timestamp\n' +
                'TXN001,ACC_0001,ACC_0002,5237,2026-02-01 10:00:00\n' +
                'TXN002,ACC_0002,ACC_0003,4812,2026-02-01 11:00:00\n' +
                'TXN003,ACC_0003,ACC_0001,4756,2026-02-01 12:00:00';
    
    const blob = new Blob([csv], {type: 'text/csv'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template.csv';
    a.click();
    
    URL.revokeObjectURL(url);
}

window.addEventListener('resize', function() {
    if (graphData) {
        drawGraph(graphData);
    }
});


