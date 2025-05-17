/**
 * PySnip Explorer - Advanced JavaScript
 * Provides enhanced interactivity and user experience for the PySnip web interface
 */

// Main configuration
const config = {
    animationDuration: 300,
    transitionEasing: 'ease',
    terminalMaxLines: 1000,
    executeTimeout: 60000, // 60 seconds
    codeTheme: 'atom-one-dark',
    defaultCategory: 'all',
    notificationDuration: 3000
};

// Store application state
const appState = {
    currentTheme: localStorage.getItem('theme') || 'dark',
    isExecuting: false,
    lastExecutionResult: null,
    activeTab: 'execution',
    categoryFilter: config.defaultCategory,
    loadedTools: {},
    searchQuery: '',
    executionHistory: JSON.parse(localStorage.getItem('executionHistory')) || []
};

// DOM ready initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('PySnip Explorer Initialized');
    
    // Initialize user interface components
    initThemeToggle();
    initBackToTop();
    initTooltips();
    initCodeHighlighting();
    initAnimations();
    initNavigation();
    initToolExecution();
    
    // Add loading indicator functionality
    setupLoadingIndicator();
    
    // Enable custom scrollbars and smooth scroll
    enableSmoothScroll();
    
    // Handle category filters if present
    setupCategoryFilters();
    
    // Setup collapsible sections
    setupCollapsibles();
    
    // Setup documentation viewer
    setupDocViewer();
    
    // Initialize dynamic counters
    initCounters();
    
    // Hide loading overlay (if shown during page load)
    hideLoadingOverlay();
});

/**
 * Theme Switching Functionality
 * Toggles between light and dark themes with smooth transitions
 */
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeToggle = document.querySelector('.theme-toggle');
    
    // Apply initial theme
    document.documentElement.setAttribute('data-bs-theme', appState.currentTheme);
    updateThemeIcon();
    
    // Set up theme toggle button
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
    
    // Update theme icon based on current theme
    function updateThemeIcon() {
        if (!themeToggleBtn) return;
        
        if (appState.currentTheme === 'dark') {
            themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.classList.add('dark-mode');
        } else {
            themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.classList.remove('dark-mode');
        }
    }
    
    // Toggle between light and dark themes
    function toggleTheme() {
        appState.currentTheme = appState.currentTheme === 'dark' ? 'light' : 'dark';
        
        // Save theme preference to localStorage
        localStorage.setItem('theme', appState.currentTheme);
        
        // Apply theme to document
        document.documentElement.setAttribute('data-bs-theme', appState.currentTheme);
        
        // Update theme icon
        updateThemeIcon();
        
        // Apply theme-specific styles to code blocks
        updateCodeTheme();
        
        // Add transition effects
        document.body.classList.add('theme-transition');
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 1000);
    }
    
    // Update code highlighting theme based on current theme
    function updateCodeTheme() {
        const codeBlocks = document.querySelectorAll('pre code');
        const darkTheme = appState.currentTheme === 'dark' ? 'atom-one-dark' : 'atom-one-light';
        
        // Update hljs theme if available
        const oldThemeLink = document.querySelector('link[href*="highlight"]');
        if (oldThemeLink) {
            const newThemeLink = document.createElement('link');
            newThemeLink.rel = 'stylesheet';
            newThemeLink.href = oldThemeLink.href.replace(/(atom-one-)(dark|light)/, `$1${appState.currentTheme}`);
            newThemeLink.onload = function() {
                oldThemeLink.remove();
                // Re-highlight code blocks
                if (window.hljs) {
                    codeBlocks.forEach(block => {
                        hljs.highlightElement(block);
                    });
                }
            };
            document.head.appendChild(newThemeLink);
        }
    }
}

/**
 * Back to Top Button
 * Shows/hides back to top button based on scroll position
 */
