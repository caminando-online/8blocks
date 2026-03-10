function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icons
    const sunIcon = document.querySelector('#theme-toggle .bi-sun-fill');
    const moonIcon = document.querySelector('#theme-toggle .bi-moon-stars-fill');
    if (sunIcon && moonIcon) {
        if (newTheme === 'dark') {
            sunIcon.classList.add('d-none');
            moonIcon.classList.remove('d-none');
        } else {
            sunIcon.classList.remove('d-none');
            moonIcon.classList.add('d-none');
        }
    }
}

function setLanguage(lang) {
    window.location.href = `/set_language/${lang}`;
}

function onlyNumbers(event, allowDecimal = false) {
    const key = event.key;
    // Allow control keys
    if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Escape', '-'].includes(key)) {
        return true;
    }
    // Allow digits
    if (/[0-9]/.test(key)) {
        return true;
    }
    // Allow decimal point or comma if requested and not already present
    if (allowDecimal && (key === '.' || key === ',') && !event.target.value.includes('.') && !event.target.value.includes(',')) {
        return true;
    }
    // Ignore everything else
    event.preventDefault();
    return false;
}

function togglePowerSource() {
    const powerSourceEl = document.getElementById('power_source');
    if (!powerSourceEl) return;

    const powerSource = powerSourceEl.value;
    const directFields = document.getElementById('direct_energy_fields');
    const gasFields = document.getElementById('gas_powered_fields');
    if (!directFields || !gasFields) return;

    directFields.innerHTML = '';
    gasFields.innerHTML = '';

    if (powerSource === 'Direct Energy') {
        directFields.style.visibility = 'visible';
        gasFields.style.visibility = 'hidden';
        directFields.innerHTML = `
            <div class="mb-3">
                <label for="energy_cost_per_mwh" class="form-label">Energy Cost ($/MWh)</label>
                <input type="number" step="0.01" class="form-control" id="energy_cost_per_mwh" name="energy_cost_per_mwh" required>
            </div>
        `;
    } else if (powerSource === 'Gas powered') {
        directFields.style.visibility = 'hidden';
        gasFields.style.visibility = 'visible';
        gasFields.innerHTML = `
            <div class="mb-3">
                <label for="gas_unit" class="form-label">Gas Unit</label>
                <select class="form-control" id="gas_unit" name="gas_unit" onchange="updateGasPriceLabel()">
                    <option value="MBTU">MBTU</option>
                    <option value="M3">M3</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="gas_price_per_unit" class="form-label">Gas Price ($/MBTU)</label>
                <input type="number" step="0.01" class="form-control" id="gas_price_per_unit" name="gas_price_per_unit">
            </div>
            <div class="mb-3">
                <label for="gas_kcal" class="form-label">Gas kCal</label>
                <input type="number" class="form-control" id="gas_kcal" name="gas_kcal" value="8500">
            </div>
            <div class="mb-3">
                <label for="generator_efficiency" class="form-label">Generator Efficiency (%)</label>
                <input type="number" step="0.01" class="form-control" id="generator_efficiency" name="generator_efficiency" value="35">
            </div>
            <div class="mb-3">
                <label for="gas_price_per_mwh" class="form-label">Gas Price ($/MWh) 
                    <button type="button" class="btn btn-info btn-sm" data-bs-toggle="modal" data-bs-target="#gasPriceModal">i</button>
                </label>
                <input type="number" step="0.01" class="form-control" id="gas_price_per_mwh" name="gas_price_per_mwh" readonly>
            </div>
            <div class="mb-3">
                <label for="om_per_mwh" class="form-label">O&M ($/MWh)</label>
                <input type="number" step="0.01" class="form-control" id="om_per_mwh" name="om_per_mwh">
            </div>
            <div class="mb-3">
                <label for="overhauling" class="form-label">Overhauling ($)</label>
                <input type="number" class="form-control" id="overhauling" name="overhauling" disabled placeholder="To be developed">
            </div>
        `;
        if (typeof calculateGasPrice === 'function') calculateGasPrice();

        // Add event listeners for gas fields
        const gasPriceInput = document.getElementById('gas_price_per_unit');
        const gasKcalInput = document.getElementById('gas_kcal');
        const genEffInput = document.getElementById('generator_efficiency');

        if (gasPriceInput) gasPriceInput.addEventListener('input', calculateGasPrice);
        if (gasKcalInput) gasKcalInput.addEventListener('input', calculateGasPrice);
        if (genEffInput) genEffInput.addEventListener('input', calculateGasPrice);
    } else {
        directFields.style.visibility = 'hidden';
        gasFields.style.visibility = 'hidden';
    }
}

