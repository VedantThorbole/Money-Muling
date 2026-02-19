// // Global variables
// let graphData = null;
// let currentSimulation = null;
// let currentZoom = null;
// let tooltip;

// document.addEventListener('DOMContentLoaded', () => {
//     console.log('DOM loaded');
//     initTooltip();
//     checkAPI();
//     setupButtons();
// });

// function initTooltip() {
//     tooltip = d3.select('body')
//         .append('div')
//         .attr('class', 'tooltip')
//         .style('opacity', 0)
//         .style('position', 'absolute')
//         .style('background', '#1e293b')
//         .style('color', 'white')
//         .style('padding', '8px 12px')
//         .style('border-radius', '6px')
//         .style('font-size', '12px')
//         .style('pointer-events', 'none')
//         .style('z-index', 1000);
// }

// function checkAPI() {
//     fetch('/health')
//         .then(r => r.json())
//         .then(() => {
//             document.getElementById('apiStatus').innerHTML = '✅ API Connected';
//         })
//         .catch(() => {
//             document.getElementById('apiStatus').innerHTML = '⚠️ API Ready';
//         });
// }

// function setupButtons() {
//     // Upload
//     document.getElementById('uploadArea').addEventListener('click', () => {
//         document.getElementById('fileInput').click();
//     });
    
//     document.getElementById('fileInput').addEventListener('change', (e) => {
//         if (e.target.files[0]) uploadFile(e.target.files[0]);
//     });
    
//     document.getElementById('loadSampleBtn').addEventListener('click', loadSample);
//     document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
//     document.getElementById('downloadTemplate').addEventListener('click', downloadTemplate);
    
//     // Graph controls - YE BUTTONS AB KAM KARENGE
//     document.getElementById('highlightCycles').addEventListener('click', () => {
//         console.log('Cycle button clicked');
//         highlightNodes('cycle');
//     });
    
//     document.getElementById('highlightFan').addEventListener('click', () => {
//         console.log('Fan button clicked');
//         highlightNodes('fan_pattern');
//     });
    
//     document.getElementById('highlightChains').addEventListener('click', () => {
//         console.log('Chain button clicked');
//         highlightNodes('shell_chain');
//     });
    
//     document.getElementById('showAll').addEventListener('click', () => {
//         console.log('Show all clicked');
//         resetNodeSizes();
//     });
    
//     document.getElementById('resetView').addEventListener('click', () => {
//         console.log('Reset view clicked');
//         resetZoom();
//     });
    
//     document.getElementById('exportGraph').addEventListener('click', () => {
//         console.log('Export clicked');
//         exportGraph();
//     });
// }

// // HIGHLIGHT FUNCTION - BUTTONS CONNECTED
// function highlightNodes(pattern) {
//     d3.selectAll('.node')
//         .transition()
//         .duration(300)
//         .attr('r', function(d) {
//             if (d.patterns && d.patterns.includes(pattern)) return 22;
//             if (d.suspicious) return 12;
//             return 8;
//         })
//         .attr('stroke', function(d) {
//             if (d.patterns && d.patterns.includes(pattern)) return '#fbbf24';
//             return '#fff';
//         })
//         .attr('stroke-width', function(d) {
//             if (d.patterns && d.patterns.includes(pattern)) return 4;
//             return 2;
//         });
// }

// function resetNodeSizes() {
//     d3.selectAll('.node')
//         .transition()
//         .duration(300)
//         .attr('r', function(d) {
//             return d.suspicious ? 12 + (d.score / 20) : 8;
//         })
//         .attr('stroke', '#fff')
//         .attr('stroke-width', 2);
// }

// function resetZoom() {
//     const svg = d3.select('#graphContainer svg');
//     if (!svg.empty()) {
//         svg.transition()
//            .duration(750)
//            .call(d3.zoom().transform, d3.zoomIdentity);
//     }
// }

// async function uploadFile(file) {
//     showLoading();
    
//     const formData = new FormData();
//     formData.append('file', file);
    
//     try {
//         const res = await fetch('/api/upload', { method: 'POST', body: formData });
//         const data = await res.json();
        
