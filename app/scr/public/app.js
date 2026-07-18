/**
 * Antigravity Finance - Core Frontend Logic
 * REST API Integration, DOM Manipulation, and Dynamic SVG Charts
 */

const API_BASE = ''; // Relative routes, served directly by FastAPI backend

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const netBalanceEl = document.getElementById('netBalance');
const totalIncomeEl = document.getElementById('totalIncome');
const totalExpenseEl = document.getElementById('totalExpense');
const balanceTrendEl = document.getElementById('balanceTrend');

// Database Details Card
const dbEngineText = document.getElementById('dbEngineText');
const dbStatusBadge = document.getElementById('dbStatusBadge');
const dbScopeText = document.getElementById('dbScopeText');

// Filters and Search
const searchInput = document.getElementById('searchInput');
const filterType = document.getElementById('filterType');
const filterCategory = document.getElementById('filterCategory');

// Transactions Table
const transactionsTableBody = document.getElementById('transactionsTableBody');

// Goals
const btnEditGoal = document.getElementById('btnEditGoal');
const btnCancelGoal = document.getElementById('btnCancelGoal');
const goalForm = document.getElementById('goalForm');
const goalProgressBar = document.getElementById('goalProgressBar');
const savedAmountText = document.getElementById('savedAmountText');
const targetAmountText = document.getElementById('targetAmountText');
const goalPercentText = document.getElementById('goalPercentText');
const inputTargetAmount = document.getElementById('inputTargetAmount');
const inputSavedAmount = document.getElementById('inputSavedAmount');

// SVG Charts
const expenseDonutChart = document.getElementById('expenseDonutChart');
const chartLegend = document.getElementById('chartLegend');

// Modal Elements
const btnOpenAddModal = document.getElementById('btnOpenAddModal');
const btnCloseModal = document.getElementById('btnCloseModal');
const btnCancelModal = document.getElementById('btnCancelModal');
const transactionModal = document.getElementById('transactionModal');
const transactionForm = document.getElementById('transactionForm');
const transDateInput = document.getElementById('transDate');

// Category Palette for SVG Donut Charts & Badges
const CATEGORY_COLORS = {
    'Food': '#f59e0b',           // Amber/Orange
    'Housing': '#3b82f6',         // Blue
    'Entertainment': '#ec4899',   // Pink
    'Transportation': '#14b8a6',  // Teal
    'Work': '#10b981',            // Emerald Green
    'Health': '#ef4444',          // Red
    'Utilities': '#8b5cf6',       // Purple
    'Other': '#64748b'            // Slate Gray
};

// 1. App Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Set default transaction date in modal to today
    const today = new Date().toISOString().split('T')[0];
    transDateInput.value = today;

    // Load initial data
    loadDashboardData();

    // Hook up all event listeners
    setupEventListeners();
});

// 2. Event Listeners Setup
function setupEventListeners() {
    // Search and Filtering triggers
    searchInput.addEventListener('input', debounce(loadTransactions, 300));
    filterType.addEventListener('change', loadTransactions);
    filterCategory.addEventListener('change', loadTransactions);

    // Modal triggers
    btnOpenAddModal.addEventListener('click', openModal);
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);
    transactionModal.addEventListener('click', (e) => {
        if (e.target === transactionModal) closeModal();
    });
    
    // Form submissions
    transactionForm.addEventListener('submit', handleAddTransaction);

    // Goal Edit Actions
    btnEditGoal.addEventListener('click', toggleGoalForm);
    btnCancelGoal.addEventListener('click', toggleGoalForm);
    goalForm.addEventListener('submit', handleUpdateGoal);
}

// 3. API Invocation & State Management

async function loadDashboardData() {
    try {
        await Promise.all([
            loadStats(),
            loadTransactions(),
            loadGoal()
        ]);
        setAPIStatus(true, 'Connected to API Server');
    } catch (error) {
        console.error('API connection failed:', error);
        setAPIStatus(false, 'Disconnected from Server');
    }
}

function setAPIStatus(connected, message) {
    if (connected) {
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = message;
        dbStatusBadge.textContent = 'Active';
        dbStatusBadge.className = 'badge badge-success';
    } else {
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = message;
        dbStatusBadge.textContent = 'Offline';
        dbStatusBadge.className = 'badge badge-danger';
    }
}

