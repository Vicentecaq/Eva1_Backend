/**
 * Sistema de Ventas & Inventario - Dashboard JS
 * 100% Vanilla JavaScript - Cero dependencias externas.
 */

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initAlerts();
  initProductSearchAndFilter();
  initPosTerminal();
  initClientToggle();
});

/* ==========================================================================
   1. CONTROL DEL SIDEBAR EN DISPOSITIVOS MÓVILES
   ========================================================================== */
function initSidebar() {
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebar = document.getElementById('appSidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (!toggleBtn || !sidebar || !backdrop) return;

  const openSidebar = () => {
    sidebar.classList.add('show');
    backdrop.classList.add('show');
    document.body.style.overflow = 'hidden';
  };

  const closeSidebar = () => {
    sidebar.classList.remove('show');
    backdrop.classList.remove('show');
    document.body.style.overflow = '';
  };

  toggleBtn.addEventListener('click', openSidebar);
  backdrop.addEventListener('click', closeSidebar);

  // Cerrar al cambiar a pantalla grande
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768 && sidebar.classList.contains('show')) {
      closeSidebar();
    }
  });
}

/* ==========================================================================
   2. DESCARTE DE ALERTAS Y MENSAJES FLASH
   ========================================================================== */
function initAlerts() {
  const alertCloseBtns = document.querySelectorAll('.alert-close-btn');
  alertCloseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert-message');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        alert.style.transition = 'all 0.25s ease';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto descartar mensajes de éxito tras 6 segundos
  const successAlerts = document.querySelectorAll('.alert-success');
  successAlerts.forEach(alert => {
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        alert.style.transition = 'all 0.25s ease';
        setTimeout(() => alert.remove(), 250);
      }
    }, 6000);
  });
}

/* ==========================================================================
   3. BÚSQUEDA Y FILTRADO EN VIVO PARA TABLA DE PRODUCTOS
   ========================================================================== */
function initProductSearchAndFilter() {
  const searchInput = document.getElementById('productSearchInput');
  const table = document.getElementById('productsTable');
  const filterChips = document.querySelectorAll('.filter-chip[data-filter]');
  const countBadge = document.getElementById('visibleProductsCount');

  if (!table) return;

  const rows = Array.from(table.querySelectorAll('tbody tr:not(.empty-row)'));
  let currentFilter = 'all';
  let searchQuery = '';

  const applyFilters = () => {
    let visibleCount = 0;

    rows.forEach(row => {
      const name = (row.getAttribute('data-name') || '').toLowerCase();
      const code = (row.getAttribute('data-code') || '').toLowerCase();
      const stock = parseInt(row.getAttribute('data-stock') || '0', 10);

      const matchesSearch = name.includes(searchQuery) || code.includes(searchQuery);

      let matchesFilter = true;
      if (currentFilter === 'in_stock') {
        matchesFilter = stock > 5;
      } else if (currentFilter === 'low_stock') {
        matchesFilter = stock > 0 && stock <= 5;
      } else if (currentFilter === 'out_of_stock') {
        matchesFilter = stock === 0;
      }

      if (matchesSearch && matchesFilter) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    if (countBadge) {
      countBadge.textContent = `${visibleCount} producto${visibleCount === 1 ? '' : 's'}`;
    }

    // Mostrar fila vacía si no hay resultados
    let emptyRow = table.querySelector('.no-results-row');
    if (visibleCount === 0) {
      if (!emptyRow) {
        emptyRow = document.createElement('tr');
        emptyRow.className = 'no-results-row';
        emptyRow.innerHTML = `
          <td colspan="6" class="text-center py-4" style="text-align: center; padding: 32px 16px; color: var(--color-text-muted);">
            🔍 No se encontraron productos que coincidan con la búsqueda o filtro.
          </td>
        `;
        table.querySelector('tbody').appendChild(emptyRow);
      }
      emptyRow.style.display = '';
    } else if (emptyRow) {
      emptyRow.style.display = 'none';
    }
  };

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      applyFilters();
    });
  }

  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentFilter = chip.getAttribute('data-filter');
      applyFilters();
    });
  });
}

/* ==========================================================================
   4. TERMINAL PUNTO DE VENTA (REGISTRAR VENTA / POS CART)
   ========================================================================== */