function updateGasPriceLabel() {
    const unitEl = document.getElementById('gas_unit');
    if (!unitEl) return;
    const unit = unitEl.value;
    const label = document.querySelector('label[for="gas_price_per_unit"]');
    if (label) label.textContent = `Gas Price ($/${unit})`;
}

function formatDisplayCurrency(val) {
    if (isNaN(val) || val === null) return '0.00';
    return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function parseDisplayCurrency(str) {
    if (!str) return 0;
    return parseFloat(str.toString().replace(/,/g, '')) || 0;
}

function handlePriceFocus(el) {
    const val = parseDisplayCurrency(el.value);
    el.value = val === 0 ? '' : val.toFixed(2);
}

function handlePriceBlur(el) {
    const val = parseFloat(el.value) || parseDisplayCurrency(el.value);
    el.value = formatDisplayCurrency(val);
}


function togglePriceMethod() {
    const method = document.getElementById('price_method')?.value;
    const manualFields = document.getElementById('manual_price_fields');
    const backlogInfo = document.getElementById('backlog_info');

    if (!manualFields || !backlogInfo) return;

    if (method === 'manual') {
        manualFields.style.display = 'block';
        backlogInfo.style.display = 'none';
    } else {
        manualFields.style.display = 'none';
        backlogInfo.style.display = 'block';
        updateBacklogProjections();
    }
    if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
}

function toggleDifficultyMethod() {
    const method = document.getElementById('difficulty_method')?.value;
    const msg = document.getElementById('diff_backlog_msg');
    if (!msg) return;

    if (method === 'backlog' && typeof DIFFICULTY_BACKLOG !== 'undefined') {
        msg.style.display = 'block';

        for (let y = 0; y < 8; y++) {
            let yearlyProduct = 1;
            for (let m = 0; m < 12; m++) {
                const monthIdx = y * 12 + m;
                const change = DIFFICULTY_BACKLOG[monthIdx % DIFFICULTY_BACKLOG.length].change_pct;
                yearlyProduct *= (1 + change / 100);
            }
            const avgMonthly = (Math.pow(yearlyProduct, 1 / 12) - 1) * 100;
            const input = document.getElementById(`manual_diff_var_${y + 1}`);
            if (input) input.value = avgMonthly.toFixed(2);
        }
    } else {
        msg.style.display = 'none';
    }
    if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
}

function syncManualPrices(year, type) {
    if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
}

function syncBacklogModifier() {
    const overrideVal = document.getElementById('btc_price_override')?.value;
    let currentPrice;
    if (overrideVal) {
        currentPrice = parseFloat(overrideVal);
    } else {
        const el = document.getElementById('val_btc_price');
        currentPrice = parseFloat(el?.dataset.raw) || (el ? parseDisplayCurrency(el.innerText) : 0);
    }

    for (let i = 1; i <= 8; i++) {
        const modEl = document.getElementById(`backlog_modifier_${i}`);
        const priceDisplayEl = document.getElementById(`backlog_price_display_${i}`);
        const hiddenVarEl = document.getElementById(`backlog_price_hidden_${i}`);

        if (!modEl) continue;

        const baseVar = parseFloat(modEl.dataset.baseVar) || 0;
        const modValue = parseFloat(modEl.value) || 0;
        const effectiveVar = baseVar * (1 + modValue / 100);
        currentPrice = currentPrice * (1 + effectiveVar / 100);

        if (priceDisplayEl) priceDisplayEl.value = formatDisplayCurrency(currentPrice);
        if (hiddenVarEl) hiddenVarEl.value = effectiveVar.toFixed(4);
    }
    if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
}

function updateBacklogProjections() {
    const overrideVal = document.getElementById('btc_price_override')?.value;
    const backlogProjList = document.getElementById('backlog_projection_list');
    if (!backlogProjList || typeof PRICE_BACKLOG === 'undefined') return;

    let startPrice;
    if (overrideVal) {
        startPrice = parseFloat(overrideVal);
    } else {
        const el = document.getElementById('val_btc_price');
        startPrice = parseFloat(el?.dataset.raw) || (el ? parseDisplayCurrency(el.innerText) : 0);
    }

    let currentPrice = startPrice;
    let baseVariations = [];

    for (let i = 0; i < 96; i++) {
        const backlogIdx = i % PRICE_BACKLOG.length;
        const changePct = PRICE_BACKLOG[backlogIdx].change_pct;
        currentPrice = currentPrice * (1 + changePct / 100);

        if (i % 12 === 11) {
            let yearlyProduct = 1;
            for (let m = 0; m < 12; m++) {
                const mIdx = (Math.floor(i / 12) * 12 + m) % PRICE_BACKLOG.length;
                yearlyProduct *= (1 + PRICE_BACKLOG[mIdx].change_pct / 100);
            }
            const annualGrowth = (yearlyProduct - 1) * 100;
            baseVariations.push(annualGrowth.toFixed(1));
        }
    }

    let html = '<div class="row g-2">';
    currentPrice = startPrice;
    baseVariations.forEach((baseVar, idx) => {
        const i = idx + 1;
        const histYear = PRICE_BACKLOG[(idx * 12) % PRICE_BACKLOG.length].year;
        const effectiveVar = parseFloat(baseVar);
        currentPrice = currentPrice * (1 + effectiveVar / 100);
        const formattedPrice = formatDisplayCurrency(currentPrice);

        html += `
        <div class="col-md-6 mb-2">
            <div class="p-2 border rounded card shadow-sm">
                <label class="form-label x-small fw-bold mb-1">Año ${i} (Base ${histYear}: ${baseVar}%)</label>
                <div class="row g-1">
                    <div class="col-7">
                        <div class="input-group input-group-sm">
                            <span class="input-group-text">$</span>
                            <input type="text" class="form-control text-end" id="backlog_price_display_${i}" value="${formattedPrice}" readonly>
                        </div>
                    </div>
                    <div class="col-5">
                        <div class="input-group input-group-sm">
                            <input type="number" step="1" class="form-control" id="backlog_modifier_${i}" data-base-var="${baseVar}" value="0" oninput="syncBacklogModifier()" title="Modificador %">
                            <span class="input-group-text">%</span>
                        </div>
                        <input type="hidden" name="backlog_price_${i}" id="backlog_price_hidden_${i}" value="${baseVar}">
                    </div>
                </div>
            </div>
        </div>`;
    });
    html += '</div>';
    backlogProjList.innerHTML = html;
}

function refreshNetworkData() {
    const btn = document.querySelector('button[onclick="refreshNetworkData()"]');
    if (!btn) return;
    const originalText = btn.innerText;
    btn.innerText = "Actualizando...";
    btn.disabled = true;

    fetch('/network_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert("Error actualizando datos: " + data.error);
            } else {
                const priceEl = document.getElementById('val_btc_price');
                if (priceEl) {
                    priceEl.innerText = formatDisplayCurrency(data.btc_price);
                    priceEl.dataset.raw = data.btc_price;
                }

                const diffEl = document.getElementById('val_difficulty');
                if (diffEl) diffEl.innerText = data.difficulty;
                const blockEl = document.getElementById('val_block');
                if (blockEl) blockEl.innerText = data.current_block;
                const halvingEl = document.getElementById('val_blocks_to_halving');
                if (halvingEl) halvingEl.innerText = data.blocks_to_halving;
                const monthsEl = document.getElementById('val_months_to_halving');
                if (monthsEl) monthsEl.innerText = data.months_to_halving;
                const diffAdjEl = document.getElementById('val_blocks_to_diff');
                if (diffAdjEl) diffAdjEl.innerText = data.blocks_to_next_difficulty;
                const estDiffEl = document.getElementById('val_est_diff_change');
                if (estDiffEl) estDiffEl.innerText = data.estimated_next_diff_change.toFixed(2);

                if (typeof calculateResults === 'function') calculateResults();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Error de conexión al actualizar datos.");
        })
        .finally(() => {
            btn.innerText = originalText;
            btn.disabled = false;
        });
}

