// Hardcoded project data (will be replaced with WebSocket later)
const projectsData = [
    {
        id: 1,
        name: "Main API Server",
        status: "healthy",
        description: "Core REST API handling all business logic",
        uptime: "99.9%",
        lastCheck: "2 mins ago",
        responseTime: "145ms"
    },
    {
        id: 2,
        name: "Authentication Service",
        status: "healthy",
        description: "OAuth2 and JWT token management service",
        uptime: "99.8%",
        lastCheck: "1 min ago",
        responseTime: "89ms"
    },
    {
        id: 3,
        name: "Database Cluster",
        status: "failed",
        description: "PostgreSQL primary and replica nodes",
        uptime: "95.2%",
        lastCheck: "30 secs ago",
        responseTime: "N/A"
    },
    {
        id: 4,
        name: "Payment Gateway",
        status: "healthy",
        description: "Stripe payment processing integration",
        uptime: "100%",
        lastCheck: "3 mins ago",
        responseTime: "234ms"
    },
    {
        id: 5,
        name: "Email Service",
        status: "healthy",
        description: "SMTP and email template rendering service",
        uptime: "98.7%",
        lastCheck: "5 mins ago",
        responseTime: "412ms"
    },
    {
        id: 6,
        name: "File Storage",
        status: "healthy",
        description: "S3-compatible object storage service",
        uptime: "99.5%",
        lastCheck: "1 min ago",
        responseTime: "178ms"
    },
    {
        id: 7,
        name: "WebSocket Server",
        status: "failed",
        description: "Real-time bidirectional communication server",
        uptime: "92.1%",
        lastCheck: "45 secs ago",
        responseTime: "N/A"
    },
    {
        id: 8,
        name: "Cache Layer",
        status: "healthy",
        description: "Redis distributed caching system",
        uptime: "99.9%",
        lastCheck: "2 mins ago",
        responseTime: "12ms"
    }
];

// Hardcoded FAQs data
const faqsData = [
    {
        id: 1,
        question: "What does the health monitor track?",
        answer: "The health monitor continuously tracks the status of all critical system components including API servers, databases, authentication services, payment gateways, and more. It monitors uptime, response times, and overall system health to ensure smooth operations."
    },
    {
        id: 2,
        question: "How often are the health checks performed?",
        answer: "Health checks are performed every 30 seconds for all services. Critical services like the main API and authentication service are checked every 15 seconds to ensure immediate detection of any issues."
    },
    {
        id: 3,
        question: "What do the different status colors mean?",
        answer: "Green indicates a healthy service with normal operations and good response times. Red indicates a failed or critical service that requires immediate attention. Yellow (if present) indicates a warning state where the service is running but experiencing degraded performance."
    },
    {
        id: 4,
        question: "How are you notified of failures?",
        answer: "When a service fails, the system automatically sends notifications through multiple channels including email, SMS, and Slack messages. Critical failures trigger immediate alerts to the on-call team, while minor issues are logged for review during business hours."
    },
    {
        id: 5,
        question: "Can I view historical health data?",
        answer: "Yes, the system maintains a complete history of all health checks and status changes. You can access detailed logs, generate reports, and view trends over time to identify patterns and potential issues before they become critical."
    },
    {
        id: 6,
        question: "What is considered a healthy uptime percentage?",
        answer: "We aim for 99.9% uptime (three nines) for critical services, which allows for approximately 43 minutes of downtime per month. Services below 99% uptime are flagged for investigation and improvement."
    },
    {
        id: 7,
        question: "How do I add a new service to monitor?",
        answer: "New services can be added through the configuration panel in the admin settings. You'll need to specify the service name, endpoint URL, expected response codes, timeout thresholds, and notification preferences. Once configured, monitoring begins automatically."
    },
    {
        id: 8,
        question: "What happens during scheduled maintenance?",
        answer: "During scheduled maintenance windows, you can temporarily suppress alerts for specific services. The system will continue to monitor and log data, but won't trigger notifications. Maintenance windows should be scheduled in advance and communicated to all stakeholders."
    },
    {
        id: 9,
        question: "Can I customize alert thresholds?",
        answer: "Yes, alert thresholds are fully customizable per service. You can set custom values for response time warnings, error rate thresholds, and uptime requirements based on the criticality and expected performance of each service."
    },
    {
        id: 10,
        question: "Is the monitoring data secure?",
        answer: "All monitoring data is encrypted at rest and in transit. Access to the admin panel is restricted through multi-factor authentication, and all actions are logged for audit purposes. Sensitive information in health check responses is automatically redacted."
    }
];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadScripts();
    loadFAQs();
    refreshWSLogs(); // Load WebSocket logs on dashboard
    refreshOrchestratorLogs(); // Load Orchestrator logs on dashboard
    updateHealthCards(); // Load health status on dashboard

    // Auto-refresh logs based on active page
    setInterval(() => {
        const logsPage = document.getElementById('logs-page');
        const dashboardPage = document.getElementById('dashboard-page');

        if (logsPage && logsPage.classList.contains('active')) {
            refreshLogs();
        }

        if (dashboardPage && dashboardPage.classList.contains('active')) {
            refreshWSLogs();
            refreshOrchestratorLogs();
            updateHealthCards();
        }
    }, 3000); // Refresh every 3 seconds
});