// Load Dashboard Metrics and Stats
async function loadStats() {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error('Failed to fetch statistics');
    const stats = await res.json();

    // Update balances and total amounts with transition animations
    animateValue(netBalanceEl, stats.net_balance, true);
    animateValue(totalIncomeEl, stats.total_income);
    animateValue(totalExpenseEl, stats.total_expense);

    // Update DB Connection UI Info
    if (stats.db_type) {
        dbEngineText.textContent = stats.db_type;
        dbScopeText.textContent = stats.db_scope;
        
        // Update header indicator with engine details
        setAPIStatus(true, `Connected to API (${stats.db_type})`);
    }

    // Balance Trend text formatting
    if (stats.net_balance > 0) {
        balanceTrendEl.textContent = 'Positive net balance. Great job!';
        balanceTrendEl.style.color = 'var(--color-income)';
    } else if (stats.net_balance < 0) {
        balanceTrendEl.textContent = 'Negative net balance. Review your expenses!';
        balanceTrendEl.style.color = 'var(--color-expense)';
    } else {
        balanceTrendEl.textContent = 'Neutral net balance.';
        balanceTrendEl.style.color = 'var(--text-muted)';
    }

    // Render Donut Chart
    renderChart(stats.categories, stats.total_expense);
}

// Load current savings target and progression
async function loadGoal() {
    const res = await fetch(`${API_BASE}/api/goals`);
    if (!res.ok) throw new Error('Failed to fetch goal settings');
    const goal = await res.json();

    const target = goal.target_amount || 0;
    const saved = goal.saved_amount || 0;
    
    // Set edit form values
    inputTargetAmount.value = target;
    inputSavedAmount.value = saved;

    // Display formatted target labels
    targetAmountText.textContent = formatCurrency(target);
    savedAmountText.textContent = formatCurrency(saved);
    
    let percent = 0;
    if (target > 0) {
        percent = Math.min(Math.round((saved / target) * 100), 100);
    }
    
    goalProgressBar.style.width = `${percent}%`;
    goalPercentText.textContent = `${percent}% reached`;
}

// Load and filter transaction logs
async function loadTransactions() {
    const search = searchInput.value;
    const type = filterType.value;
    const category = filterCategory.value;

    const url = new URL(`${API_BASE}/api/transactions`, window.location.origin);
    if (search) url.searchParams.append('search', search);
    if (type !== 'all') url.searchParams.append('type', type);
    if (category !== 'all') url.searchParams.append('category', category);

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch transactions');
    const transactions = await res.json();

    renderTransactionsTable(transactions);
}

// 4. DOM Rendering Processes