let capexCount = 0;
function addOtherCapex() {
    const name = prompt("Enter the name for the new CAPEX item:");
    if (!name) return;
    capexCount++;
    const div = document.getElementById('other_capex');
    if (!div) return;
    const newField = document.createElement('div');
    newField.className = 'mb-3';
    newField.id = `capex_item_${capexCount}`;
    newField.innerHTML = `
        <label for="other_capex_${capexCount}" class="form-label small">${name} (USD)</label>
        <input type="hidden" name="other_capex_name_${capexCount}" value="${name}">
        <div class="input-group input-group-sm">
            <input type="number" class="form-control" id="other_capex_${capexCount}" name="other_capex_${capexCount}" value="0">
            <button type="button" class="btn btn-outline-danger" onclick="removeCapex(${capexCount})">Remove</button>
        </div>
    `;
    div.appendChild(newField);
}

function removeCapex(id) {
    const element = document.getElementById(`capex_item_${id}`);
    if (element) {
        element.remove();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    }
}

let staffCount = 0;
function addStaff() {
    const name = prompt("Enter the staff role name:");
    if (!name) return;
    staffCount++;
    const div = document.getElementById('staff_fields');
    if (!div) return;
    const newField = document.createElement('div');
    newField.className = 'mb-1';
    newField.id = `staff_item_${staffCount}`;
    newField.innerHTML = `
        <label for="staff_${staffCount}" class="form-label x-small">${name} (USD/month)</label>
        <input type="hidden" name="staff_name_${staffCount}" value="${name}">
        <div class="input-group input-group-sm">
            <input type="number" class="form-control" id="staff_${staffCount}" name="staff_${staffCount}" value="0">
            <button type="button" class="btn btn-outline-danger" onclick="removeStaff(${staffCount})">Remove</button>
        </div>
    `;
    div.appendChild(newField);
}