//         if (data.error) throw new Error(data.error);
        
//         graphData = data;
//         updateUI(data);
//     } catch (err) {
//         alert('Error: ' + err.message);
//     } finally {
//         hideLoading();
//     }
// }

// async function loadSample() {
//     showLoading();
//     try {
//         const res = await fetch('/api/sample');
//         const data = await res.json();
//         graphData = data;
//         updateUI(data);
//     } catch (err) {
//         alert('Sample error: ' + err.message);
//     } finally {
//         hideLoading();
//     }
// }

// function updateUI(data) {
//     document.getElementById('dashboard').style.display = 'block';
    
//     // Stats
//     document.getElementById('totalAccounts').textContent = data.summary.total_accounts_analyzed;
//     document.getElementById('suspiciousAccounts').textContent = data.summary.suspicious_accounts_flagged;
//     document.getElementById('fraudRings').textContent = data.summary.fraud_rings_detected;
//     document.getElementById('processingTime').textContent = data.summary.processing_time_seconds + 's';
    
//     // Tables
//     updateRingsTable(data.fraud_rings);
//     updateSuspiciousTable(data.suspicious_accounts);
    
//     // Graph
//     drawGraph(data);
// }

// function updateRingsTable(rings) {
//     const tbody = document.getElementById('ringsTableBody');
//     tbody.innerHTML = '';
    
//     rings.forEach(ring => {
//         const row = tbody.insertRow();
//         row.insertCell().textContent = ring.ring_id;
//         row.insertCell().textContent = ring.pattern_type;
//         row.insertCell().textContent = ring.member_accounts.length;
//         row.insertCell().textContent = ring.risk_score;
//         row.insertCell().textContent = ring.member_accounts.slice(0, 3).join(', ') + 
//             (ring.member_accounts.length > 3 ? '...' : '');
//     });
// }

// function updateSuspiciousTable(accounts) {
//     const tbody = document.getElementById('suspiciousTableBody');
//     tbody.innerHTML = '';
    
//     accounts.slice(0, 15).forEach(acc => {
//         const row = tbody.insertRow();
//         row.insertCell().textContent = acc.account_id;
//         row.insertCell().textContent = acc.suspicion_score;
//         row.insertCell().textContent = acc.detected_patterns.join(', ');
//         row.insertCell().textContent = acc.ring_id;
//     });
// }

// function drawGraph(data) {
//     const container = document.getElementById('graphContainer');
//     const width = container.clientWidth;
//     const height = 500;
    
//     d3.select(container).selectAll('*').remove();
    
//     const svg = d3.select(container)
//         .append('svg')
//         .attr('width', width)
//         .attr('height', height);
    
//     const g = svg.append('g');
    
//     // Zoom
//     const zoom = d3.zoom()
//         .scaleExtent([0.1, 4])
//         .on('zoom', (event) => {
//             g.attr('transform', event.transform);
//         });
    
//     svg.call(zoom);
//     currentZoom = zoom;
    
//     // Create graph data
//     const nodes = new Map();
//     const links = [];
    
//     if (data.transactions) {
//         data.transactions.forEach(tx => {
//             if (!nodes.has(tx.sender)) {
//                 const suspicious = data.suspicious_accounts.find(a => a.account_id === tx.sender);
//                 nodes.set(tx.sender, {
//                     id: tx.sender,
//                     suspicious: !!suspicious,
//                     score: suspicious ? suspicious.suspicion_score : 0,
//                     patterns: suspicious ? suspicious.detected_patterns : []
//                 });
//             }
//             if (!nodes.has(tx.receiver)) {
//                 const suspicious = data.suspicious_accounts.find(a => a.account_id === tx.receiver);
//                 nodes.set(tx.receiver, {
//                     id: tx.receiver,
//                     suspicious: !!suspicious,
//                     score: suspicious ? suspicious.suspicion_score : 0,
//                     patterns: suspicious ? suspicious.detected_patterns : []
//                 });
//             }
            
