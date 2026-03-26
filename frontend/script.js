// ── Initialization ────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    initVolumeChart();
    await loadInitialData();
    setupGenerateAction();
});

// ── Dashboard Data ───────────────────────────────────────

async function loadInitialData() {
    try {
        const response = await fetch('/api/reviews?limit=500');
        const reviews = await response.json();
        
        if (reviews.length > 0) {
            updateDashboardStats(reviews);
            updateLastGenerated();
        }
    } catch (e) {
        showToast('Failed to load dashboard data', 'danger');
    }
}

function updateDashboardStats(reviews) {
    // Basic metrics
    document.getElementById('total-reviews-count').innerText = reviews.length;
    
    // Average rating
    const avgRating = reviews.reduce((sum, r) => sum + (r.rating || 0), 0) / reviews.length;
    document.getElementById('avg-sentiment').innerText = avgRating.toFixed(1);
}

function updateLastGenerated() {
    const now = new Date();
    const formatted = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()}, ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    document.getElementById('last-generated').innerHTML = `<span class="dot"></span> Last Generated: ${formatted}`;
}

// ── Chart.js Setup ────────────────────────────────────────

let volumeChart;

function initVolumeChart() {
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    // Mock data for the 8 week trend
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const data = [12, 19, 15, 22, 18, 25, 30];
    
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Review Volume',
                data: data,
                backgroundColor: 'rgba(44, 154, 255, 0.7)',
                hoverBackgroundColor: '#2c9aff',
                borderRadius: 8,
                barThickness: 32
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8b949e' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e', font: { weight: 'bold' } }
                }
            }
        }
    });
}

// ── Generate Logic ─────────────────────────────────────────

function setupGenerateAction() {
    const btn = document.getElementById('generate-pulse-btn');
    const modal = document.getElementById('pipeline-modal');
    const emailInput = document.getElementById('email-input');

    btn.onclick = async () => {
        const email = emailInput.value.trim();
        if (!email) return showToast('Please enter an email address', 'danger');

        // Show modal and reset steps
        modal.classList.add('active');
        const progressBar = document.getElementById('main-progress');
        progressBar.style.width = '0%';
        resetSteps();

        try {
            // STEP 1: Ingest
            updateStep(1, 'active');
            progressBar.style.width = '25%';
            await callApi('/api/fetch', 'POST');

            // STEP 2: Analyze
            updateStep(2, 'active');
            progressBar.style.width = '50%';
            const analysis = await callApi('/api/analyze', 'POST');
            if (analysis && analysis.themes) {
                renderThemes(analysis.themes);
            }

            // STEP 3: Build Report
            updateStep(3, 'active');
            progressBar.style.width = '75%';
            await callApi('/api/report', 'POST');

            // STEP 4: Send Email
            updateStep(4, 'active');
            progressBar.style.width = '100%';
            await callApi('/api/email', 'POST', { email: email });

            showToast('✅ Pulse generated and email sent!', 'success');
            await loadInitialData();
            setTimeout(() => { modal.classList.remove('active'); }, 1000);

        } catch (e) {
            showToast(e.message, 'danger');
            modal.classList.remove('active');
        }
    };
}

function updateStep(index, status) {
    const stepEl = document.getElementById(`p${index}`);
    if (status === 'active') {
        stepEl.classList.add('active');
    }
}

function resetSteps() {
    for (let i = 1; i <= 4; i++) {
        document.getElementById(`p${i}`).classList.remove('active');
    }
}

function renderThemes(themes) {
    const container = document.getElementById('themes-list');
    container.innerHTML = '';
    
    themes.slice(0, 3).forEach(t => {
        const div = document.createElement('div');
        div.className = 'theme-card';
        div.innerHTML = `
            <div class="theme-info">
                <h4>${t.label}</h4>
                <p>${t.description}</p>
            </div>
            <div class="mini-trend positive">ACTION</div>
        `;
        container.appendChild(div);
    });
}

// ── Helpers ──────────────────────────────────────────────

async function callApi(url, method = 'GET', body = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) options.body = JSON.stringify(body);
    const response = await fetch(url, options);
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Request failed');
    }
    return await response.json();
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} active`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
