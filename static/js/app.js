/**
 * Sistema Distribuidor - Main JavaScript Application
 * Handles client-side functionality and UI interactions
 */

// Global application object
window.DistribuidorApp = {
    // Configuration
    config: {
        dateFormat: 'DD/MM/YYYY',
        timeFormat: 'HH:mm',
        currency: 'BRL',
        locale: 'pt-BR'
    },
    
    // Utility functions
    utils: {},
    
    // Component modules
    components: {},
    
    // Initialize application
    init: function() {
        this.utils.init();
        this.components.init();
        this.bindGlobalEvents();
        this.initTooltips();
        this.initPopovers();
    }
};

// Utility functions
DistribuidorApp.utils = {
    init: function() {
        // Initialize utility functions
    },
    
    // Format currency values
    formatCurrency: function(value) {
        if (isNaN(value) || value === null || value === undefined) {
            return 'R$ 0,00';
        }
        
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },
    
    // Format numbers
    formatNumber: function(value, decimals = 2) {
        if (isNaN(value) || value === null || value === undefined) {
            return '0';
        }
        
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },
    
    // Format dates
    formatDate: function(date, format = 'DD/MM/YYYY') {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        switch (format) {
            case 'DD/MM/YYYY':
                return `${day}/${month}/${year}`;
            case 'DD/MM/YYYY HH:mm':
                return `${day}/${month}/${year} ${hours}:${minutes}`;
            case 'HH:mm':
                return `${hours}:${minutes}`;
            default:
                return `${day}/${month}/${year}`;
        }
    },
    
    // Parse currency input
    parseCurrency: function(value) {
        if (typeof value === 'number') return value;
        if (!value) return 0;
        
        // Remove currency symbols and convert to number
        const cleaned = value.toString()
            .replace(/[^\d,.-]/g, '')
            .replace(',', '.');
        
        return parseFloat(cleaned) || 0;
    },
    
    // Show loading overlay
    showLoading: function() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'globalLoadingOverlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    },
    
    // Hide loading overlay
    hideLoading: function() {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'info', duration = 5000) {
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 350px;
            `;
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.style.cssText = 'margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    },
    
    // Confirm dialog
    confirm: function(message, callback) {
        if (window.confirm(message)) {
            callback();
        }
    },
    
    // Debounce function
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }
};

// Component modules
DistribuidorApp.components = {
    init: function() {
        this.initFormValidation();
        this.initDataTables();
        this.initCharts();
        this.initSearch();
        this.initPrint();
        this.initWhatsApp();
        this.initStockAlerts();
        this.initKeyboardShortcuts();
    },
    
    // Form validation enhancements
    initFormValidation: function() {
        // Add custom validation styles
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Focus on first invalid field
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
                form.classList.add('was-validated');
            });
        });
        
        // Real-time validation for currency inputs
        const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
        currencyInputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value) {
                    const value = DistribuidorApp.utils.parseCurrency(this.value);
                    this.value = value.toFixed(2);
                }
            });
        });
    },
    
    // Enhanced data tables
    initDataTables: function() {
        // Add sorting functionality to tables
        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            // Add click-to-sort on headers (basic implementation)
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                if (header.textContent.trim() && !header.querySelector('.no-sort')) {
                    header.style.cursor = 'pointer';
                    header.title = 'Clique para ordenar';
                    
                    header.addEventListener('click', function() {
                        // Basic client-side sorting implementation
                        // This is a simplified version - in production you might want a more robust solution
                        DistribuidorApp.components.sortTable(table, index);
                    });
                }
            });
        });
        
        // Highlight rows on hover
        const tableRows = document.querySelectorAll('.table tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('click', function() {
                // Remove previous selection
                const selected = row.parentNode.querySelector('.table-active');
                if (selected) {
                    selected.classList.remove('table-active');
                }
                // Add selection to current row
                row.classList.add('table-active');
            });
        });
    },
    
    // Chart enhancements
    initCharts: function() {
        // Global Chart.js defaults
        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = 'inherit';
            Chart.defaults.color = 'rgba(255, 255, 255, 0.8)';
            Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
            Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        }
    },
    
    // Search enhancements
    initSearch: function() {
        const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
        searchInputs.forEach(input => {
            // Add search icon
            if (!input.parentNode.querySelector('.search-icon')) {
                const icon = document.createElement('i');
                icon.className = 'fas fa-search search-icon';
                icon.style.cssText = `
                    position: absolute;
                    right: 10px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #6c757d;
                    pointer-events: none;
                `;
                input.parentNode.style.position = 'relative';
                input.parentNode.appendChild(icon);
                input.style.paddingRight = '35px';
            }
            
            // Add real-time search with debounce
            const debouncedSearch = DistribuidorApp.utils.debounce(function() {
                // Auto-submit search form after typing stops
                const form = input.closest('form');
                if (form && input.value.length >= 2) {
                    // Only auto-submit if it's a GET form (search)
                    if (form.method.toLowerCase() === 'get' || !form.method) {
                        form.submit();
                    }
                }
            }, 800);
            
            input.addEventListener('input', debouncedSearch);
        });
    },
    
    // Print functionality
    initPrint: function() {
        const printButtons = document.querySelectorAll('[data-print]');
        printButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const url = this.href || this.getAttribute('data-print');
                
                if (url) {
                    // Open print window
                    const printWindow = window.open(url + '?auto_print=true', '_blank', 
                        'width=800,height=600,scrollbars=yes,resizable=yes');
                    
                    if (printWindow) {
                        printWindow.focus();
                    } else {
                        DistribuidorApp.utils.showToast(
                            'Pop-ups bloqueados. Por favor, permita pop-ups para impressão.',
                            'warning'
                        );
                    }
                }
            });
        });
    },
    
    // WhatsApp integration
    initWhatsApp: function() {
        const whatsappButtons = document.querySelectorAll('[href*="whatsapp"], .btn-whatsapp');
        whatsappButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                // Add loading state
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Abrindo WhatsApp...';
                this.disabled = true;
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.disabled = false;
                }, 2000);
            });
        });
    },
    
    // Stock alerts
    initStockAlerts: function() {
        // Check for low stock indicators
        const stockBadges = document.querySelectorAll('.badge[class*="danger"], .stock-critical');
        if (stockBadges.length > 0) {
            // Show notification about low stock
            setTimeout(() => {
                DistribuidorApp.utils.showToast(
                    `Atenção: ${stockBadges.length} produto(s) com estoque baixo!`,
                    'warning',
                    8000
                );
            }, 1000);
        }
    },
    
    // Keyboard shortcuts
    initKeyboardShortcuts: function() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + specific keys
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'n':
                        e.preventDefault();
                        // Find "New" button and click it
                        const newButton = document.querySelector('a[href*="/new"], .btn-primary[href*="/new"]');
                        if (newButton) newButton.click();
                        break;
                    
                    case 's':
                        e.preventDefault();
                        // Find and submit the main form
                        const mainForm = document.querySelector('form');
                        if (mainForm && !mainForm.querySelector('input[type="search"]')) {
                            mainForm.submit();
                        }
                        break;
                    
                    case '/':
                        e.preventDefault();
                        // Focus on search input
                        const searchInput = document.querySelector('input[type="search"], input[name="search"]');
                        if (searchInput) {
                            searchInput.focus();
                            searchInput.select();
                        }
                        break;
                }
            }
            
            // Escape key
            if (e.key === 'Escape') {
                // Close modals
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const bootstrapModal = bootstrap.Modal.getInstance(openModal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                }
                
                // Clear search
                const searchInput = document.querySelector('input[type="search"]:focus, input[name="search"]:focus');
                if (searchInput) {
                    searchInput.value = '';
                    searchInput.blur();
                }
            }
        });
    },
    
    // Table sorting helper
    sortTable: function(table, columnIndex) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const header = table.querySelectorAll('th')[columnIndex];
        
        // Determine sort direction
        const isAscending = !header.classList.contains('sort-asc');
        
        // Remove existing sort classes
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add sort class to current header
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();
            
            // Try to parse as numbers for numeric sorting
            const aNum = parseFloat(aText.replace(/[^\d.-]/g, ''));
            const bNum = parseFloat(bText.replace(/[^\d.-]/g, ''));
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            } else {
                return isAscending 
                    ? aText.localeCompare(bText, 'pt-BR')
                    : bText.localeCompare(aText, 'pt-BR');
            }
        });
        
        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));
    }
};

// Global event handlers
DistribuidorApp.bindGlobalEvents = function() {
    // Handle form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM') {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton && !form.hasAttribute('data-no-loading')) {
                const originalText = submitButton.innerHTML || submitButton.value;
                
                if (submitButton.tagName === 'BUTTON') {
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
                } else {
                    submitButton.value = 'Processando...';
                }
                
                submitButton.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    if (submitButton.tagName === 'BUTTON') {
                        submitButton.innerHTML = originalText;
                    } else {
                        submitButton.value = originalText;
                    }
                    submitButton.disabled = false;
                }, 5000);
            }
        }
    });
    
    // Handle file upload preview
    document.addEventListener('change', function(e) {
        if (e.target.type === 'file' && e.target.accept && e.target.accept.includes('image')) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.getElementById(e.target.id + '_preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = e.target.id + '_preview';
                        preview.style.cssText = 'max-width: 200px; max-height: 200px; margin-top: 10px; border-radius: 5px;';
                        e.target.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        }
    });
    
    // Auto-focus on modal open
    document.addEventListener('shown.bs.modal', function(e) {
        const modal = e.target;
        const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    });
    
    // Confirm delete actions
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm]') || e.target.closest('[data-confirm]')) {
            const element = e.target.matches('[data-confirm]') ? e.target : e.target.closest('[data-confirm]');
            const message = element.getAttribute('data-confirm') || 'Tem certeza que deseja continuar?';
            
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        }
    });
};

// Initialize tooltips and popovers
DistribuidorApp.initTooltips = function() {
    // Initialize Bootstrap tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
};

DistribuidorApp.initPopovers = function() {
    // Initialize Bootstrap popovers
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DistribuidorApp.init();
    
    // Show welcome message for new sessions
    const isNewSession = !sessionStorage.getItem('app_initialized');
    if (isNewSession) {
        sessionStorage.setItem('app_initialized', 'true');
        setTimeout(() => {
            DistribuidorApp.utils.showToast(
                'Sistema carregado com sucesso! Use Ctrl+/ para buscar.',
                'success',
                3000
            );
        }, 1000);
    }
});

// Handle page unload
window.addEventListener('beforeunload', function(e) {
    // Check for unsaved forms, but exclude simple action forms (like status updates)
    const forms = document.querySelectorAll('form.was-validated:not([data-no-warning]):not([method="POST"][action*="/status"])');
    if (forms.length > 0) {
        // Only warn if form has actual input fields that could contain unsaved data
        let hasInputs = false;
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input:not([type="hidden"]), textarea, select');
            if (inputs.length > 1) { // More than just one field (usually the status select)
                hasInputs = true;
            }
        });
        
        if (hasInputs) {
            const message = 'Você tem alterações não salvas. Deseja realmente sair?';
            e.returnValue = message;
            return message;
        }
    }
});

// Export for global access
window.App = DistribuidorApp;
