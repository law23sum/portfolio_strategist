// Budget Planner - JavaScript Implementation
// Migrated from Java budget app

// Tax brackets for different years
const TAX_BRACKETS = {
    2022: {
        standardDeduction: 12950.00,
        brackets: [
            { max: 44725.00, tax: 5147.00, rate: 0.22 },
            { max: 95375.00, tax: 16290.00, rate: 0.24 },
        ]
    },
    2023: {
        standardDeduction: 13850.00,
        brackets: [
            { max: 44725.00, tax: 4807.50, rate: 0.22 },
            { max: 89075.00, tax: 15213.00, rate: 0.24 },
        ]
    },
    2024: {
        standardDeduction: 14600.00,
        brackets: [
            { max: 47025.00, tax: 5174.00, rate: 0.22 },
            { max: 100525.00, tax: 17018.00, rate: 0.24 },
        ]
    }
};

let budgetChart = null;

// Tax Calculation Class (migrated from Java)
class TaxCalculation {
    constructor(year, salary, healthInsurance, benefitsPerPaycheck, retirementPercent, paycheckQuantity) {
        this.year = parseInt(year);
        this.salary = parseFloat(salary) || 0;
        this.healthInsurance = parseFloat(healthInsurance) || 0;
        this.benefitsPerPaycheck = parseFloat(benefitsPerPaycheck) || 0;
        this.retirementPercent = parseFloat(retirementPercent) || 0;
        this.paycheckQuantity = parseInt(paycheckQuantity) || 26;
        
        this.setYearDetails();
        this.setRetirementAmount();
    }
    
    setYearDetails() {
        const yearData = TAX_BRACKETS[this.year];
        if (!yearData) {
            throw new Error(`Tax brackets not available for year ${this.year}`);
        }
        
        this.standardDeduction = yearData.standardDeduction;
        
        // Determine which bracket based on salary
        const bracket = this.salary > yearData.brackets[1].max 
            ? yearData.brackets[1] 
            : yearData.brackets[0];
        
        this.yearAmountTaxToBracket = bracket.tax;
        this.yearAmountDueToBracket = bracket.max;
        this.yearPercentBracket = bracket.rate;
    }
    
    setRetirementAmount() {
        this.retirementTraditional = this.salary * (this.retirementPercent / 100);
    }
    
    calculateDetails() {
        // Calculate deductible
        this.deductible = this.healthInsurance + 
                         this.retirementTraditional + 
                         (this.benefitsPerPaycheck * this.paycheckQuantity);
        
        // Calculate taxable income
        this.salaryDeductible = this.salary - this.deductible - this.standardDeduction;
        
        // Calculate tax bracket amount
        this.taxableAmountBracket = Math.max(0, this.salaryDeductible - this.yearAmountDueToBracket);
        this.taxBracketAmount = this.taxableAmountBracket * this.yearPercentBracket;
        
        // Total tax
        this.taxTotal = this.yearAmountTaxToBracket + this.taxBracketAmount;
        
        // Per paycheck calculations
        this.paycheck = this.salary / this.paycheckQuantity;
        this.salaryNet = this.salary - this.taxTotal - this.deductible;
        this.paycheckNet = this.salaryNet / this.paycheckQuantity;
        this.paycheckTaxAmount = this.taxTotal / this.paycheckQuantity;
        
        return {
            salary: this.salary,
            salaryNet: this.salaryNet,
            taxTotal: this.taxTotal,
            healthInsurance: this.healthInsurance,
            retirementTraditional: this.retirementTraditional,
            paycheck: this.paycheck,
            paycheckNet: this.paycheckNet,
            paycheckTaxAmount: this.paycheckTaxAmount,
            deductible: this.deductible,
        };
    }
}

// Expense Calculation Class (migrated from Java)
class ExpenseCalculation {
    constructor(benefitsTotal) {
        this.benefitsTotal = benefitsTotal || 0;
        this.expenseTotal = 0;
        this.remainTotal = 0;
        this.biweeklyDayAmount = 14;
    }
    
    calculateDetails(expenses) {
        this.expenseTotal = expenses.reduce((sum, exp) => sum + (parseFloat(exp.amount) || 0), 0);
    }
    
    setRemainTotal(remainTotal) {
        this.remainTotal = remainTotal;
    }
    
    getPerDayFunds() {
        return this.remainTotal / this.biweeklyDayAmount;
    }
}