// Navigation handling
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Show corresponding page
            const pageName = item.getAttribute('data-page');
            showPage(pageName);
        });
    });
}

function showPage(pageName) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));

    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');

        // Load page-specific data
        if (pageName === 'scripts') {
            loadScripts();
        } else if (pageName === 'logs') {
            refreshLogs();
        } else if (pageName === 'dashboard') {
            refreshWSLogs();
            refreshOrchestratorLogs();
            updateHealthCards();
        }
    }
}

// Load and render projects
function loadProjects() {
    const projectsGrid = document.getElementById('projects-grid');
    projectsGrid.innerHTML = '';

    projectsData.forEach(project => {
        const projectCard = createProjectCard(project);
        projectsGrid.appendChild(projectCard);
    });
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';

    const statusClass = project.status === 'healthy' ? 'healthy' : 'failed';
    const statusText = project.status === 'healthy' ? 'Healthy' : 'Failed';
    const uptime = parseFloat(project.uptime);

    card.innerHTML = `
        <div class="project-header">
            <h3 class="project-name">${project.name}</h3>
            <span class="status-badge ${statusClass}">${statusText}</span>
        </div>
        <p class="project-description">${project.description}</p>
        <div class="project-details">
            <div class="detail-row">
                <span class="detail-label">Uptime</span>
                <span class="detail-value">${project.uptime}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Response Time</span>
                <span class="detail-value">${project.responseTime}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Last Check</span>
                <span class="detail-value">${project.lastCheck}</span>
            </div>
        </div>
        <div class="status-bar">
            <div class="status-bar-fill ${statusClass}" style="width: ${uptime}%"></div>
        </div>
    `;

    return card;
}

// Update status summary
function updateStatusSummary() {
    const totalProjects = projectsData.length;
    const healthyCount = projectsData.filter(p => p.status === 'healthy').length;
    const failedCount = projectsData.filter(p => p.status === 'failed').length;

    document.getElementById('total-projects').textContent = totalProjects;
    document.getElementById('healthy-count').textContent = healthyCount;
    document.getElementById('failed-count').textContent = failedCount;
}

// Load and render FAQs
function loadFAQs() {
    const accordion = document.getElementById('faqs-accordion');
    accordion.innerHTML = '';

    faqsData.forEach(faq => {
        const accordionItem = createAccordionItem(faq);
        accordion.appendChild(accordionItem);
    });
}

function createAccordionItem(faq) {
    const item = document.createElement('div');
    item.className = 'accordion-item';

    item.innerHTML = `
        <div class="accordion-header">
            <h3 class="accordion-title">${faq.question}</h3>
            <span class="accordion-icon">▼</span>
        </div>
        <div class="accordion-content">
            <div class="accordion-content-inner">
                ${faq.answer}
            </div>
        </div>
    `;

    const header = item.querySelector('.accordion-header');
    header.addEventListener('click', () => {
        const isActive = item.classList.contains('active');

        // Close all accordion items
        document.querySelectorAll('.accordion-item').forEach(accItem => {
            accItem.classList.remove('active');
        });

        // Toggle current item
        if (!isActive) {
            item.classList.add('active');
        }
    });

    return item;
}