function initPosTerminal() {
  const posContainer = document.getElementById('posTerminalContainer');
  if (!posContainer) return;

  const cartTableBody = document.getElementById('posCartTableBody');
  const emptyCartState = document.getElementById('emptyCartState');
  const cartTableWrapper = document.getElementById('cartTableWrapper');
  const grandTotalEl = document.getElementById('posGrandTotal');
  const subtotalEl = document.getElementById('posSubtotal');
  const itemCountEl = document.getElementById('posItemCount');
  const form = document.getElementById('posSaleForm');
  const hiddenInputsContainer = document.getElementById('posHiddenInputs');
  const catalogSearch = document.getElementById('posCatalogSearch');

  // Estado del Carrito: { [productId]: { id, name, code, price, stock, qty } }
  const cart = {};

  const formatCLP = (val) => {
    return '$ ' + Math.round(val).toLocaleString('es-CL');
  };

  const updateUI = () => {
    cartTableBody.innerHTML = '';
    hiddenInputsContainer.innerHTML = '';

    const items = Object.values(cart);
    let total = 0;
    let totalItems = 0;

    if (items.length === 0) {
      if (emptyCartState) emptyCartState.style.display = 'flex';
      if (cartTableWrapper) cartTableWrapper.style.display = 'none';
    } else {
      if (emptyCartState) emptyCartState.style.display = 'none';
      if (cartTableWrapper) cartTableWrapper.style.display = 'block';

      items.forEach(item => {
        const itemSubtotal = item.price * item.qty;
        total += itemSubtotal;
        totalItems += item.qty;

        // Fila en tabla del carrito
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <div style="font-weight: 600; color: var(--color-text-main);">${escapeHtml(item.name)}</div>
            <div style="font-size: 0.76rem; color: var(--color-text-muted); font-family: monospace;">${escapeHtml(item.code)}</div>
          </td>
          <td style="font-variant-numeric: tabular-nums; font-weight: 600;">${formatCLP(item.price)}</td>
          <td>
            <div class="qty-stepper">
              <button type="button" class="qty-btn btn-dec" data-id="${item.id}">−</button>
              <input type="text" class="qty-val" value="${item.qty}" readonly>
              <button type="button" class="qty-btn btn-inc" data-id="${item.id}" ${item.qty >= item.stock ? 'disabled style="opacity:0.4;"' : ''}>+</button>
            </div>
            <div style="font-size: 0.7rem; color: var(--color-text-muted); margin-top: 2px;">Máx: ${item.stock}</div>
          </td>
          <td style="font-weight: 700; color: var(--color-text-main); font-variant-numeric: tabular-nums;">
            ${formatCLP(itemSubtotal)}
          </td>
          <td style="text-align: center;">
            <button type="button" class="btn-sm btn-outline btn-del" data-id="${item.id}" title="Quitar producto" style="color: var(--color-danger); border-color: transparent;">
              🗑️
            </button>
          </td>
        `;
        cartTableBody.appendChild(tr);

        // Inputs ocultos que Django espera en views.py: request.POST.getlist('productos') y getlist('cantidades')
        const prodInput = document.createElement('input');
        prodInput.type = 'hidden';
        prodInput.name = 'productos';
        prodInput.value = item.id;
        hiddenInputsContainer.appendChild(prodInput);

        const cantInput = document.createElement('input');
        cantInput.type = 'hidden';
        cantInput.name = 'cantidades';
        cantInput.value = item.qty;
        hiddenInputsContainer.appendChild(cantInput);
      });
    }

    if (grandTotalEl) grandTotalEl.textContent = formatCLP(total);
    if (subtotalEl) subtotalEl.textContent = formatCLP(total);
    if (itemCountEl) itemCountEl.textContent = `${totalItems} unidad${totalItems === 1 ? '' : 'es'}`;
  };

  // Agregar al carrito desde catálogo
  document.querySelectorAll('.btn-add-pos-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const name = btn.getAttribute('data-name');
      const code = btn.getAttribute('data-code');
      const price = parseFloat(btn.getAttribute('data-price') || '0');
      const stock = parseInt(btn.getAttribute('data-stock') || '0', 10);

      if (stock <= 0) return;

      if (cart[id]) {
        if (cart[id].qty < stock) {
          cart[id].qty++;
        }
      } else {
        cart[id] = { id, name, code, price, stock, qty: 1 };
      }

      updateUI();
    });
  });

  // Event delegation para Stepper y Eliminar del carrito
  cartTableBody.addEventListener('click', (e) => {
    const incBtn = e.target.closest('.btn-inc');
    const decBtn = e.target.closest('.btn-dec');
    const delBtn = e.target.closest('.btn-del');

    if (incBtn) {
      const id = incBtn.getAttribute('data-id');
      if (cart[id] && cart[id].qty < cart[id].stock) {
        cart[id].qty++;
        updateUI();
      }
    } else if (decBtn) {
      const id = decBtn.getAttribute('data-id');
      if (cart[id]) {
        if (cart[id].qty > 1) {
          cart[id].qty--;
        } else {
          delete cart[id];
        }
        updateUI();
      }
    } else if (delBtn) {
      const id = delBtn.getAttribute('data-id');
      if (cart[id]) {
        delete cart[id];
        updateUI();
      }
    }
  });

  // Filtro de catálogo en tiempo real en la pantalla POS
  if (catalogSearch) {
    catalogSearch.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const items = document.querySelectorAll('.pos-product-item');
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'flex' : 'none';
      });
    });
  }

  // Validación antes del submit
  if (form) {
    form.addEventListener('submit', (e) => {
      const items = Object.values(cart);
      if (items.length === 0) {
        e.preventDefault();
        alert('Por favor agrega al menos un producto al carrito antes de registrar la venta.');
      }
    });
  }
}

/* ==========================================================================
   5. SWITCH DE CLIENTE HABITUAL (REVEAL NOMBRE)
   ========================================================================== */
function initClientToggle() {
  const switchEl = document.getElementById('es_habitual');
  const nombreDiv = document.getElementById('nombre_div');
  const nombreInput = document.getElementById('nombre');

  if (!switchEl || !nombreDiv) return;

  const updateState = () => {
    if (switchEl.checked) {
      nombreDiv.style.display = 'block';
      if (nombreInput) nombreInput.focus();
    } else {
      nombreDiv.style.display = 'none';
    }
  };

  switchEl.addEventListener('change', updateState);
  updateState();
}

function escapeHtml(string) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(string).replace(/[&<>"']/g, function(m) { return map[m]; });
}