// Debt Calculation Class (migrated from Java)
class DebtCalculation {
    constructor(monthlyDebtPayment) {
        this.debtAmount = monthlyDebtPayment || 0;
        this.debtTotal = 0;
        this.debtPaidTotal = 0;
    }
    
    calculateDetails(debts) {
        this.debtTotal = debts.reduce((sum, debt) => sum + (parseFloat(debt.total) || 0), 0);
        this.debtPaidTotal = debts.reduce((sum, debt) => sum + (parseFloat(debt.paid) || 0), 0);
    }
    
    getDebtRemaining() {
        return this.debtTotal - this.debtPaidTotal;
    }
}

// Budget Calculation Class (migrated from Java)
class BudgetCalculation {
    constructor() {
        this.taxCalc = null;
        this.expenseCalc = null;
        this.debtCalc = null;
    }
    
    setTaxCalculation(taxCalc) {
        this.taxCalc = taxCalc;
    }
    
    setExpenseCalculation(expenseCalc) {
        this.expenseCalc = expenseCalc;
    }
    
    setDebtCalculation(debtCalc) {
        this.debtCalc = debtCalc;
    }
}

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function getExpenses() {
    const expenses = [];
    const containers = document.querySelectorAll('#expensesContainer .expense-item');
    containers.forEach(item => {
        const name = item.querySelector('.expense-name').value.trim();
        const amount = parseFloat(item.querySelector('.expense-amount').value) || 0;
        if (name && amount > 0) {
            expenses.push({ name, amount });
        }
    });
    return expenses;
}

function getDebts() {
    const debts = [];
    const containers = document.querySelectorAll('#debtsContainer .debt-item');
    containers.forEach(item => {
        const name = item.querySelector('.debt-name').value.trim();
        const total = parseFloat(item.querySelector('.debt-amount').value) || 0;
        const paid = parseFloat(item.querySelector('.debt-paid').value) || 0;
        if (name) {
            debts.push({ name, total, paid });
        }
    });
    return debts;
}

function addExpense() {
    const container = document.getElementById('expensesContainer');
    if (!container) {
        console.error("Element with id 'expensesContainer' not found");
        return;
    }
    const div = document.createElement('div');
    div.className = 'expense-item';
    div.innerHTML = `
        <input type="text" class="input expense-name" placeholder="Expense name">
        <input type="number" class="input expense-amount" placeholder="Amount" step="0.01" style="width: 150px;">
        <button class="button is-danger is-small" onclick="removeExpense(this)">Remove</button>
    `;
    container.appendChild(div);
}

function removeExpense(button) {
    button.parentElement.remove();
}

function addDebt() {
    const container = document.getElementById('debtsContainer');
    if (!container) {
        console.error("Element with id 'debtsContainer' not found");
        return;
    }
    const div = document.createElement('div');
    div.className = 'debt-item';
    div.innerHTML = `
        <input type="text" class="input debt-name" placeholder="Debt name">
        <input type="number" class="input debt-amount" placeholder="Total debt" step="0.01" style="width: 150px;">
        <input type="number" class="input debt-paid" placeholder="Amount paid" step="0.01" style="width: 150px;">
        <button class="button is-danger is-small" onclick="removeDebt(this)">Remove</button>
    `;
    container.appendChild(div);
}

function removeDebt(button) {
    button.parentElement.remove();
}