// Simulate real-time updates (will be replaced with WebSocket)
setInterval(() => {
    // Randomly update a project status for demo purposes
    const randomIndex = Math.floor(Math.random() * projectsData.length);
    const randomStatus = Math.random() > 0.2 ? 'healthy' : 'failed';

    // Only update if status actually changes
    if (projectsData[randomIndex].status !== randomStatus) {
        projectsData[randomIndex].status = randomStatus;
        loadProjects();
        updateStatusSummary();
    }
}, 10000); // Update every 10 seconds

// ========== Script Manager Functions ==========

async function loadScripts() {
    const scriptsGrid = document.getElementById('scripts-grid');
    if (!scriptsGrid) return;

    scriptsGrid.innerHTML = '<div class="loading">Loading scripts...</div>';

    try {
        const response = await fetch('/api/scripts');
        const data = await response.json();

        scriptsGrid.innerHTML = '';

        data.scripts.forEach(script => {
            const scriptCard = createScriptCard(script);
            scriptsGrid.appendChild(scriptCard);
        });
    } catch (error) {
        scriptsGrid.innerHTML = '<div class="error">Failed to load scripts</div>';
        console.error('Error loading scripts:', error);
    }
}

function createScriptCard(script) {
    const card = document.createElement('div');
    card.className = 'script-card';

    const statusClass = script.exists ? 'script-available' : 'script-missing';
    const statusText = script.exists ? 'Available' : 'Not Found';

    let sizeText = 'N/A';
    if (script.size !== undefined) {
        sizeText = script.size < 1024 ? `${script.size} B` : `${(script.size / 1024).toFixed(2)} KB`;
    }

    card.innerHTML = `
        <div class="script-header">
            <h3 class="script-name">${script.name}</h3>
            <span class="status-badge ${statusClass}">${statusText}</span>
        </div>
        <div class="script-details">
            <div class="detail-row">
                <span class="detail-label">📄 Size</span>
                <span class="detail-value">${sizeText}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">📂 Path</span>
                <span class="detail-value script-path">${script.path || 'Not available'}</span>
            </div>
        </div>
        <button 
            class="btn btn-primary btn-run-script" 
            onclick="runScript('${script.name}')"
            ${!script.exists ? 'disabled' : ''}
        >
            ▶️ Execute Script
        </button>
    `;

    return card;
}

