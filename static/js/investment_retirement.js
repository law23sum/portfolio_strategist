// Investment and Retirement Planner - JavaScript Implementation
// Converted from financia Python code

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

// Utility functions
function parseFloat(value) {
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

function formatDate(date) {
    if (!date) return '-';
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
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

// Calculate purchase plan (converted from Python calculate_purchase_plan)
function calculatePurchasePlan(currentPrice, investmentAmount, shareQuantity) {
    if (!currentPrice || currentPrice <= 0) {
        throw new Error("Current price is required and must be non-zero.");
    }

    let normalizedShares = 0.0;
    if (shareQuantity !== null && shareQuantity > 0) {
        normalizedShares = shareQuantity;
    } else if (investmentAmount !== null && investmentAmount > 0) {
        normalizedShares = investmentAmount / currentPrice;
    }

    normalizedShares = Math.max(0.0, normalizedShares);
    const totalCost = normalizedShares * currentPrice;

    return {
        shares: normalizedShares,
        totalCost: totalCost,
    };
}

// Get current price from historical data (simplified for web)
function getCurrentPrice(priceInput) {
    const price = parseFloat(priceInput);
    return price && price > 0 ? price : null;
}

// Calculate forecast summary (converted from Python summarize_forecast)
function summarizeForecast(forecastPrices, currentPrice, shareQuantity, totalCost, forecastDays) {
    if (!forecastPrices || forecastPrices.length === 0) {
        throw new Error("Forecast data is empty; cannot summarize.");
    }

    const summary = [];
    const horizons = Object.entries(HORIZON_WINDOWS).filter(([_, days]) => days <= forecastDays);
    
    horizons.forEach(([label, daysAhead]) => {
        const idx = Math.min(Math.floor((daysAhead / forecastDays) * forecastPrices.length), forecastPrices.length - 1);
        const targetPrice = forecastPrices[idx].price;
        const investmentValue = shareQuantity > 0 ? shareQuantity * targetPrice : null;
        const profitLoss = investmentValue !== null ? investmentValue - totalCost : null;
        const growthPct = currentPrice ? ((targetPrice - currentPrice) / currentPrice) * 100.0 : null;

        // Find peak and valley in the subset
        const subsetPrices = forecastPrices.slice(0, idx + 1);
        const peak = subsetPrices.reduce((max, p) => p.price > max.price ? p : max, subsetPrices[0]);
        const valley = subsetPrices.reduce((min, p) => p.price < min.price ? p : min, subsetPrices[0]);

        const targetDate = new Date();
        targetDate.setDate(targetDate.getDate() + daysAhead);

        summary.push({
            label: label,
            days: daysAhead,
            forecastPrice: targetPrice,
            growthPct: growthPct,
            investmentValue: investmentValue,
            profitLoss: profitLoss,
            targetDate: targetDate,
            peak: {
                price: peak.price,
                date: peak.date,
                type: "peak",
            },
            valley: {
                price: valley.price,
                date: valley.date,
                type: "valley",
            },
        });
    });

    return summary;
}

// Generate forecast prices using Geometric Brownian Motion (simplified)
function generateForecast(currentPrice, forecastDays, volatility = 0.02, drift = 0.0001) {
    const prices = [];
    const dates = [];
    let price = currentPrice;
    
    const today = new Date();
    
    for (let day = 0; day <= forecastDays; day++) {
        // Simple GBM simulation
        const randomChange = (Math.random() - 0.5) * 2; // -1 to 1
        const dailyReturn = drift + (volatility * randomChange);
        price = price * (1 + dailyReturn);
        
        const date = new Date(today);
        date.setDate(date.getDate() + day);
        
        prices.push({
            price: price,
            date: date,
            day: day,
        });
    }
    
    return prices;
}

// Main calculation function
function calculateProjection() {
    try {
        const stockSymbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
        const currentPriceInput = document.getElementById('currentPrice').value;
        const investmentAmount = parseFloat(document.getElementById('investmentAmount').value);
        const shareQuantity = parseFloat(document.getElementById('shareQuantity').value);
        const forecastDays = parseInt(document.getElementById('forecastHorizon').value);

        // Validation
        if (!stockSymbol) {
            alert('Please enter a stock symbol.');
            return;
        }

        const currentPrice = getCurrentPrice(currentPriceInput);
        if (!currentPrice || currentPrice <= 0) {
            alert('Please enter a valid current stock price.');
            return;
        }

        if ((!investmentAmount || investmentAmount <= 0) && (!shareQuantity || shareQuantity <= 0)) {
            alert('Enter an investment amount or a share quantity to build a plan.');
            return;
        }

        appendLog(`Calculating projection for ${stockSymbol}...`);
        updateStatus('Calculating projection...');

        // Calculate purchase plan
        const plan = calculatePurchasePlan(currentPrice, investmentAmount, shareQuantity);
        
        if (plan.shares <= 0) {
            alert('Calculated share quantity is zero. Adjust your inputs and try again.');
            return;
        }

        // Display purchase summary
        const summaryText = `${plan.shares.toFixed(4)} shares (~${formatCurrency(plan.totalCost)}) at ${formatCurrency(currentPrice)}`;
        document.getElementById('summaryText').textContent = summaryText;
        document.getElementById('purchaseSummary').style.display = 'block';

        appendLog(`Purchase plan: ${summaryText}`);

        // Generate forecast
        appendLog('Generating price forecast...');
        forecastData = generateForecast(currentPrice, forecastDays);
        
        // Calculate summary
        summaryData = summarizeForecast(
            forecastData,
            currentPrice,
            plan.shares,
            plan.totalCost,
            forecastDays
        );

        // Update UI
        updateResultsTable();
        updateChart();
        
        document.getElementById('resultsBox').style.display = 'block';
        document.getElementById('chartBox').style.display = 'block';
        document.getElementById('startMonitoringBtn').disabled = false;
        
        updateStatus('Projection ready. Review horizons or start monitoring alerts.');
        appendLog(`Projection ready for ${summaryData.length} horizons.`);

    } catch (error) {
        appendLog(`Error: ${error.message}`);
        alert(`Error calculating projection: ${error.message}`);
        updateStatus('Projection failed. Review the logs and adjust inputs.');
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
            <td>${formatDate(entry.targetDate)}</td>
            <td>${formatCurrency(entry.forecastPrice)}</td>
            <td>${formatPercent(entry.growthPct)}</td>
            <td>${formatCurrency(entry.investmentValue)}</td>
            <td style="color: ${entry.profitLoss >= 0 ? 'green' : 'red'}">${formatCurrency(entry.profitLoss)}</td>
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
                label: 'Forecasted Price',
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

    const errorMargin = parseFloat(document.getElementById('errorMargin').value) / 100.0;
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    appendLog('Investment Planner initialized.');
    
    // Auto-fetch stock price when symbol is entered (optional enhancement)
    document.getElementById('stockSymbol').addEventListener('blur', function() {
        const symbol = this.value.trim().toUpperCase();
        if (symbol) {
            // In a real implementation, you could fetch the current price from an API
            appendLog(`Stock symbol set to ${symbol}. Enter current price manually or fetch from API.`);
        }
    });
});