function calculateBudget() {
    try {
        // Get inputs with null checks
        const taxYearEl = document.getElementById('taxYear');
        const salaryEl = document.getElementById('salary');
        const healthInsuranceEl = document.getElementById('healthInsurance');
        const retirementPercentEl = document.getElementById('retirementPercent');
        const benefitsPerPaycheckEl = document.getElementById('benefitsPerPaycheck');
        const paycheckQuantityEl = document.getElementById('paycheckQuantity');
        const monthlyDebtPaymentEl = document.getElementById('monthlyDebtPayment');
        
        if (!taxYearEl || !salaryEl || !healthInsuranceEl || !retirementPercentEl || 
            !benefitsPerPaycheckEl || !paycheckQuantityEl || !monthlyDebtPaymentEl) {
            throw new Error('Required input fields are missing from the page');
        }
        
        const year = taxYearEl.value;
        const salary = parseFloat(salaryEl.value) || 0;
        const healthInsurance = parseFloat(healthInsuranceEl.value) || 0;
        const retirementPercent = parseFloat(retirementPercentEl.value) || 0;
        const benefitsPerPaycheck = parseFloat(benefitsPerPaycheckEl.value) || 0;
        const paycheckQuantity = parseInt(paycheckQuantityEl.value) || 26;
        const monthlyDebtPayment = parseFloat(monthlyDebtPaymentEl.value) || 0;
        
        const expenses = getExpenses();
        const debts = getDebts();
        
        // Create calculations
        const budget = new BudgetCalculation();
        
        // Tax calculation
        const taxCalc = new TaxCalculation(
            year, salary, healthInsurance, benefitsPerPaycheck, 
            retirementPercent, paycheckQuantity
        );
        taxCalc.calculateDetails();
        budget.setTaxCalculation(taxCalc);
        
        // Expense calculation
        const benefitsTotal = benefitsPerPaycheck * paycheckQuantity;
        const expenseCalc = new ExpenseCalculation(benefitsTotal);
        expenseCalc.calculateDetails(expenses);
        const remainingAfterExpenses = taxCalc.paycheckNet - expenseCalc.expenseTotal - monthlyDebtPayment;
        expenseCalc.setRemainTotal(remainingAfterExpenses);
        budget.setExpenseCalculation(expenseCalc);
        
        // Debt calculation
        const debtCalc = new DebtCalculation(monthlyDebtPayment);
        debtCalc.calculateDetails(debts);
        budget.setDebtCalculation(debtCalc);
        
        // Display results
        displayResults(budget, expenses, debts);
        
    } catch (error) {
        alert('Error calculating budget: ' + error.message);
        console.error(error);
    }
}