function initBackToTop() {
    const backToTopBtn = document.getElementById('back-to-top');
    
    if (!backToTopBtn) return;
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    // Scroll to top when clicked
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * Initialize tooltips and other Bootstrap components
 */
function initTooltips() {
    // Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

/**
 * Code Highlighting
 * Initializes syntax highlighting for code blocks
 */
function initCodeHighlighting() {
    if (window.hljs) {
        // Highlight all code blocks
        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
        
        // Add copy buttons to code blocks
        document.querySelectorAll('pre').forEach(block => {
            if (!block.querySelector('.copy-btn') && block.querySelector('code')) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                copyBtn.setAttribute('title', 'Copy to clipboard');
                copyBtn.setAttribute('aria-label', 'Copy to clipboard');
                
                copyBtn.addEventListener('click', () => {
                    const code = block.querySelector('code').textContent;
                    copyToClipboard(code, copyBtn);
                });
                
                block.appendChild(copyBtn);
            }
        });
    }
}

/**
 * Initialize animations for page elements
 */
function initAnimations() {
    // Initialize AOS animations if available
    if (window.AOS) {
        AOS.init({
            duration: 800,
            easing: 'ease-out',
            once: true,
            offset: 100
        });
    }
    
    // Add custom animations for elements
    document.querySelectorAll('.animate-fadeIn').forEach(element => {
        element.style.opacity = 0;
        element.style.transform = 'translateY(20px)';
        
        // Use Intersection Observer to trigger animation when element is visible
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'fadeIn 0.5s forwards';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(element);
    });
}

/**
 * Setup navigation behavior
 */
function initNavigation() {
    // Handle navigation links active state
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath === linkPath) {
            link.classList.add('active');
        }
    });
    
    // Handle tab navigation
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', event => {
            appState.activeTab = event.target.getAttribute('aria-controls');
            
            // Trigger specific actions based on the tab
            if (appState.activeTab === 'documentation' && !document.querySelector('.documentation-loaded')) {
                loadDocumentation();
            } else if (appState.activeTab === 'source' && !document.querySelector('.source-loaded')) {
                loadSourceCode();
            }
        });
    });
}

/**
 * Setup execution interface for tools
 */
function initToolExecution() {
    const executeBtn = document.getElementById('execute-button');
    const resetBtn = document.getElementById('reset-params');
    const outputContainer = document.getElementById('output-container');
    const toolPath = document.querySelector('[data-tool-path]')?.getAttribute('data-tool-path');
    
    if (!executeBtn || !toolPath) return;
    
    // Load parameters for the tool
    loadToolParameters(toolPath);
    
    // Handle execute button click
    executeBtn.addEventListener('click', () => {
        if (appState.isExecuting) return;
        
        // Collect parameters
        const params = collectParameters();
        
        // Execute the tool
        executeTool(toolPath, params);
    });
    
    // Handle reset button click
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            resetParameters();
        });
    }
    
    // Copy output button
    const copyOutputBtn = document.getElementById('copy-output');
    if (copyOutputBtn && outputContainer) {
        copyOutputBtn.addEventListener('click', () => {
            copyToClipboard(outputContainer.textContent, copyOutputBtn);
        });
    }
}

/**
 * Load tool parameters from the server
 */
