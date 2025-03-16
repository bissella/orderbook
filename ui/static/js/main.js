// Global variables
let apiKey = localStorage.getItem('apiKey');
let selectedCommodityId = null;
let commodities = {};
let orderBookIntervalId = null;

// DOM elements
const authSection = document.getElementById('auth-section');
const mainContent = document.getElementById('main-content');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const orderForm = document.getElementById('order-form');
const commodityForm = document.getElementById('commodity-form');
const commoditySelect = document.getElementById('commodity-select');
const customerName = document.getElementById('customer-name');
const logoutBtn = document.getElementById('logout-btn');
const addCommodityBtn = document.getElementById('add-commodity-btn');
const saveCommodityBtn = document.getElementById('save-commodity-btn');

// Bootstrap modal
let commodityModal;

// Initialize the app
document.addEventListener('DOMContentLoaded', initApp);

function initApp() {
    console.log("Initializing app...");
    
    // Initialize Bootstrap components
    const modalElement = document.getElementById('commodity-modal');
    if (modalElement) {
        commodityModal = new bootstrap.Modal(modalElement);
    } else {
        console.warn("Commodity modal element not found");
    }
    
    // Check if user is logged in
    if (apiKey) {
        console.log("API key found, fetching customer info...");
        fetchCustomerInfo();
    } else {
        console.log("No API key found, showing auth section");
        showAuthSection();
    }

    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    console.log("Setting up event listeners...");
    
    // Auth forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);

    // Order form
    orderForm.addEventListener('submit', handleCreateOrder);

    // Commodity selection and creation
    commoditySelect.addEventListener('change', handleCommodityChange);
    if (addCommodityBtn) {
        addCommodityBtn.addEventListener('click', () => {
            if (commodityModal) commodityModal.show();
        });
    }
    if (saveCommodityBtn) {
        saveCommodityBtn.addEventListener('click', handleCreateCommodity);
    }

    // Orders/Trades tab handling
    const tabsElement = document.getElementById('orders-trades-tabs');
    if (tabsElement) {
        tabsElement.addEventListener('shown.bs.tab', function (e) {
            if (e.target.id === 'orders-tab') {
                fetchOrders();
            } else if (e.target.id === 'trades-tab') {
                fetchTrades();
            }
        });
    }
}