function renderTransactionsTable(transactions) {
    if (transactions.length === 0) {
        transactionsTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 muted">No transactions found.</td>
            </tr>
        `;
        return;
    }

    transactionsTableBody.innerHTML = transactions.map(t => {
        const valueClass = t.type === 'income' ? 'value-income' : 'value-expense';
        const sign = t.type === 'income' ? '+' : '-';
        const formattedDate = formatDate(t.date);
        
        return `
            <tr id="row-${t.id}">
                <td class="transaction-title-cell">${escapeHTML(t.description)}</td>
                <td><span class="badge-category" style="background-color: ${CATEGORY_COLORS[t.category] || '#64748b'}15; color: ${CATEGORY_COLORS[t.category] || '#64748b'}">${escapeHTML(t.category)}</span></td>
                <td class="muted">${formattedDate}</td>
                <td class="${valueClass} text-right">${sign} ${formatCurrency(t.amount)}</td>
                <td class="text-center">
                    <div class="action-buttons">
                        <button class="delete-btn" onclick="deleteTransaction(${t.id})" title="Delete Transaction">🗑</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Generate SVG Donut segments and update HTML legend elements
function renderChart(categories, totalExpense) {
    // Keep initial template layout (outer donut circle path skeleton)
    const baseCircles = expenseDonutChart.querySelectorAll('.donut-hole, .donut-ring');
    expenseDonutChart.innerHTML = '';
    baseCircles.forEach(c => expenseDonutChart.appendChild(c));
    chartLegend.innerHTML = '';

    const categoriesList = Object.entries(categories);

    if (categoriesList.length === 0 || totalExpense === 0) {
        chartLegend.innerHTML = `<div class="no-chart-data">No expense data to display.</div>`;
        return;
    }

    let accumulatedPercentage = 0;

    categoriesList.forEach(([category, value]) => {
        const percentage = (value / totalExpense) * 100;
        const color = CATEGORY_COLORS[category] || '#64748b';

        // Construct SVG circle path segment. Radius 15.9155 creates circumference of exactly 100.
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('class', 'donut-segment');
        circle.setAttribute('cx', '18');
        circle.setAttribute('cy', '18');
        circle.setAttribute('r', '15.91549430918954');
        circle.setAttribute('fill', 'transparent');
        circle.setAttribute('stroke', color);
        circle.setAttribute('stroke-width', '3');
        
        // Dasharray represents: stroke-length (fraction of 100) and spacing (remainder of 100)
        circle.setAttribute('stroke-dasharray', `${percentage.toFixed(4)} ${(100 - percentage).toFixed(4)}`);
        // Dashoffset rotates segment clockwise by negative accumulated percentages
        circle.setAttribute('stroke-dashoffset', `${(-accumulatedPercentage).toFixed(4)}`);
        
        expenseDonutChart.appendChild(circle);
        accumulatedPercentage += percentage;

        // Build corresponding legend DOM items
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background-color: ${color}"></span>
            <span>${escapeHTML(category)}</span>
            <span class="legend-value">${formatCurrency(value)}</span>
        `;
        chartLegend.appendChild(legendItem);
    });
}

// 5. Actions / Submissions

// Post a new Transaction record
async function handleAddTransaction(e) {
    e.preventDefault();

    const payload = {
        description: document.getElementById('transDescription').value,
        amount: parseFloat(document.getElementById('transAmount').value),
        type: document.getElementById('transType').value,
        category: document.getElementById('transCategory').value,
        date: document.getElementById('transDate').value
    };

    try {
        const res = await fetch(`${API_BASE}/api/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Add transaction action failed');

        // Form cleanup, modal close, reload datasets
        transactionForm.reset();
        transDateInput.value = new Date().toISOString().split('T')[0];
        closeModal();
        await loadDashboardData();
    } catch (error) {
        alert('Could not save transaction. Please try again.');
        console.error(error);
    }
}

// Delete transaction record by ID
async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;

    try {
        const res = await fetch(`${API_BASE}/api/transactions?id=${id}`, {
            method: 'DELETE'
        });

        if (!res.ok) throw new Error('Delete transaction action failed');

        // Transition animation out before refreshing details
        const row = document.getElementById(`row-${id}`);
        if (row) {
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            row.style.transition = 'all 0.3s ease';
            setTimeout(async () => {
                await loadDashboardData();
            }, 300);
        } else {
            await loadDashboardData();
        }
    } catch (error) {
        alert('Could not delete transaction. Please try again.');
        console.error(error);
    }
}

// Update saving goals
async function handleUpdateGoal(e) {
    e.preventDefault();

    const payload = {
        target_amount: parseFloat(inputTargetAmount.value),
        saved_amount: parseFloat(inputSavedAmount.value)
    };

    try {
        const res = await fetch(`${API_BASE}/api/goals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Update target goal failed');

        toggleGoalForm();
        await loadGoal();
        await loadStats(); // Reload stats as net balance/ratios might be relative
    } catch (error) {
        alert('Could not update savings goal.');
        console.error(error);
    }
}

// 6. Modal / Form Visibility toggles

function openModal() {
    transactionModal.classList.add('show');
}

// Close Modal wrapper
function closeModal() {
    transactionModal.classList.remove('show');
}

// Toggle Inline Goal Form display
function toggleGoalForm() {
    goalForm.classList.toggle('hidden');
}

// 7. Utility Helpers

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    const dateObj = new Date(year, month - 1, day);
    return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// Number rolling counter logic for sleek user experience
function animateValue(obj, endValue, handleNegative = false) {
    let start = 0;
    const duration = 400; // ms transition duration
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // easeOutQuad transition easing
        const easeProgress = progress * (2 - progress);
        const currentValue = start + (endValue - start) * easeProgress;
        
        obj.textContent = formatCurrency(currentValue);
        
        // Style changes if handling negative net values
        if (handleNegative) {
            if (endValue < 0) {
                obj.style.color = 'var(--color-expense)';
            } else {
                obj.style.color = 'var(--text-primary)';
            }
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// General debounce delay helper for inputs
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