function loadToolParameters(toolPath) {
    const paramContainer = document.getElementById('param-cards');
    if (!paramContainer) return;
    
    // Show loading indicator
    paramContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-accent" role="status">
                <span class="visually-hidden">Loading parameters...</span>
            </div>
            <p class="mt-3">Loading parameters...</p>
        </div>
    `;
    
    // Fetch parameters from server
    fetch(`/parameters/${toolPath}`)
        .then(response => response.json())
        .then(data => {
            if (data.error || !data.parameters || data.parameters.length === 0) {
                paramContainer.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        ${data.error || 'No configurable parameters found for this tool.'}
                    </div>
                    <p class="text-muted">You can execute the tool with default settings.</p>
                `;
                return;
            }
            
            // Generate parameter cards
            let paramHtml = '';
            data.parameters.forEach((param, index) => {
                paramHtml += generateParameterCard(param, index);
            });
            
            // Update container
            paramContainer.innerHTML = paramHtml;
            
            // Initialize parameter interactivity
            initParameterCards();
        })
        .catch(error => {
            console.error('Error loading parameters:', error);
            paramContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading parameters: ${error.message}
                </div>
                <p class="text-muted">You can still try to execute the tool with default settings.</p>
            `;
        });
}

/**
 * Generate HTML for a parameter card
 */
function generateParameterCard(param, index) {
    const paramId = `param-${param.clean_name}`;
    const isFlag = param.type === 'bool' || param.default === 'True' || param.default === 'False';
    const isRequired = param.required || false;
    
    return `
        <div class="card parameter-card mb-3" data-param-name="${param.name}">
            <div class="card-header d-flex justify-content-between align-items-center" 
                 data-bs-toggle="collapse" data-bs-target="#${paramId}-collapse" aria-expanded="${index === 0 ? 'true' : 'false'}">
                <div>
                    <span class="fw-bold">${param.name}</span>
                    ${isRequired ? '<span class="badge bg-danger ms-2">Required</span>' : ''}
                </div>
                <i class="fas fa-chevron-down"></i>
            </div>
            <div class="collapse ${index === 0 ? 'show' : ''}" id="${paramId}-collapse">
                <div class="card-body">
                    <p class="card-text text-muted">${param.help || 'No description available.'}</p>
                    <div class="mb-3">
                        ${generateParameterInput(param, paramId)}
                    </div>
                    <div class="text-muted small">
                        <span class="me-2">Type: <code>${param.type}</code></span>
                        ${param.default ? `<span>Default: <code>${param.default}</code></span>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generate input element for a parameter
 */
function generateParameterInput(param, paramId) {
    const isFlag = param.type === 'bool' || param.default === 'True' || param.default === 'False';
    
    if (isFlag) {
        // Boolean flag
        const isChecked = param.default === 'True';
        return `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="${paramId}" 
                       ${isChecked ? 'checked' : ''}>
                <label class="form-check-label" for="${paramId}">
                    Enable this option
                </label>
            </div>
        `;
    } else if (param.choices && param.choices.length > 0) {
        // Select from choices
        let options = '';
        param.choices.forEach(choice => {
            const isSelected = choice === param.default;
            options += `<option value="${choice}" ${isSelected ? 'selected' : ''}>${choice}</option>`;
        });
        
        return `
            <label for="${paramId}" class="form-label">Value:</label>
            <select class="form-select" id="${paramId}">
                ${options}
            </select>
        `;
    } else {
        // Text/Number input
        return `
            <label for="${paramId}" class="form-label">Value:</label>
            <input type="${param.type === 'int' || param.type === 'float' ? 'number' : 'text'}" 
                   class="form-control" id="${paramId}" 
                   value="${param.default || ''}" 
                   placeholder="Enter value...">
        `;
    }
}

/**
 * Initialize parameter card interactivity
 */
function initParameterCards() {
    // Add animation to parameter card headers
    document.querySelectorAll('.parameter-card .card-header').forEach(header => {
        header.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const isCollapsed = this.getAttribute('aria-expanded') === 'false';
            
            if (icon) {
                // Animate icon rotation
                icon.style.transition = 'transform 0.3s';
                icon.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    });
}

/**
 * Collect parameter values from form
 */
function collectParameters() {
    const params = {};
    
    document.querySelectorAll('.parameter-card').forEach(card => {
        const paramName = card.getAttribute('data-param-name');
        const inputElement = card.querySelector('input, select');
        
        if (!inputElement) return;
        
        if (inputElement.type === 'checkbox') {
            params[paramName] = inputElement.checked;
        } else if (inputElement.value.trim()) {
            params[paramName] = inputElement.value.trim();
        }
    });
    
    return params;
}

/**
 * Reset parameters to default values
 */
function resetParameters() {
    document.querySelectorAll('.parameter-card').forEach(card => {
        const paramHeader = card.querySelector('.card-header');
        const paramDefault = paramHeader.nextElementSibling.querySelector('.small code:last-child')?.textContent;
        
        const inputElement = card.querySelector('input, select');
        if (!inputElement) return;
        
        if (inputElement.type === 'checkbox') {
            inputElement.checked = paramDefault === 'True';
        } else {
            inputElement.value = paramDefault?.replace(/^'|'$/g, '') || '';
        }
    });
    
    // Show notification
    showNotification('Parameters reset to default values', 'info');
}

/**
 * Execute tool with parameters
 */
function executeTool(toolPath, params) {
    const executeBtn = document.getElementById('execute-button');
    const executeStatus = document.getElementById('execute-status');
    const outputContainer = document.getElementById('output-container');
    
    if (!executeBtn || !outputContainer) return;
    
    // Set executing state
    appState.isExecuting = true;
    
    // Update UI
    executeBtn.disabled = true;
    executeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Executing...';
    
    if (executeStatus) {
        executeStatus.className = 'alert alert-info';
        executeStatus.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Executing tool...';
        executeStatus.style.display = 'block';
    }
    
    // Show loading animation in output container
    outputContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-accent" role="status"></div>
            <p class="mt-3">Executing tool, please wait...</p>
        </div>
    `;
    
    // Execute the tool
    fetch('/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tool_path: toolPath,
            params: params
        })
    })
    .then(response => response.json())
    .then(result => {
        // Store execution result
        appState.lastExecutionResult = result;
        
        // Add to execution history
        addToExecutionHistory(toolPath, params, result);
        
        // Display results
        displayExecutionResult(result, outputContainer, executeStatus);
    })
    .catch(error => {
        console.error('Error executing tool:', error);
        
        // Show error message
        outputContainer.innerHTML = `
            <div class="error p-3">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error executing tool: ${error.message}
            </div>
        `;
        
        if (executeStatus) {
            executeStatus.className = 'alert alert-danger';
            executeStatus.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                Error: ${error.message}
            `;
        }
    })
    .finally(() => {
        // Reset executing state
        appState.isExecuting = false;
        
        // Reset button
        executeBtn.disabled = false;
        executeBtn.innerHTML = '<i class="fas fa-play me-2"></i>Execute Tool';
    });
}

/**
 * Display execution result in the output container
 */
function displayExecutionResult(result, outputContainer, executeStatus) {
    let outputHtml = '';
    
    // Add command if available
    if (result.cmd) {
        outputHtml += `<div class="command">$ ${escapeHtml(result.cmd)}</div>\n\n`;
    }
    
    // Add stdout if available
    if (result.stdout) {
        outputHtml += escapeHtml(result.stdout);
    }
    
    // Add stderr if available
    if (result.stderr) {
        outputHtml += `\n\n<div class="error">${escapeHtml(result.stderr)}</div>`;
    }
    
    // If no output, show message
    if (!result.stdout && !result.stderr) {
        outputHtml += '<div class="text-muted">No output generated.</div>';
    }
    
    // Update output container
    outputContainer.innerHTML = outputHtml;
    
    // Scroll to bottom of output
    outputContainer.scrollTop = outputContainer.scrollHeight;
    
    // Update status
    if (executeStatus) {
        if (result.success) {
            executeStatus.className = 'alert alert-success';
            executeStatus.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                Tool executed successfully in ${result.execution_time.toFixed(2)} seconds.
            `;
        } else {
            executeStatus.className = 'alert alert-danger';
            executeStatus.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                Tool execution failed: ${result.error || 'Unknown error'}
            `;
        }
    }
    
    // Show notification
    showNotification(
        result.success ? 'Tool executed successfully' : 'Tool execution failed',
        result.success ? 'success' : 'danger'
    );
}

/**
 * Add execution to history
 */
function addToExecutionHistory(toolPath, params, result) {
    // Create history entry
    const historyEntry = {
        toolPath: toolPath,
        params: params,
        result: {
            success: result.success,
            execution_time: result.execution_time,
            timestamp: result.timestamp || new Date().toISOString()
        },
        timestamp: new Date().toISOString()
    };
    
    // Add to history
    appState.executionHistory.unshift(historyEntry);
    
    // Limit history size
    if (appState.executionHistory.length > 20) {
        appState.executionHistory.pop();
    }
    
    // Save to localStorage
    localStorage.setItem('executionHistory', JSON.stringify(appState.executionHistory));
}

/**
 * Load documentation for a tool
 */
function loadDocumentation() {
    const docContainer = document.getElementById('doc-container');
    const toolPath = document.querySelector('[data-tool-path]')?.getAttribute('data-tool-path');
    
    if (!docContainer || !toolPath) return;
    
    // Show loading indicator
    docContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-accent" role="status">
                <span class="visually-hidden">Loading documentation...</span>
            </div>
            <p class="mt-3">Loading documentation...</p>
        </div>
    `;
    
    // Fetch documentation
    fetch(`/docs/${toolPath}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                docContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error}
                    </div>
                    <p class="text-muted">No documentation available for this tool.</p>
                `;
                return;
            }
            
            // Generate documentation HTML
            let docHtml = `<div class="documentation-loaded">`;
            
            // Add title
            docHtml += `<h2 class="text-gradient">${data.title || 'Documentation'}</h2>`;
            
            // Add summary
            if (data.summary) {
                docHtml += `<p class="lead">${data.summary}</p>`;
            }
            
            // Add sections
            const sections = data.key_sections || {};
            for (const [title, content] of Object.entries(sections)) {
                if (content && content.trim()) {
                    docHtml += `
                        <div class="doc-section mb-4">
                            <h3 class="mb-3"><i class="fas fa-book text-accent me-2"></i>${title}</h3>
                            <div class="doc-content">${formatDocContent(content)}</div>
                        </div>
                    `;
                }
            }
            
            // Add examples if available
            if (data.examples && data.examples.length > 0) {
                docHtml += `
                    <div class="doc-section mb-4">
                        <h3 class="mb-3"><i class="fas fa-code text-accent me-2"></i>Examples</h3>
                        <div class="doc-content">
                `;
                
                data.examples.forEach(example => {
                    docHtml += `
                        <div class="example-block p-3 mb-3 bg-elevated rounded">
                            <pre><code class="language-bash">${escapeHtml(example)}</code></pre>
                        </div>
                    `;
                });
                
                docHtml += `</div></div>`;
            }
            
            // Close documentation div
            docHtml += `</div>`;
            
            // Update container
            docContainer.innerHTML = docHtml;
            
            // Apply syntax highlighting
            if (window.hljs) {
                document.querySelectorAll('.documentation-loaded pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
            }
            
            // Add copy buttons to code blocks
            document.querySelectorAll('.documentation-loaded pre').forEach(block => {
                if (!block.querySelector('.copy-btn')) {
                    const copyBtn = document.createElement('button');
                    copyBtn.className = 'copy-btn';
                    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                    
                    copyBtn.addEventListener('click', () => {
                        const code = block.querySelector('code').textContent;
                        copyToClipboard(code, copyBtn);
                    });
                    
                    block.appendChild(copyBtn);
                }
            });
        })
        .catch(error => {
            console.error('Error loading documentation:', error);
            docContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading documentation: ${error.message}
                </div>
            `;
        });
}

/**
 * Format documentation content with Markdown-like syntax
 */
function formatDocContent(content) {
    if (!content) return '';
    
    // Escape HTML characters
    content = escapeHtml(content);
    
    // Format code blocks with ```
    content = content.replace(/```([a-z]*)\n([\s\S]*?)\n```/g, (match, language, code) => {
        return `<pre><code class="language-${language || 'bash'}">${code.trim()}</code></pre>`;
    });
    
    // Format inline code with `
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert lines to paragraphs
    const lines = content.split('\n');
    let formatted = '';
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line === '') {
            if (inList) {
                formatted += '</ul>';
                inList = false;
            }
            formatted += '<br>';
            continue;
        }
        
        // Handle bullet points
        if (line.match(/^[-*•]\s+/)) {
            if (!inList) {
                formatted += '<ul class="mb-3">';
                inList = true;
            }
            formatted += `<li>${line.replace(/^[-*•]\s+/, '')}</li>`;
        } 
        // Handle numbered lists
        else if (line.match(/^\d+\.\s+/)) {
            if (!inList) {
                formatted += '<ol class="mb-3">';
                inList = true;
            }
            formatted += `<li>${line.replace(/^\d+\.\s+/, '')}</li>`;
        }
        // Regular line
        else {
            if (inList) {
                formatted += inList === 'ul' ? '</ul>' : '</ol>';
                inList = false;
            }
            formatted += `<p>${line}</p>`;
        }
    }
    
    if (inList) {
        formatted += inList === 'ul' ? '</ul>' : '</ol>';
    }
    
    return formatted;
}

/**
 * Load source code for a tool
 */
function loadSourceCode() {
    const sourceContainer = document.getElementById('source-container');
    const toolPath = document.querySelector('[data-tool-path]')?.getAttribute('data-tool-path');
    
    if (!sourceContainer || !toolPath) return;
    
    // Show loading indicator
    sourceContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-accent" role="status">
                <span class="visually-hidden">Loading source code...</span>
            </div>
            <p class="mt-3">Loading source code...</p>
        </div>
    `;
    
    // Fetch source code
    fetch(`/source/${toolPath}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                sourceContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error}
                    </div>
                `;
                return;
            }
            
            // Generate source code HTML
            const sourceHtml = `
                <div class="source-loaded">
                    <pre class="source-code"><code class="language-python">${escapeHtml(data.source)}</code></pre>
                </div>
            `;
            
            // Update container
            sourceContainer.innerHTML = sourceHtml;
            
            // Apply syntax highlighting
            if (window.hljs) {
                document.querySelectorAll('.source-loaded pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
            }
            
            // Add line numbers
            addLineNumbers();
        })
        .catch(error => {
            console.error('Error loading source code:', error);
            sourceContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading source code: ${error.message}
                </div>
            `;
        });
    
    // Add line numbers to source code
    function addLineNumbers() {
        const sourceCode = document.querySelector('.source-code');
        if (!sourceCode) return;
        
        const codeLines = sourceCode.querySelector('code').innerHTML.split('\n');
        let numberedCode = '';
        
        for (let i = 0; i < codeLines.length; i++) {
            numberedCode += `<span class="line-number">${i + 1}</span>${codeLines[i]}\n`;
        }
        
        sourceCode.querySelector('code').innerHTML = numberedCode;
        sourceCode.classList.add('line-numbers');
    }
}

