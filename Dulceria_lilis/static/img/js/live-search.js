// static/js/live-search.js

/**
 * 🔍 Búsqueda en tiempo real con paginación dinámica
 * Actualiza la URL y recarga los resultados sin refrescar toda la página
 */

class LiveSearch {
    constructor(inputId, formId, debounceTime = 500) {
        this.input = document.getElementById(inputId);
        this.form = document.getElementById(formId);
        this.debounceTimer = null;
        this.debounceTime = debounceTime;
        
        if (this.input && this.form) {
            this.init();
        }
    }
    
    init() {
        // Búsqueda mientras escribe (con debounce)
        this.input.addEventListener('input', () => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.submitForm();
            }, this.debounceTime);
        });
        
        // Prevenir submit normal del formulario
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });
        
        // Botón limpiar
        const clearBtn = this.form.querySelector('[data-clear-search]');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.input.value = '';
                this.submitForm();
            });
        }
    }
    
    submitForm() {
        // Obtener todos los parámetros del formulario
        const formData = new FormData(this.form);
        const params = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
             params.append(key, value);   // Enviar incluso vacío
        }
        
        // Resetear a página 1 cuando cambia la búsqueda
        params.delete('page');
        params.set('page', '1');
        params.set('live', '1');
        
        // Actualizar URL y recargar
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.location.href = newUrl;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Para Productos
    if (document.getElementById('liveSearchProductos')) {
        new LiveSearch('liveSearchProductos', 'formFiltrosProductos', 400);
    }
    
    // Para Proveedores
    if (document.getElementById('liveSearchProveedores')) {
        new LiveSearch('liveSearchProveedores', 'formFiltrosProveedores', 400);
    }
    
    // Para Inventario
    if (document.getElementById('liveSearchInventario')) {
        new LiveSearch('liveSearchInventario', 'formFiltrosInventario', 400);
    }
});