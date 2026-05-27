// Autocomplete functionality for loan form
class Autocomplete {
    constructor(input, options = {}) {
        this.input = input;
        this.dropdown = null;
        this.hiddenField = null;
        this.searchTimeout = null;
        this.currentRequest = null;
        this.selectedIndex = -1;
        
        this.options = {
            minLength: 2,
            delay: 500,
            maxResults: 10,
            noResultsText: 'Nenhum resultado encontrado',
            loadingText: 'Buscando...',
            ...options
        };
        
        this.init();
    }
    
    init() {
        // Find the dropdown and hidden field
        const wrapper = this.input.closest('.autocomplete-wrapper');
        if (!wrapper) return;
        
        this.dropdown = wrapper.querySelector('.autocomplete-dropdown');
        
        const target = this.input.dataset.target;
        if (target) {
            this.hiddenField = wrapper.querySelector(`#id_${target}`);
        }
        
        if (!this.dropdown || !this.hiddenField) return;
        
        this.bindEvents();
    }
    
    bindEvents() {
        // Input events
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('focus', () => this.handleFocus());
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Dropdown events
        this.dropdown.addEventListener('mousedown', (e) => {
            // Prevent blur event when clicking on dropdown
            e.preventDefault();
        });
        
        this.dropdown.addEventListener('click', (e) => {
            const item = e.target.closest('.autocomplete-item');
            if (item) {
                this.selectItem(item);
            }
        });
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        // Clear selection if input changes
        if (this.hiddenField.value) {
            this.hiddenField.value = '';
            this.input.classList.remove('has-selection');
        }
        
        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Hide dropdown if query is too short
        if (query.length < this.options.minLength) {
            this.hideDropdown();
            return;
        }
        
        // Set loading state
        this.input.classList.add('loading');
        
        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.search(query);
        }, this.options.delay);
    }
    
    handleFocus() {
        if (this.dropdown.children.length > 0) {
            this.showDropdown();
        }
    }
    
    handleBlur(e) {
        // Use timeout to allow dropdown clicks
        setTimeout(() => {
            this.hideDropdown();
        }, 200);
    }
    
    handleKeydown(e) {
        if (!this.dropdown.classList.contains('show')) {
            return;
        }
        
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                this.updateHighlight(items);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateHighlight(items);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    this.selectItem(items[this.selectedIndex]);
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }
    
    search(query) {
        // Cancel previous request
        if (this.currentRequest) {
            this.currentRequest.abort();
        }
        
        const url = this.input.dataset.autocompleteUrl;
        if (!url) return;
        
        // Create AbortController for this request
        const controller = new AbortController();
        this.currentRequest = controller;
        
        fetch(`${url}?q=${encodeURIComponent(query)}`, {
            signal: controller.signal,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            this.input.classList.remove('loading');
            this.renderResults(data.results || []);
        })
        .catch(error => {
            if (error.name !== 'AbortError') {
                console.error('Autocomplete search error:', error);
                this.input.classList.remove('loading');
                this.renderError();
            }
        });
    }
    
    renderResults(results) {
        this.dropdown.innerHTML = '';
        this.selectedIndex = -1;
        
        if (results.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'autocomplete-no-results';
            noResults.textContent = this.options.noResultsText;
            this.dropdown.appendChild(noResults);
        } else {
            results.slice(0, this.options.maxResults).forEach(item => {
                const element = document.createElement('div');
                element.className = 'autocomplete-item';
                
                // Add special styling for ineligible users
                if (item.is_eligible === false || item.is_eligible === 'false') {
                    element.classList.add('autocomplete-item-disabled');
                }
                
                element.textContent = item.text;
                element.dataset.id = item.id;
                element.dataset.value = item.text;
                
                // Store additional data
                Object.keys(item).forEach(key => {
                    if (key !== 'id' && key !== 'text') {
                        element.dataset[key] = item[key];
                    }
                });
                
                this.dropdown.appendChild(element);
            });
        }
        
        this.showDropdown();
    }
    
    renderError() {
        this.dropdown.innerHTML = '';
        const error = document.createElement('div');
        error.className = 'autocomplete-no-results';
        error.textContent = 'Erro ao buscar resultados';
        this.dropdown.appendChild(error);
        this.showDropdown();
    }
    
    selectItem(item) {
        const id = item.dataset.id;
        const value = item.dataset.value;
        
        if (id && value) {
            this.input.value = value;
            this.hiddenField.value = id;
            this.input.classList.add('has-selection');
            this.hideDropdown();
            
            // Trigger change event for validation
            this.input.dispatchEvent(new Event('change', { bubbles: true }));
            this.hiddenField.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    
    updateHighlight(items) {
        items.forEach((item, index) => {
            item.classList.toggle('highlighted', index === this.selectedIndex);
        });
        
        // Scroll highlighted item into view
        if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
            items[this.selectedIndex].scrollIntoView({
                block: 'nearest'
            });
        }
    }
    
    showDropdown() {
        this.dropdown.classList.add('show');
    }
    
    hideDropdown() {
        this.dropdown.classList.remove('show');
        this.selectedIndex = -1;
    }
}

// Initialize autocomplete on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    const autocompleteInputs = document.querySelectorAll('.autocomplete-input');
    
    autocompleteInputs.forEach(input => {
        new Autocomplete(input);
    });
});