//             links.push({
//                 source: tx.sender,
//                 target: tx.receiver,
//                 value: tx.amount
//             });
//         });
//     }
    
//     const graph = {
//         nodes: Array.from(nodes.values()),
//         links: links
//     };
    
//     // Simulation
//     const simulation = d3.forceSimulation(graph.nodes)
//         .force('link', d3.forceLink(graph.links).id(d => d.id).distance(120))
//         .force('charge', d3.forceManyBody().strength(-400))
//         .force('center', d3.forceCenter(width / 2, height / 2));
    
//     currentSimulation = simulation;
    
//     // Draw links
//     g.append('g')
//         .selectAll('line')
//         .data(graph.links)
//         .enter()
//         .append('line')
//         .attr('stroke', '#94a3b8')
//         .attr('stroke-opacity', 0.3)
//         .attr('stroke-width', 1);
    
//     // Draw nodes
//     const node = g.append('g')
//         .selectAll('circle')
//         .data(graph.nodes)
//         .enter()
//         .append('circle')
//         .attr('class', d => {
//             let c = 'node';
//             if (d.suspicious) c += ' suspicious';
//             return c;
//         })
//         .attr('r', d => d.suspicious ? 12 + (d.score / 20) : 8)
//         .attr('fill', d => {
//             if (!d.suspicious) return '#94a3b8';
//             if (d.patterns.includes('cycle')) return '#ef4444';
//             if (d.patterns.includes('fan_pattern')) return '#f59e0b';
//             if (d.patterns.includes('shell_chain')) return '#10b981';
//             return '#3b82f6';
//         })
//         .attr('stroke', '#fff')
//         .attr('stroke-width', 2)
//         .call(d3.drag()
//             .on('start', (e, d) => {
//                 if (!e.active) simulation.alphaTarget(0.3).restart();
//                 d.fx = d.x;
//                 d.fy = d.y;
//             })
//             .on('drag', (e, d) => {
//                 d.fx = e.x;
//                 d.fy = e.y;
//             })
//             .on('end', (e, d) => {
//                 if (!e.active) simulation.alphaTarget(0);
//                 d.fx = null;
//                 d.fy = null;
//             }))
//         .on('mouseover', (e, d) => {
//             tooltip.transition().duration(200).style('opacity', 0.9);
//             tooltip.html(`
//                 <strong>${d.id}</strong><br>
//                 Score: ${d.score.toFixed(2)}<br>
//                 Patterns: ${d.patterns.join(', ') || 'none'}
//             `)
//                 .style('left', (e.pageX + 10) + 'px')
//                 .style('top', (e.pageY - 28) + 'px');
//         })
//         .on('mouseout', () => {
//             tooltip.transition().duration(500).style('opacity', 0);
//         });
    
//     // Labels
//     g.append('g')
//         .selectAll('text')
//         .data(graph.nodes.filter(d => d.suspicious))
//         .enter()
//         .append('text')
//         .text(d => d.id)
//         .attr('font-size', '10px')
//         .attr('fill', '#fff')
//         .attr('text-anchor', 'middle')
//         .attr('dy', -15);
    
//     // Update positions
//     simulation.on('tick', () => {
//         g.selectAll('line')
//             .attr('x1', d => d.source.x)
//             .attr('y1', d => d.source.y)
//             .attr('x2', d => d.target.x)
//             .attr('y2', d => d.target.y);
        
//         g.selectAll('circle')
//             .attr('cx', d => d.x)
//             .attr('cy', d => d.y);
        
//         g.selectAll('text')
//             .attr('x', d => d.x)
//             .attr('y', d => d.y);
//     });
// }

// function exportGraph() {
//     const svg = document.querySelector('#graphContainer svg');
//     if (!svg) return;
    
//     const serializer = new XMLSerializer();
//     const source = serializer.serializeToString(svg);
//     const blob = new Blob([source], { type: 'image/svg+xml' });
//     const url = URL.createObjectURL(blob);
    
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = 'graph.svg';
//     a.click();
//     URL.revokeObjectURL(url);
// }