function removeStaff(id) {
    const element = document.getElementById(`staff_item_${id}`);
    if (element) {
        element.remove();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    }
}

let serviceCount = 0;
function addService() {
    const name = prompt("Enter the service name:");
    if (!name) return;
    serviceCount++;
    const div = document.getElementById('service_fields');
    if (!div) return;
    const newField = document.createElement('div');
    newField.className = 'mb-1';
    newField.id = `service_item_${serviceCount}`;
    newField.innerHTML = `
        <label for="service_${serviceCount}" class="form-label x-small">${name} (USD/month)</label>
        <input type="hidden" name="service_name_${serviceCount}" value="${name}">
        <div class="input-group input-group-sm">
            <input type="number" class="form-control" id="service_${serviceCount}" name="service_${serviceCount}" value="0">
            <button type="button" class="btn btn-outline-danger" onclick="removeService(${serviceCount})">Remove</button>
        </div>
    `;
    div.appendChild(newField);
}

function removeService(id) {
    const element = document.getElementById(`service_item_${id}`);
    if (element) {
        element.remove();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    }
}

let opexCount = 0;
function addOtherOpex() {
    const name = prompt("Enter the other OPEX name:");
    if (!name) return;
    opexCount++;
    const div = document.getElementById('other_fields');
    if (!div) return;
    const newField = document.createElement('div');
    newField.className = 'mb-1';
    newField.id = `other_item_${opexCount}`;
    newField.innerHTML = `
        <label for="other_${opexCount}" class="form-label x-small">${name} (USD/month)</label>
        <input type="hidden" name="other_name_${opexCount}" value="${name}">
        <div class="input-group input-group-sm">
            <input type="number" class="form-control" id="other_${opexCount}" name="other_${opexCount}" value="0">
            <button type="button" class="btn btn-outline-danger" onclick="removeOtherOpex(${opexCount})">Remove</button>
        </div>
    `;
    div.appendChild(newField);
}

function removeOtherOpex(id) {
    const element = document.getElementById(`other_item_${id}`);
    if (element) {
        element.remove();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    }
}

function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        // Dispose existing instance if any
        const existing = bootstrap.Popover.getInstance(popoverTriggerEl);
        if (existing) existing.dispose();

        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'hover focus',
            placement: 'top',
            container: 'body',
            html: true,
            boundary: 'viewport',
            fallbackPlacements: ['bottom', 'right', 'left'],
            customClass: 'popover-dismissible'
        });
    });
}

// Dismiss all popovers on scroll to prevent them from getting stuck
let scrollDismissTimer = null;
window.addEventListener('scroll', function () {
    if (scrollDismissTimer) clearTimeout(scrollDismissTimer);
    scrollDismissTimer = setTimeout(function () {
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
            const instance = bootstrap.Popover.getInstance(el);
            if (instance) instance.hide();
        });
    }, 50);
}, true);

// Also dismiss on any scrollable container within the page
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.overflow-auto, .table-responsive, .card-body').forEach(function (container) {
        container.addEventListener('scroll', function () {
            document.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
                const instance = bootstrap.Popover.getInstance(el);
                if (instance) instance.hide();
            });
        });
    });
});