async function runScript(scriptName) {
    const button = event.target;
    const originalText = button.innerHTML;

    button.disabled = true;
    button.innerHTML = '⏳ Executing...';

    try {
        const response = await fetch(`/run/${scriptName}`);
        const data = await response.json();

        if (data.success) {
            showNotification(`✅ ${data.message}`, 'success');
            button.innerHTML = '✓ Executed';

            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 2000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// ========== Logs Functions ==========

async function refreshLogs() {
    const logsContent = document.getElementById('logs-content');
    if (!logsContent) return;

    try {
        const response = await fetch('/api/logs');
        const data = await response.json();

        if (data.logs) {
            logsContent.textContent = data.logs || 'No logs available';
        } else {
            logsContent.textContent = data.message || 'No logs available';
        }

        // Auto-scroll to bottom
        logsContent.scrollTop = logsContent.scrollHeight;
    } catch (error) {
        logsContent.textContent = `Error loading logs: ${error.message}`;
        console.error('Error loading logs:', error);
    }
}

async function clearLogs() {
    if (!confirm('Are you sure you want to clear all logs?')) {
        return;
    }

    try {
        const response = await fetch('/clear-logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Logs cleared successfully', 'success');
            refreshLogs();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error clearing logs: ${error.message}`, 'error');
    }
}

// ========== Notification System ==========

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ========== Upgrade Checker Functions ==========

async function runUpgradeChecker() {
    const button = event.target.closest('.btn');
    const originalText = button.innerHTML;

    button.disabled = true;
    button.innerHTML = '⏳ Running...';

    try {
        // Run the Windows batch file instead of the Python script
        const response = await fetch('/run/UpdateChecker.bat');
        const data = await response.json();

        if (data.success) {
            showNotification('✅ Upgrade checker opened in new terminal', 'success');
            button.innerHTML = '✓ Opened Terminal';

            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 2000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}


// Run Health WebSocket Simulator
async function runHealthSimulator() {
    const button = event ? event.target.closest('.btn') : null;
    const originalText = button ? button.innerHTML : 'Running...';

    if (button) {
        button.disabled = true;
        button.innerHTML = '⏳ Starting...';
    }

    try {
        const response = await fetch('/run/health_websocket_simulator.py');
        const data = await response.json();

        if (data.success) {
            showNotification('✅ Health WS Simulator opened in new terminal', 'success');
            if (button) button.innerHTML = '✓ Opened Terminal';

            setTimeout(() => {
                if (button) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            }, 2000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
        if (button) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
}

// ========== Terminal Log Functions ==========

async function refreshWSLogs() {
    const wsContent = document.getElementById('ws-terminal-content');
    if (!wsContent) return;

    try {
        const response = await fetch('/api/ws-logs');
        const data = await response.json();

        if (data.logs) {
            wsContent.textContent = data.logs;
        } else {
            wsContent.textContent = 'No logs available';
        }

        // Auto-scroll to bottom
        const viewer = document.getElementById('ws-terminal-viewer');
        if (viewer) {
            viewer.scrollTop = viewer.scrollHeight;
        }
    } catch (error) {
        wsContent.textContent = `Error loading WebSocket logs: ${error.message}`;
        console.error('Error loading WebSocket logs:', error);
    }
}

async function clearWSLogs() {
    if (!confirm('Are you sure you want to clear the WebSocket server logs?')) {
        return;
    }

    try {
        const response = await fetch('/api/clear-ws-logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ WebSocket logs cleared successfully', 'success');
            refreshWSLogs();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error clearing logs: ${error.message}`, 'error');
    }
}

async function refreshOrchestratorLogs() {
    const orchestratorContent = document.getElementById('orchestrator-terminal-content');
    if (!orchestratorContent) return;

    try {
        const response = await fetch('/api/orchestrator-logs');
        const data = await response.json();

        if (data.logs) {
            orchestratorContent.textContent = data.logs;
        } else {
            orchestratorContent.textContent = 'No logs available';
        }

        // Auto-scroll to bottom
        const viewer = document.getElementById('orchestrator-terminal-viewer');
        if (viewer) {
            viewer.scrollTop = viewer.scrollHeight;
        }
    } catch (error) {
        orchestratorContent.textContent = `Error loading Orchestrator logs: ${error.message}`;
        console.error('Error loading Orchestrator logs:', error);
    }
}

async function clearOrchestratorLogs() {
    if (!confirm('Are you sure you want to clear the Orchestrator logs?')) {
        return;
    }

    try {
        const response = await fetch('/api/clear-orchestrator-logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Orchestrator logs cleared successfully', 'success');
            refreshOrchestratorLogs();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        showNotification(`❌ Error clearing logs: ${error.message}`, 'error');
    }
}

// ========== Health Status Functions ==========

async function updateHealthCards() {
    try {
        const response = await fetch('/api/health-status');
        const data = await response.json();

        if (data.health) {
            // Update each health card
            ['1', '2', '3'].forEach(num => {
                const appName = `${num}.py`;
                const healthData = data.health[appName];

                if (healthData) {
                    const statusElement = document.getElementById(`status-${num}`);
                    const indicatorElement = document.getElementById(`indicator-${num}`);
                    const cardElement = document.getElementById(`health-card-${num}`);

                    if (statusElement && indicatorElement && cardElement) {
                        // Update status text
                        statusElement.textContent = healthData.status;

                        // Update card classes based on health
                        if (healthData.healthy) {
                            cardElement.classList.remove('unhealthy');
                            cardElement.classList.add('healthy');
                            indicatorElement.classList.remove('unhealthy');
                            indicatorElement.classList.add('healthy');
                        } else {
                            cardElement.classList.remove('healthy');
                            cardElement.classList.add('unhealthy');
                            indicatorElement.classList.remove('healthy');
                            indicatorElement.classList.add('unhealthy');
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error updating health cards:', error);
    }
}