/**
 * Setup documentation viewer tabs and navigation
 */
function setupDocViewer() {
    // Handle tab navigation for documentation
    document.querySelectorAll('.doc-nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get target section
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                // Scroll to section
                targetSection.scrollIntoView({ behavior: 'smooth' });
                
                // Update active tab
                document.querySelectorAll('.doc-nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
}

/**
 * Initialize dynamic counters with animation
 */
function initCounters() {
    // Find counter elements
    const counterElements = document.querySelectorAll('.counter');
    
    // Setup Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counterElement = entry.target;
                const targetValue = parseInt(counterElement.getAttribute('data-target'), 10);
                animateCounter(counterElement, targetValue);
                observer.unobserve(counterElement);
            }
        });
    }, { threshold: 0.5 });
    
    // Observe counter elements
    counterElements.forEach(counter => {
        observer.observe(counter);
    });
    
    // Animate counter from 0 to target
    function animateCounter(element, target, duration = 2000) {
        let start = 0;
        const increment = target / (duration / 16);
        const timer = setInterval(() => {
            start += increment;
            element.textContent = Math.floor(start);
            if (start >= target) {
                element.textContent = target;
                clearInterval(timer);
            }
        }, 16);
    }
}

/**
 * Setup category filters for tool lists
 */
function setupCategoryFilters() {
    const filterButtons = document.querySelectorAll('.category-filter-btn');
    const toolItems = document.querySelectorAll('[data-category]');
    
    if (filterButtons.length === 0 || toolItems.length === 0) return;
    
    // Add click handler to filter buttons
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Get selected category
            const category = button.getAttribute('data-filter');
            appState.categoryFilter = category;
            
            // Filter tools
            filterToolsByCategory(category);
        });
    });
    
    // Filter tools by category
    function filterToolsByCategory(category) {
        toolItems.forEach(item => {
            if (category === 'all' || item.getAttribute('data-category') === category) {
                item.style.display = '';
                item.classList.add('animate-fadeIn');
            } else {
                item.style.display = 'none';
                item.classList.remove('animate-fadeIn');
            }
        });
    }
}