// function showLoading() {
//     document.getElementById('loadingOverlay').style.display = 'flex';
// }

// function hideLoading() {
//     document.getElementById('loadingOverlay').style.display = 'none';
// }

// async function downloadJson() {
//     if (!graphData) {
//         alert('No data');
//         return;
//     }
    
//     const res = await fetch('/api/download/json');
//     const blob = await res.blob();
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = 'results.json';
//     a.click();
//     URL.revokeObjectURL(url);
// }

// function downloadTemplate() {
//     const csv = 'transaction_id,sender_id,receiver_id,amount,timestamp\nTXN001,ACC_A,ACC_B,5237,2026-02-18 10:00:00\nTXN002,ACC_B,ACC_C,4812,2026-02-18 11:00:00';
//     const blob = new Blob([csv], { type: 'text/csv' });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = 'template.csv';
//     a.click();
//     URL.revokeObjectURL(url);
// }

// Global variables
let graphData = null;
let currentSimulation = null;
let svg, g, zoom;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded');
    
    // Tooltip
    window.tooltip = d3.select('body')
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
        .style('z-index', 1000);
    
    checkAPI();
    
    // BUTTONS - DIRECT ATTACH
    document.getElementById('uploadArea').onclick = function() {
        document.getElementById('fileInput').click();
    };
    
    document.getElementById('fileInput').onchange = function(e) {
        if (e.target.files[0]) uploadFile(e.target.files[0]);
    };
    
    document.getElementById('loadSampleBtn').onclick = loadSample;
    document.getElementById('downloadJsonBtn').onclick = downloadJson;
    document.getElementById('downloadTemplate').onclick = downloadTemplate;
    
    // GRAPH BUTTONS - YEH AB KAM KARENGE
    document.getElementById('highlightCycles').onclick = function() {
        console.log('CYCLE CLICKED');
        highlightPattern('cycle');
    };
    
    document.getElementById('highlightFan').onclick = function() {
        console.log('FAN CLICKED');
        highlightPattern('fan_pattern');
    };
    
    document.getElementById('highlightChains').onclick = function() {
        console.log('CHAIN CLICKED');
        highlightPattern('shell_chain');
    };
    
    document.getElementById('showAll').onclick = function() {
        console.log('SHOW ALL CLICKED');
        resetHighlights();
    };
    
    document.getElementById('resetView').onclick = function() {
        console.log('RESET CLICKED');
        resetZoom();
    };
    
    document.getElementById('exportGraph').onclick = function() {
        console.log('EXPORT CLICKED');
        exportGraph();
    };
});

function checkAPI() {
    fetch('/health')
        .then(r => r.json())
        .then(() => {
            document.getElementById('apiStatus').innerHTML = '✅ API Connected';
        })
        .catch(() => {
            document.getElementById('apiStatus').innerHTML = '✅ Ready';
        });
}

// HIGHLIGHT FUNCTION - SIMPLE
function highlightPattern(pattern) {
    d3.selectAll('circle').each(function(d) {
        const circle = d3.select(this);
        if (d && d.patterns && d.patterns.includes(pattern)) {
            circle.transition()
                .duration(300)
                .attr('r', 22)
                .attr('stroke', '#fbbf24')
                .attr('stroke-width', 4);
        } else {
            circle.transition()
                .duration(300)
                .attr('r', d && d.suspicious ? 12 : 8)
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
        }
    });
}

function resetHighlights() {
    d3.selectAll('circle').each(function(d) {
        d3.select(this).transition()
            .duration(300)
            .attr('r', d && d.suspicious ? 12 + (d.score/20) : 8)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
    });
}

function resetZoom() {
    d3.select('svg').transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity);
}

async function uploadFile(file) {
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        graphData = data;
        updateUI(data);
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        hideLoading();
    }
}

async function loadSample() {
    showLoading();
    try {
        const res = await fetch('/api/sample');
        const data = await res.json();
        graphData = data;
        updateUI(data);
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        hideLoading();
    }
}