function displayResults(budget, expenses, debts) {
    const tax = budget.taxCalc;
    const expense = budget.expenseCalc;
    const debt = budget.debtCalc;
    
    // Helper function to safely set text content
    function setTextContent(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element with id '${id}' not found`);
        }
    }
    
    // Helper function to safely set innerHTML
    function setInnerHTML(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = value;
        } else {
            console.warn(`Element with id '${id}' not found`);
        }
    }
    
    // Tax results
    setTextContent('salaryGross', formatCurrency(tax.salary));
    setTextContent('salaryNet', formatCurrency(tax.salaryNet));
    setTextContent('taxTotal', formatCurrency(tax.taxTotal));
    setTextContent('paycheckGross', formatCurrency(tax.paycheck));
    setTextContent('paycheckNet', formatCurrency(tax.paycheckNet));
    setTextContent('taxPerPaycheck', formatCurrency(tax.paycheckTaxAmount));
    
    // Expense breakdown
    let expenseHtml = '<div class="expense-list">';
    expenses.forEach(exp => {
        expenseHtml += `<div class="expense-item"><span>${exp.name}</span><span>${formatCurrency(exp.amount)}</span></div>`;
    });
    expenseHtml += '</div>';
    setInnerHTML('expenseBreakdown', expenseHtml);
    
    setTextContent('totalExpenses', formatCurrency(expense.expenseTotal));
    setTextContent('totalBenefits', formatCurrency(expense.benefitsTotal));
    setTextContent('remainingFunds', formatCurrency(expense.remainTotal));
    setTextContent('perDayFunds', formatCurrency(expense.getPerDayFunds()));
    
    // Debt breakdown
    let debtHtml = '<div class="debt-list">';
    debts.forEach(d => {
        const remaining = d.total - d.paid;
        debtHtml += `<div class="debt-item"><span>${d.name}</span><span>Total: ${formatCurrency(d.total)}</span><span>Paid: ${formatCurrency(d.paid)}</span><span>Remaining: ${formatCurrency(remaining)}</span></div>`;
    });
    debtHtml += '</div>';
    setInnerHTML('debtBreakdown', debtHtml);
    
    setTextContent('totalDebt', formatCurrency(debt.debtTotal));
    setTextContent('totalDebtPaid', formatCurrency(debt.debtPaidTotal));
    setTextContent('debtRemaining', formatCurrency(debt.getDebtRemaining()));
    setTextContent('monthlyDebtDisplay', formatCurrency(debt.debtAmount));
    
    // Show results
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    } else {
        console.warn("Element with id 'resultsSection' not found");
    }
    
    // Update chart
    updateChart(budget);
}

function updateChart(budget) {
    const ctx = document.getElementById('budgetChart');
    if (!ctx) return;
    
    if (budgetChart) {
        budgetChart.destroy();
    }
    
    const tax = budget.taxCalc;
    const expense = budget.expenseCalc;
    const debt = budget.debtCalc;
    
    budgetChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Net Income', 'Taxes', 'Expenses', 'Debt Payment'],
            datasets: [{
                data: [
                    tax.salaryNet,
                    tax.taxTotal,
                    expense.expenseTotal,
                    debt.debtAmount
                ],
                backgroundColor: [
                    'rgb(75, 192, 192)',
                    'rgb(255, 99, 132)',
                    'rgb(255, 205, 86)',
                    'rgb(54, 162, 235)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

function runAnalysis() {
    const taxYearEl = document.getElementById('taxYear');
    const salaryEl = document.getElementById('salary');
    const paycheckQuantityEl = document.getElementById('paycheckQuantity');
    
    if (!taxYearEl || !salaryEl || !paycheckQuantityEl) {
        alert('Error: Required input fields are missing from the page');
        return;
    }
    
    const year = taxYearEl.value;
    const salary = parseFloat(salaryEl.value) || 125000;
    const paycheckQuantity = parseInt(paycheckQuantityEl.value) || 26;
    
    const scenarios = [
        { name: 'MIN', health: 0, retirement: 0 },
        { name: 'MIDLOWER', health: 750, retirement: 1.5 },
        { name: 'MID', health: 1500, retirement: 3 },
        { name: 'MIDUPPER', health: 2300, retirement: 4.5 },
        { name: 'MAX', health: 3000, retirement: 6 },
    ];
    
    let html = '<table class="table is-fullwidth"><thead><tr><th>Scenario</th><th>Health ($)</th><th>Retirement (%)</th><th>Tax Owed ($)</th><th>Net Salary ($)</th></tr></thead><tbody>';
    
    const results = [];
    scenarios.forEach(scenario => {
        const taxCalc = new TaxCalculation(year, salary, scenario.health, 0, scenario.retirement, paycheckQuantity);
        taxCalc.calculateDetails();
        results.push(taxCalc);
        
        html += `<tr>
            <td><strong>${scenario.name}</strong></td>
            <td>${formatCurrency(scenario.health)}</td>
            <td>${scenario.retirement}%</td>
            <td>${formatCurrency(taxCalc.taxTotal)}</td>
            <td>${formatCurrency(taxCalc.salaryNet)}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    
    const minTax = results[0].taxTotal;
    const midTax = results[2].taxTotal;
    const maxTax = results[results.length - 1].taxTotal;
    
    html += `<div style="margin-top: 20px;">
        <p><strong>Tax Range:</strong> ${formatCurrency(Math.abs(maxTax - minTax))}</p>
        <p><strong>Sub-Range (MAX to MID):</strong> ${formatCurrency(Math.abs(maxTax - midTax))}</p>
    </div>`;
    
    const analysisResultsEl = document.getElementById('analysisResults');
    const analysisSectionEl = document.getElementById('analysisSection');
    
    if (analysisResultsEl) {
        analysisResultsEl.innerHTML = html;
    } else {
        console.warn("Element with id 'analysisResults' not found");
    }
    
    if (analysisSectionEl) {
        analysisSectionEl.style.display = 'block';
    } else {
        console.warn("Element with id 'analysisSection' not found");
    }
}

function clearAll() {
    const resultsSection = document.getElementById('resultsSection');
    const analysisSection = document.getElementById('analysisSection');
    
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
    if (analysisSection) {
        analysisSection.style.display = 'none';
    }
    if (budgetChart) {
        budgetChart.destroy();
        budgetChart = null;
    }
}

// Initialize with default expenses
document.addEventListener('DOMContentLoaded', function() {
    // Add default expenses
    const defaultExpenses = [
        { name: 'Utilities', amount: 200 },
        { name: 'Internet', amount: 68.98 },
        { name: 'Insurance', amount: 174.95 },
        { name: 'Telephone', amount: 109.33 },
    ];
    
    defaultExpenses.forEach(exp => {
        addExpense();
        const items = document.querySelectorAll('#expensesContainer .expense-item');
        const lastItem = items[items.length - 1];
        lastItem.querySelector('.expense-name').value = exp.name;
        lastItem.querySelector('.expense-amount').value = exp.amount;
    });
});

