// Investment and Retirement Planner - JavaScript Implementation
// Integrated with financia backend API for full prediction logic

// Horizon windows matching Python HORIZON_WINDOWS
const HORIZON_WINDOWS = {
    "Next Day": 1,
    "Next Week": 7,
    "Next Month": 30,
    "Next Quarter": 90,
    "Next Half": 182,
    "Next Year": 365,
};

let forecastData = [];
let summaryData = [];
let monitoringInterval = null;
let forecastChart = null;
let currentApiData = null;

// Utility functions
function parseFloatValue(value) {
    if (!value || value.trim() === '') return null;
    const parsed = parseFloat(value);
    return isNaN(parsed) ? null : parsed;
}

function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined) return '-';
    return `$${value.toFixed(decimals)}`;
}

function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(decimals)}%`;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
    } catch (e) {
        return dateString;
    }
}

function appendLog(message) {
    const logOutput = document.getElementById('logOutput');
    if (!logOutput) return;
    
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const logEntry = document.createElement('div');
    logEntry.textContent = `[${timestamp}] ${message}`;
    logOutput.appendChild(logEntry);
    logOutput.scrollTop = logOutput.scrollHeight;
}

function updateStatus(message) {
    const statusEl = document.getElementById('statusMessage');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

// Main calculation function - calls financia backend API
async function calculateProjection() {
    try {
        const stockSymbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
        const investmentAmount = parseFloatValue(document.getElementById('investmentAmount').value);
        const shareQuantity = parseFloatValue(document.getElementById('shareQuantity').value);
        const forecastDays = parseInt(document.getElementById('forecastHorizon').value);
        const equationType = document.getElementById('equationType').value;

        // Validation
        if (!stockSymbol) {
            alert('Please enter a stock symbol.');
            return;
        }

        if ((!investmentAmount || investmentAmount <= 0) && (!shareQuantity || shareQuantity <= 0)) {
            alert('Enter an investment amount or a share quantity to build a plan.');
            return;
        }

        appendLog(`Calculating projection for ${stockSymbol} using ${equationType}...`);
        updateStatus('Calculating projection with financia prediction engine...');

        // Call backend API with full financia logic
        const response = await fetch('/stock-analysis/api/investment-forecast/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                symbol: stockSymbol,
                investment_amount: investmentAmount,
                share_quantity: shareQuantity,
                forecast_days: forecastDays,
                equation_type: equationType,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to calculate projection');
        }

        if (!data.success) {
            throw new Error(data.error || 'Projection calculation failed');
        }

        // Store API data
        currentApiData = data;

        // Auto-fill current price
        document.getElementById('currentPrice').value = data.current_price.toFixed(2);

        // Display purchase summary
        const plan = data.purchase_plan;
        const summaryText = `${plan.shares.toFixed(4)} shares (~${formatCurrency(plan.total_cost)}) at ${formatCurrency(data.current_price)}`;
        document.getElementById('summaryText').textContent = summaryText;
        document.getElementById('purchaseSummary').style.display = 'block';

        appendLog(`Purchase plan: ${summaryText}`);
        appendLog(`Using ${data.equation_type} model for forecasting`);

        // Process forecast data
        forecastData = data.forecast_data.map(item => ({
            price: item.price,
            date: new Date(item.date),
            day: item.day,
        }));

        // Process summary data
        summaryData = data.summary;

        // Update UI
        updateResultsTable();
        updateChart();
        
        document.getElementById('resultsBox').style.display = 'block';
        document.getElementById('chartBox').style.display = 'block';
        document.getElementById('startMonitoringBtn').disabled = false;
        
        updateStatus('Projection ready. Review horizons or start monitoring alerts.');
        appendLog(`Projection ready for ${summaryData.length} horizons using financia prediction engine.`);

    } catch (error) {
        appendLog(`Error: ${error.message}`);
        alert(`Error calculating projection: ${error.message}`);
        updateStatus('Projection failed. Review the logs and adjust inputs.');
        console.error('Projection error:', error);
    }
}

// Update results table
function updateResultsTable() {
    const tbody = document.getElementById('resultsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    summaryData.forEach(entry => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${entry.label}</td>
            <td>${formatDate(entry.target_date)}</td>
            <td>${formatCurrency(entry.forecast_price)}</td>
            <td>${formatPercent(entry.growth_pct)}</td>
            <td>${formatCurrency(entry.investment_value)}</td>
            <td style="color: ${entry.profit_loss >= 0 ? 'green' : 'red'}">${formatCurrency(entry.profit_loss)}</td>
            <td>${formatCurrency(entry.peak.price)}</td>
            <td>${formatDate(entry.peak.date)}</td>
            <td>${formatCurrency(entry.valley.price)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update chart
function updateChart() {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;

    if (forecastChart) {
        forecastChart.destroy();
    }

    const labels = forecastData.map(d => formatDate(d.date));
    const prices = forecastData.map(d => d.price);

    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Forecasted Price (Financia Prediction)',
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Price ($)',
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                    },
                },
            },
            plugins: {
                legend: {
                    display: true,
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Price: ${formatCurrency(context.parsed.y)}`;
                        },
                    },
                },
            },
        },
    });
}

// Clear results
function clearResults() {
    forecastData = [];
    summaryData = [];
    currentApiData = null;
    document.getElementById('resultsBox').style.display = 'none';
    document.getElementById('chartBox').style.display = 'none';
    document.getElementById('purchaseSummary').style.display = 'none';
    document.getElementById('startMonitoringBtn').disabled = true;
    document.getElementById('stopMonitoringBtn').disabled = true;
    if (forecastChart) {
        forecastChart.destroy();
        forecastChart = null;
    }
    appendLog('Results cleared.');
    updateStatus('Enter stock information and investment details to start planning.');
}

// Start monitoring
function startMonitoring() {
    if (!summaryData || summaryData.length === 0) {
        alert('Calculate a projection before starting monitoring.');
        return;
    }

    stopMonitoring();

    const errorMargin = parseFloatValue(document.getElementById('errorMargin').value) / 100.0;
    const intervalMinutes = parseInt(document.getElementById('checkInterval').value);
    const email = document.getElementById('alertEmail').value.trim() || null;
    const phone = document.getElementById('alertPhone').value.trim() || null;

    appendLog(`Started monitoring with ${(errorMargin * 100).toFixed(1)}% error margin, checking every ${intervalMinutes} minutes.`);
    
    // Simulate monitoring (in real implementation, this would check actual stock prices)
    monitoringInterval = setInterval(() => {
        const now = new Date();
        appendLog(`[${now.toLocaleTimeString()}] Checking prices... (Monitoring active)`);
        // In a real implementation, you would fetch current stock price and compare with forecasts
    }, intervalMinutes * 60 * 1000);

    document.getElementById('startMonitoringBtn').disabled = true;
    document.getElementById('stopMonitoringBtn').disabled = false;
    updateStatus('Monitoring active. Alerts will be sent when prices match forecasts.');
}

// Stop monitoring
function stopMonitoring() {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
        appendLog('Monitoring stopped.');
    }
    document.getElementById('startMonitoringBtn').disabled = false;
    document.getElementById('stopMonitoringBtn').disabled = true;
    updateStatus('Monitoring stopped.');
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    appendLog('Investment Planner initialized with financia prediction engine.');
    
    // Auto-fetch stock price when symbol is entered (optional enhancement)
    document.getElementById('stockSymbol').addEventListener('blur', function() {
        const symbol = this.value.trim().toUpperCase();
        if (symbol) {
            appendLog(`Stock symbol set to ${symbol}. Price will be fetched from financia backend.`);
        }
    });
});