/**
 * Setup collapsible sections
 */
function setupCollapsibles() {
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const icon = this.querySelector('.collapse-icon');
            
            if (content.style.maxHeight) {
                // Collapse
                content.style.maxHeight = null;
                if (icon) icon.className = 'fas fa-chevron-down collapse-icon';
            } else {
                // Expand
                content.style.maxHeight = content.scrollHeight + 'px';
                if (icon) icon.className = 'fas fa-chevron-up collapse-icon';
            }
        });
    });
}

/**
 * Setup loading indicator
 */
function setupLoadingIndicator() {
    // Show loading indicator when fetching data
    if (window.fetch) {
        const originalFetch = window.fetch;
        
        window.fetch = function() {
            // Check if this is a data request (e.g. /api/, /execute, etc.)
            const url = arguments[0];
            if (typeof url === 'string' && (url.includes('/api/') || url.includes('/execute') || url.includes('/source/') || url.includes('/docs/'))) {
                // Show loading indicator
                showLoadingOverlay();
            }
            
            const fetchPromise = originalFetch.apply(this, arguments);
            
            fetchPromise.finally(() => {
                // Hide loading indicator
                hideLoadingOverlay();
            });
            
            return fetchPromise;
        };
    }
}

/**
 * Show loading overlay
 */
function showLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('active');
    }
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('active');
    }
}

/**
 * Enable smooth scrolling
 */
function enableSmoothScroll() {
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip non-scroll links
            if (href === '#' || href.startsWith('#/') || href.includes('collapse')) return;
            
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL hash without scrolling
                history.pushState(null, null, targetId);
            }
        });
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast-notification toast-${type}`;
    notification.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${type === 'info' ? 'info-circle' : (type === 'success' ? 'check-circle' : 'exclamation-circle')}"></i>
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close">×</button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto-hide after delay
    const timeout = setTimeout(() => {
        hideNotification(notification);
    }, config.notificationDuration);
    
    // Handle close button
    const closeButton = notification.querySelector('.toast-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            clearTimeout(timeout);
            hideNotification(notification);
        });
    }
    
    // Hide notification
    function hideNotification(element) {
        element.classList.remove('show');
        setTimeout(() => {
            element.remove();
        }, 300);
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text, button = null) {
    // Create a temporary textarea
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    
    // Select the text
    textarea.select();
    document.execCommand('copy');
    
    // Remove the textarea
    document.body.removeChild(textarea);
    
    // Update button state if provided
    if (button) {
        const originalHtml = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('success');
        
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.classList.remove('success');
        }, 2000);
    }
    
    // Show notification
    showNotification('Copied to clipboard', 'success');
    
    // Return true to indicate success
    return true;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + units[i];
}

/**
 * Get category icon based on category name
 */
function getCategoryIcon(category) {
    const icons = {
        'automation': 'robot',
        'creative': 'paint-brush',
        'data_processing': 'database',
        'dev_tools': 'code',
        'education': 'graduation-cap',
        'file_management': 'folder',
        'finance': 'chart-line',
        'gaming': 'gamepad',
        'hardware_iot': 'microchip',
        'multimedia': 'photo-video',
        'networking': 'network-wired',
        'security': 'shield-alt',
        'system_tools': 'desktop',
        'utility': 'tools',
        'web_api_tools': 'globe'
    };
    
    return icons[category] || 'puzzle-piece';
}

/**
 * Get tool icon based on tool category
 */
function getToolIcon(category) {
    return getCategoryIcon(typeof category === 'string' ? category : (category.category || 'utility'));
}

/**
 * Format date to relative time (e.g. "2 days ago")
 */
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // Difference in seconds
    
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' minutes ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
    if (diff < 2592000) return Math.floor(diff / 86400) + ' days ago';
    if (diff < 31536000) return Math.floor(diff / 2592000) + ' months ago';
    
    return Math.floor(diff / 31536000) + ' years ago';
}