function updateUI(data) {
    document.getElementById('dashboard').style.display = 'block';
    
    // Stats
    document.getElementById('totalAccounts').textContent = data.summary.total_accounts_analyzed;
    document.getElementById('suspiciousAccounts').textContent = data.summary.suspicious_accounts_flagged;
    document.getElementById('fraudRings').textContent = data.summary.fraud_rings_detected;
    document.getElementById('processingTime').textContent = data.summary.processing_time_seconds + 's';
    
    // Tables
    updateRingsTable(data.fraud_rings);
    updateSuspiciousTable(data.suspicious_accounts);
    
    // Graph
    drawGraph(data);
}

function updateRingsTable(rings) {
    const tbody = document.getElementById('ringsTableBody');
    tbody.innerHTML = '';
    rings.forEach(ring => {
        const row = tbody.insertRow();
        row.insertCell().textContent = ring.ring_id;
        row.insertCell().textContent = ring.pattern_type;
        row.insertCell().textContent = ring.member_accounts.length;
        row.insertCell().textContent = ring.risk_score;
        row.insertCell().textContent = ring.member_accounts.slice(0, 3).join(', ');
    });
}

function updateSuspiciousTable(accounts) {
    const tbody = document.getElementById('suspiciousTableBody');
    tbody.innerHTML = '';
    accounts.slice(0, 15).forEach(acc => {
        const row = tbody.insertRow();
        row.insertCell().textContent = acc.account_id;
        row.insertCell().textContent = acc.suspicion_score;
        row.insertCell().textContent = acc.detected_patterns.join(', ');
        row.insertCell().textContent = acc.ring_id;
    });
}

function drawGraph(data) {
    const container = document.getElementById('graphContainer');
    const width = container.clientWidth;
    const height = 500;
    
    d3.select(container).selectAll('*').remove();
    
    svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    g = svg.append('g');
    
    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => g.attr('transform', event.transform));
    
    svg.call(zoom);
    
    // Create nodes
    const nodes = new Map();
    const links = [];
    
    if (data.transactions) {
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
                target: tx.receiver
            });
        });
    }
    
    // Draw links
    g.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('stroke', '#94a3b8')
        .attr('stroke-opacity', 0.3);
    
    // Draw nodes
    g.append('g')
        .selectAll('circle')
        .data(Array.from(nodes.values()))
        .enter()
        .append('circle')
        .attr('r', d => d.suspicious ? 12 + (d.score/20) : 8)
        .attr('fill', d => {
            if (!d.suspicious) return '#94a3b8';
            if (d.patterns.includes('cycle')) return '#ef4444';
            if (d.patterns.includes('fan_pattern')) return '#f59e0b';
            if (d.patterns.includes('shell_chain')) return '#10b981';
            return '#3b82f6';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .on('mouseover', function(event, d) {
            tooltip.transition().duration(200).style('opacity', 0.9);
            tooltip.html(`<strong>${d.id}</strong><br>Score: ${d.score}<br>${d.patterns.join(', ')}`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            tooltip.transition().duration(500).style('opacity', 0);
        });
    
    // Simulation
    const simulation = d3.forceSimulation(Array.from(nodes.values()))
        .force('link', d3.forceLink(links).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width/2, height/2));
    
    simulation.on('tick', () => {
        g.selectAll('line')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        g.selectAll('circle')
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
    });
}

function exportGraph() {
    const svgNode = document.querySelector('#graphContainer svg');
    if (!svgNode) return;
    
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svgNode);
    const blob = new Blob([source], {type: 'image/svg+xml'});
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graph.svg';
    a.click();
    URL.revokeObjectURL(url);
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

async function downloadJson() {
    if (!graphData) {
        alert('No data');
        return;
    }
    const res = await fetch('/api/download/json');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'results.json';
    a.click();
    URL.revokeObjectURL(url);
}

function downloadTemplate() {
    const csv = 'transaction_id,sender_id,receiver_id,amount,timestamp\nTXN001,ACC_A,ACC_B,5237,2026-02-18 10:00:00';
    const blob = new Blob([csv], {type: 'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template.csv';
    a.click();
    URL.revokeObjectURL(url);
}