// Authentication functions
async function handleLogin(e) {
    e.preventDefault();
    console.log("Handling login...");
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        console.log("Sending login request...");
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        console.log("Login response:", data);
        
        if (response.ok) {
            console.log("Login successful");
            apiKey = data.api_key;
            localStorage.setItem('apiKey', apiKey);
            customerName.textContent = data.customer.name;
            
            // First fetch commodities so we have data to display
            await fetchCommodities();
            
            // Show main content after getting data
            showMainContent();
            
            // Setup order book updates
            await setupOrderBookUpdates();
            
            // Fetch user orders
            await fetchOrders();
            
            showSuccess("Login successful! Welcome to the Order Book System.");
        } else {
            console.error("Login failed:", data.error);
            showError(data.error || 'Login failed');
        }
    } catch (error) {
        console.error("Login error:", error);
        showError('Error during login: ' + error.message);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    console.log("Handling register...");
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    // Validate password match
    if (password !== confirmPassword) {
        console.error("Passwords do not match");
        showError('Passwords do not match');
        return;
    }
    
    try {
        console.log("Sending register request...");
        const response = await fetch('/api/customers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        console.log("Register response:", data);
        
        if (response.ok) {
            console.log("Register successful");
            apiKey = data.api_key;
            localStorage.setItem('apiKey', apiKey);
            showSuccess('Registration successful! You are now logged in.');
            customerName.textContent = data.name;
            showMainContent();
            await fetchCommodities();
        } else {
            console.error("Register failed:", data.error);
            showError(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error("Register error:", error);
        showError('Error during registration: ' + error.message);
    }
}

function handleLogout() {
    console.log("Handling logout...");
    apiKey = null;
    localStorage.removeItem('apiKey');
    showAuthSection();
    clearInterval(orderBookIntervalId);
}

async function fetchCustomerInfo() {
    console.log("Fetching customer info...");
    try {
        const response = await fetch('/api/customers', {
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            const customer = await response.json();
            console.log("Customer info:", customer);
            customerName.textContent = customer.name;
            logoutBtn.classList.remove('d-none');
            
            // Fetch other data
            await fetchCommodities();
            showMainContent();
            await setupOrderBookUpdates();
            await fetchOrders();
        } else {
            console.error("Invalid API key");
            // Invalid API key
            apiKey = null;
            localStorage.removeItem('apiKey');
            showAuthSection();
        }
    } catch (error) {
        console.error("Error fetching customer info:", error);
        showError('Error fetching customer info: ' + error.message);
    }
}

// Commodity functions
async function fetchCommodities() {
    console.log("Fetching commodities...");
    try {
        const response = await fetch('/api/commodities', {
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            commodities = {};
            
            // Clear select options
            commoditySelect.innerHTML = '<option value="">Select a commodity...</option>';
            
            // Add commodities to select
            data.forEach(commodity => {
                commodities[commodity.id] = commodity;
                const option = document.createElement('option');
                option.value = commodity.id;
                option.textContent = `${commodity.name} (${commodity.symbol})`;
                commoditySelect.appendChild(option);
            });
            
            // If there are commodities, select the first one
            if (data.length > 0) {
                commoditySelect.value = data[0].id;
                handleCommodityChange();
            }
        }
    } catch (error) {
        console.error("Error fetching commodities:", error);
        showError('Error fetching commodities: ' + error.message);
    }
}

async function handleCreateCommodity() {
    console.log("Handling create commodity...");
    const name = document.getElementById('commodity-name').value;
    const symbol = document.getElementById('commodity-symbol').value;
    const description = document.getElementById('commodity-description').value;
    
    try {
        console.log("Sending create commodity request...");
        const response = await fetch('/api/commodities', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({ name, symbol, description })
        });
        
        if (response.ok) {
            const commodity = await response.json();
            console.log("Commodity created:", commodity);
            showSuccess(`Commodity ${commodity.name} created successfully!`);
            commodityModal.hide();
            document.getElementById('commodity-form').reset();
            await fetchCommodities();
        } else {
            const data = await response.json();
            console.error("Create commodity failed:", data.error);
            showError('Failed to create commodity: ' + data.error);
        }
    } catch (error) {
        console.error("Create commodity error:", error);
        showError('Error creating commodity: ' + error.message);
    }
}

function handleCommodityChange() {
    console.log("Handling commodity change...");
    selectedCommodityId = commoditySelect.value;
    
    if (selectedCommodityId) {
        // Start fetching order book for selected commodity
        fetchOrderBook();
        
        // Setup interval to refresh order book
        clearInterval(orderBookIntervalId);
        orderBookIntervalId = setInterval(fetchOrderBook, 5000);
    } else {
        // Clear order book if no commodity selected
        clearInterval(orderBookIntervalId);
        document.getElementById('bids-table').innerHTML = '';
        document.getElementById('asks-table').innerHTML = '';
    }
}

// Order book functions
async function fetchOrderBook() {
    console.log("Fetching order book...");
    if (!selectedCommodityId) return;
    
    try {
        const response = await fetch(`/api/orderbook/${selectedCommodityId}`, {
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateOrderBook(data);
        }
    } catch (error) {
        console.error("Error fetching order book:", error);
    }
}

function updateOrderBook(data) {
    console.log("Updating order book...");
    const bidsTable = document.getElementById('bids-table');
    const asksTable = document.getElementById('asks-table');
    
    // Clear tables
    bidsTable.innerHTML = '';
    asksTable.innerHTML = '';
    
    // Add bids (buy orders)
    data.bids.forEach(bid => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${bid.price.toFixed(2)}</td>
            <td>${bid.quantity.toFixed(2)}</td>
        `;
        bidsTable.appendChild(row);
    });
    
    // Add asks (sell orders)
    data.asks.forEach(ask => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${ask.price.toFixed(2)}</td>
            <td>${ask.quantity.toFixed(2)}</td>
        `;
        asksTable.appendChild(row);
    });
}

// Setup order book updates
async function setupOrderBookUpdates() {
    console.log("Setting up order book updates...");
    // Clear existing interval if any
    if (orderBookIntervalId) {
        clearInterval(orderBookIntervalId);
    }
    
    // Fetch initial order book
    if (selectedCommodityId) {
        await fetchOrderBook();
    }
    
    // Setup interval for updates
    orderBookIntervalId = setInterval(async () => {
        if (selectedCommodityId) {
            await fetchOrderBook();
        }
    }, 5000); // Update every 5 seconds
}

// Order functions
async function handleCreateOrder(e) {
    e.preventDefault();
    console.log("Handling create order...");
    
    if (!selectedCommodityId) {
        console.error("No commodity selected");
        showError('Please select a commodity first');
        return;
    }
    
    const orderType = document.getElementById('order-type').value;
    const price = parseFloat(document.getElementById('order-price').value);
    const quantity = parseFloat(document.getElementById('order-quantity').value);
    
    try {
        console.log("Sending create order request...");
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({
                commodity_id: parseInt(selectedCommodityId),
                order_type: orderType,
                price,
                quantity
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log("Order created:", data);
            showSuccess(`Order placed successfully!`);
            
            // If there were trades executed immediately, show info
            if (data.trades && data.trades.length > 0) {
                showSuccess(`Order matched with ${data.trades.length} existing order(s)!`);
            }
            
            // Reset form
            orderForm.reset();
            
            // Refresh orders and order book
            fetchOrders();
            fetchOrderBook();
        } else {
            const data = await response.json();
            console.error("Create order failed:", data.error);
            showError('Failed to place order: ' + data.error);
        }
    } catch (error) {
        console.error("Create order error:", error);
        showError('Error placing order: ' + error.message);
    }
}

async function fetchOrders() {
    console.log("Fetching orders...");
    try {
        const response = await fetch('/api/orders', {
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            const orders = await response.json();
            updateOrdersTable(orders);
        }
    } catch (error) {
        console.error("Error fetching orders:", error);
        showError('Error fetching orders: ' + error.message);
    }
}

function updateOrdersTable(orders) {
    console.log("Updating orders table...");
    const ordersTable = document.getElementById('orders-table');
    
    // Clear table
    ordersTable.innerHTML = '';
    
    if (orders.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="text-center">No orders yet</td>';
        ordersTable.appendChild(row);
        return;
    }
    
    // Add orders
    orders.forEach(order => {
        const row = document.createElement('tr');
        const commodity = commodities[order.commodity_id] || { symbol: 'Unknown' };
        
        row.innerHTML = `
            <td>${order.id}</td>
            <td class="type-${order.order_type}">${order.order_type.toUpperCase()}</td>
            <td>${commodity.symbol}</td>
            <td>${order.price.toFixed(2)}</td>
            <td>${order.quantity.toFixed(2)}</td>
            <td>${order.filled_quantity.toFixed(2)}</td>
            <td class="status-${order.status}">${order.status.replace('_', ' ').toUpperCase()}</td>
            <td>
                ${order.status === 'open' || order.status === 'partially_filled' ? 
                    `<button class="btn btn-sm btn-outline-danger cancel-order" data-id="${order.id}">Cancel</button>` : 
                    ''}
            </td>
        `;
        ordersTable.appendChild(row);
    });
    
    // Add event listeners to cancel buttons
    document.querySelectorAll('.cancel-order').forEach(button => {
        button.addEventListener('click', () => cancelOrder(button.dataset.id));
    });
}

async function cancelOrder(orderId) {
    console.log("Canceling order...");
    try {
        const response = await fetch(`/api/orders/${orderId}`, {
            method: 'DELETE',
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            console.log("Order canceled");
            showSuccess('Order cancelled successfully');
            fetchOrders();
            fetchOrderBook();
        } else {
            const data = await response.json();
            console.error("Cancel order failed:", data.error);
            showError('Failed to cancel order: ' + data.error);
        }
    } catch (error) {
        console.error("Cancel order error:", error);
        showError('Error cancelling order: ' + error.message);
    }
}

// Trade functions
async function fetchTrades() {
    console.log("Fetching trades...");
    try {
        const response = await fetch('/api/trades', {
            headers: {
                'X-API-Key': apiKey
            }
        });
        
        if (response.ok) {
            const trades = await response.json();
            updateTradesTable(trades);
        }
    } catch (error) {
        console.error("Error fetching trades:", error);
        showError('Error fetching trades: ' + error.message);
    }
}

function updateTradesTable(trades) {
    console.log("Updating trades table...");
    const tradesTable = document.getElementById('trades-table');
    
    // Clear table
    tradesTable.innerHTML = '';
    
    if (trades.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="text-center">No trades yet</td>';
        tradesTable.appendChild(row);
        return;
    }
    
    // Add trades
    trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.id}</td>
            <td>${trade.order_id}</td>
            <td>${trade.price.toFixed(2)}</td>
            <td>${trade.quantity.toFixed(2)}</td>
            <td>${new Date(trade.executed_at).toLocaleString()}</td>
        `;
        tradesTable.appendChild(row);
    });
}

// UI helper functions
function showAuthSection() {
    console.log("Showing auth section");
    authSection.classList.remove('d-none');
    mainContent.classList.add('d-none');
    customerName.textContent = '';
    logoutBtn.classList.add('d-none');
}

function showMainContent() {
    console.log("Showing main content");
    authSection.classList.add('d-none');
    mainContent.classList.remove('d-none');
    logoutBtn.classList.remove('d-none');
}

function showError(message) {
    console.log("Showing error:", message);
    // Create a Bootstrap toast for error messages
    createToast(message, 'bg-danger');
}

function showSuccess(message) {
    console.log("Showing success:", message);
    // Create a Bootstrap toast for success messages
    createToast(message, 'bg-success text-white');
}

function createToast(message, bgClass) {
    console.log("Creating toast...");
    // Check if toast container exists, create if not
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast ${bgClass} text-white`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Notification</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
    
    // Remove after hiding
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}
