// Main application entry point and global state
const ASIC_OVERRIDES = {}; // Track user modifications per model
let asicRowCount = 0;

function _(key) {
    const translationsEl = document.getElementById('translations-data');
    if (translationsEl) {
        const translations = JSON.parse(translationsEl.textContent);
        return translations[key] || key;
    }
    return key;
}

function addAsicRow(preselectModel = null) {
    asicRowCount++;
    const currentId = asicRowCount;
    const tbody = document.getElementById('asics_tbody');
    if (!tbody) return;

    const row = document.createElement('tr');
    row.id = `asic_row_${currentId}`;

    const bitmain = ASIC_DATA.filter(a => a.model.toLowerCase().includes('antminer') || a.model.includes('HOST Antminer'));
    const whatsminer = ASIC_DATA.filter(a => a.model.toLowerCase().includes('whatsminer'));

    let optionsHtml = '<option value="">-- Seleccionar --</option>';
    optionsHtml += '<optgroup label="BITMAIN">';
    bitmain.forEach(a => {
        optionsHtml += `<option value="${a.model}">${a.model}</option>`;
    });
    optionsHtml += '</optgroup>';
    optionsHtml += '<optgroup label="WHATSMINER">';
    whatsminer.forEach(a => {
        optionsHtml += `<option value="${a.model}">${a.model}</option>`;
    });
    optionsHtml += '</optgroup>';

    row.innerHTML = `
        <td>
            <select class="form-control" name="asic_model_${currentId}">
                ${preselectModel ? optionsHtml.replace(`value="${preselectModel}"`, `value="${preselectModel}" selected`) : optionsHtml}
            </select>
        </td>
        <td><input type="number" class="form-control" name="asic_units_${currentId}" value="0" min="0" onkeydown="return onlyNumbers(event, false)" onchange="updateAsicsTotal()"></td>
        <td><input type="number" class="form-control" name="asic_price_${currentId}" value="0" onkeydown="return onlyNumbers(event, true)" onchange="updateAsicRowMetrics(${currentId})"></td>
        <td><input type="number" class="form-control" name="asic_hashrate_${currentId}" value="0" onkeydown="return onlyNumbers(event, true)" onchange="updateAsicRowMetrics(${currentId})"></td>
        <td><input type="number" class="form-control" name="asic_consumption_${currentId}" value="0" onkeydown="return onlyNumbers(event, false)" onchange="updateAsicRowMetrics(${currentId})"></td>
        <td><input type="number" step="0.01" class="form-control" name="asic_usd_per_th_${currentId}" value="0" readonly></td>
        <td><input type="number" step="0.01" class="form-control" name="asic_j_per_th_${currentId}" value="0" readonly></td>
        <td><button type="button" class="btn btn-danger btn-sm" onclick="removeAsicRow(${currentId})">Remove</button></td>
    `;
    tbody.appendChild(row);

    if (preselectModel) {
        updateAsicSpecs(row, preselectModel, currentId);
        updateAsicsTotal();
    }

    row.querySelector('select').addEventListener('change', function () {
        updateAsicSpecs(row, this.value, currentId);
        updateAsicsTotal();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    });
}

function updateAsicRowMetrics(id) {
    const row = document.getElementById(`asic_row_${id}`);
    if (!row) return;

    const modelEl = row.querySelector(`select[name="asic_model_${id}"]`);
    const priceEl = row.querySelector(`input[name="asic_price_${id}"]`);
    const hashrateEl = row.querySelector(`input[name="asic_hashrate_${id}"]`);
    const consumptionEl = row.querySelector(`input[name="asic_consumption_${id}"]`);
    const usdPerThEl = row.querySelector(`input[name="asic_usd_per_th_${id}"]`);
    const jPerThEl = row.querySelector(`input[name="asic_j_per_th_${id}"]`);

    if (!modelEl || !priceEl || !hashrateEl || !consumptionEl || !usdPerThEl || !jPerThEl) return;

    const model = modelEl.value;
    const price = parseFloat(priceEl.value) || 0;
    const hashrate = parseFloat(hashrateEl.value) || 0;
    const consumption = parseFloat(consumptionEl.value) || 0;

    usdPerThEl.value = hashrate > 0 ? (price / hashrate).toFixed(2) : 0;
    jPerThEl.value = hashrate > 0 ? (consumption / hashrate).toFixed(2) : 0;

    if (model) {
        const original = ASIC_DATA.find(a => a.model === model);
        if (original) {
            const allRows = document.querySelectorAll('#asics_tbody tr[id^="asic_row_"]');
            let modelOverride = { price: null, hashrate: null, consumption: null };

            allRows.forEach(r => {
                const s = r.querySelector('select');
                if (s && s.value === model) {
                    const rPrice = parseFloat(r.querySelector('input[name*="price"]').value) || 0;
                    const rHashrate = parseFloat(r.querySelector('input[name*="hashrate"]').value) || 0;
                    const rConsumption = parseFloat(r.querySelector('input[name*="consumption"]').value) || 0;

                    if (Math.abs(rPrice - original.price) > 0.01) modelOverride.price = rPrice;
                    if (Math.abs(rHashrate - original.hashrate) > 0.01) modelOverride.hashrate = rHashrate;
                    if (Math.abs(rConsumption - original.consumption) > 0.01) modelOverride.consumption = rConsumption;
                }
            });

            if (modelOverride.price !== null || modelOverride.hashrate !== null || modelOverride.consumption !== null) {
                ASIC_OVERRIDES[model] = modelOverride;
            } else {
                delete ASIC_OVERRIDES[model];
            }
        }
    }

    updateAsicsTotal();
    if (document.getElementById('benchmarks-tab')?.classList.contains('active')) {
        if (typeof renderBenchmarks === 'function') renderBenchmarks();
    }
}

function updateAsicSpecs(row, modelName, id) {
    const asic = ASIC_DATA.find(a => a.model === modelName);
    const priceEl = row.querySelector(`input[name="asic_price_${id}"]`);
    const hashrateEl = row.querySelector(`input[name="asic_hashrate_${id}"]`);
    const consumptionEl = row.querySelector(`input[name="asic_consumption_${id}"]`);

    if (!priceEl || !hashrateEl || !consumptionEl) return;

    if (asic) {
        priceEl.value = asic.price;
        hashrateEl.value = asic.hashrate;
        consumptionEl.value = asic.consumption;
    } else {
        priceEl.value = 0;
        hashrateEl.value = 0;
        consumptionEl.value = 0;
    }
    updateAsicRowMetrics(id);
}

function removeAsicRow(id) {
    const row = document.getElementById(`asic_row_${id}`);
    if (!row) return;
    const model = row.querySelector('select')?.value;
    if (model) delete ASIC_OVERRIDES[model];
    row.remove();
    updateAsicsTotal();
    if (document.getElementById('benchmarks-tab')?.classList.contains('active')) {
        if (typeof renderBenchmarks === 'function') renderBenchmarks();
    }
}

function updateAsicsTotal() {
    let total = 0;
    const addedRows = document.querySelectorAll('#asics_tbody tr[id^="asic_row_"]');
    addedRows.forEach(row => {
        const units = parseFloat(row.querySelector('input[name*="units"]').value) || 0;
        const price = parseFloat(row.querySelector('input[name*="price"]').value) || 0;
        total += units * price;
    });
    const asicsValueEl = document.getElementById('asics_unit_value');
    if (asicsValueEl) asicsValueEl.value = total.toFixed(2);
    if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
}

// Note: formatDisplayCurrency and parseDisplayCurrency are now in ui_handlers.js

function renderDashboard() {
    const resultsDataEl = document.getElementById('results-data-json');
    const container = document.getElementById('dashboard-container');
    if (!container) return;

    if (!resultsDataEl) {
        container.innerHTML = `<div class="alert alert-warning">${_('no_data_msg') || 'No hay datos disponibles. Por favor, calcula los resultados primero.'}</div>`;
        return;
    }

    const res = JSON.parse(resultsDataEl.textContent);
    let cumulativeCashFlow = -res.investment;

    let html = `
        <div class="mt-4">
            <!-- Dashboard Header -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="bg-gradient p-3 rounded text-white d-flex justify-content-between align-items-center" style="background-color: #217346;">
                        <div>
                            <h3 class="mb-0">${_('dashboard_title')}: ${res.farm_name || 'PROYECTO BITCOIN'}</h3>
                            <p class="mb-0 opacity-75">${_('dashboard_report')}</p>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-white text-dark p-2">${_('confidential')}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI Section -->
            <div class="row g-3 mb-4">
                <div class="col-md-3">
                    <div class="excel-kpi-box text-center">
                        <div class="excel-kpi-label">${_('roi')}</div>
                        <div class="excel-kpi-value text-success">${res.roi.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="excel-kpi-box text-center">
                        <div class="excel-kpi-label">${_('cagr')}</div>
                        <div class="excel-kpi-value text-info">${res.cagr.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="excel-kpi-box text-center">
                        <div class="excel-kpi-label">${_('break_even')}</div>
                        <div class="excel-kpi-value text-warning">${res.break_even_usd}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="excel-kpi-box text-center">
                        <div class="excel-kpi-label">${_('cost_per_btc_label')}</div>
                        <div class="excel-kpi-value text-primary">$${formatDisplayCurrency(res.cost_per_btc)}</div>
                    </div>
                </div>
            </div>

            <!-- Unified Main Table -->
            <div class="row mb-4">
                <div class="col-12 overflow-auto">
                    <table class="excel-table shadow-sm">
                        <thead>
                            <tr>
                                <th colspan="12" class="excel-header-main text-uppercase">${_('flujo_consolidado')}</th>
                            </tr>
                            <tr>
                                <th>${_('year')}</th>
                                <th>${_('btc_prod')}</th>
                                <th>${_('mining_rev')}</th>
                                <th>${_('other_rev')}</th>
                                <th>${_('total_rev')}</th>
                                <th>${_('elec_cost')}</th>
                                <th>${_('opex_fixed')}</th>
                                <th>${_('ebitda')}</th>
                                <th>${_('depreciation_label')}</th>
                                <th>${_('net_profit')}</th>
                                <th>${_('margin')}</th>
                                <th>${_('cumulative_flow')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${res.annual_generation.map((y, idx) => {
        cumulativeCashFlow += y.net_profit;
        const rowClass = y.net_profit < 0 ? 'excel-negative' : '';
        return `
                                    <tr class="${rowClass}">
                                        <td class="text-center fw-bold" style="background-color: var(--bs-secondary-bg);">${y.year}</td>
                                        <td>${y.btc_generated.toFixed(4)}</td>
                                        <td>$${formatDisplayCurrency(y.usd_revenue)}</td>
                                        <td class="text-success">$${formatDisplayCurrency(y.other_income)}</td>
                                        <td class="fw-bold">$${formatDisplayCurrency(y.total_revenue)}</td>
                                        <td class="text-danger">($${formatDisplayCurrency(y.electricity_cost)})</td>
                                        <td class="text-danger">($${formatDisplayCurrency(y.opex_cost)})</td>
                                        <td class="fw-bold">$${formatDisplayCurrency(y.total_revenue - y.electricity_cost - y.opex_cost)}</td>
                                        <td class="text-muted small">($${formatDisplayCurrency(y.depreciation)})</td>
                                        <td class="${y.net_profit >= 0 ? 'text-success' : 'text-danger'} fw-bold">$${formatDisplayCurrency(y.net_profit)}</td>
                                        <td>${y.operating_margin.toFixed(1)}%</td>
                                        <td class="${cumulativeCashFlow >= 0 ? 'text-success' : 'text-danger'} fw-bold" style="background-color: var(--bs-tertiary-bg);">$${formatDisplayCurrency(cumulativeCashFlow)}</td>
                                    </tr>
                                `;
    }).join('')}
                        </tbody>
                        <tfoot>
                            <tr class="fw-bold" style="background-color: var(--bs-secondary-bg);">
                                <td colspan="2" class="text-center">${_('totals')}</td>
                                <td>$${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.usd_revenue, 0))}</td>
                                <td class="text-success">$${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.other_income, 0))}</td>
                                <td>$${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.total_revenue, 0))}</td>
                                <td class="text-danger">($${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.electricity_cost, 0))})</td>
                                <td class="text-danger">($${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.opex_cost, 0))})</td>
                                <td>$${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + (y.total_revenue - y.electricity_cost - y.opex_cost), 0))}</td>
                                <td class="text-muted">($${formatDisplayCurrency(res.annual_generation.reduce((acc, y) => acc + y.depreciation, 0))})</td>
                                <td class="${res.total_profits_usd >= 0 ? 'text-success' : 'text-danger'}">$${formatDisplayCurrency(res.total_profits_usd)}</td>
                                <td class="text-center">${(res.total_profits_usd / res.annual_generation.reduce((acc, y) => acc + y.total_revenue, 0) * 100).toFixed(1)}%</td>
                                <td class="${cumulativeCashFlow >= 0 ? 'text-success' : 'text-danger'}">$${formatDisplayCurrency(cumulativeCashFlow)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>

            <div class="row">
                <!-- Investment Recovery Column -->
                <div class="col-lg-7">
                    <table class="excel-table shadow-sm mb-4">
                        <thead>
                            <tr>
                                <th colspan="4" class="excel-header-main">${_('recovery_status')}</th>
                            </tr>
                            <tr>
                                <th>${_('year')}</th>
                                <th>${_('annual_net_flow')}</th>
                                <th>${_('accumulated_return')}</th>
                                <th>${_('pending_investment')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="text-center fw-bold">${_('year_0')}</td>
                                <td class="text-danger">($${formatDisplayCurrency(res.investment)})</td>
                                <td class="text-danger">$0.00</td>
                                <td class="fw-bold text-danger">($${formatDisplayCurrency(res.investment)})</td>
                            </tr>
                            ${(() => {
            let runningReturn = 0;
            return res.annual_generation.map(y => {
                runningReturn += y.net_profit;
                const pending = Math.max(0, res.investment - runningReturn);
                const isRecovered = runningReturn >= res.investment;
                return `
                                        <tr>
                                            <td class="text-center fw-bold">${y.year}</td>
                                            <td class="${y.net_profit >= 0 ? 'text-success' : 'text-danger'}">$${formatDisplayCurrency(y.net_profit)}</td>
                                            <td class="text-success">$${formatDisplayCurrency(runningReturn)}</td>
                                            <td class="${isRecovered ? 'text-success' : 'text-danger'} fw-bold">
                                                ${isRecovered ? _('recovered') : `($${formatDisplayCurrency(pending)})`}
                                            </td>
                                        </tr>
                                    `;
            }).join('');
        })()}
                        </tbody>
                    </table>
                </div>

                <!-- CAPEX/OPEX Summary Column -->
                <div class="col-lg-5">
                    <div class="card shadow-sm border-0 mb-4" style="background: var(--bs-tertiary-bg);">
                        <div class="card-header excel-header-main">
                            ${_('cost_structure')}
                        </div>
                        <div class="card-body p-0">
                            <table class="excel-table border-0">
                                <tr>
                                    <td class="text-start excel-sub-header" colspan="2">${_('initial_investment')}</td>
                                </tr>
                                ${Object.entries(res.capex_breakdown).filter(([k]) => k !== 'Total').map(([name, val]) => `
                                    <tr>
                                        <td class="text-start">${name}</td>
                                        <td class="fw-bold">$${formatDisplayCurrency(val)}</td>
                                    </tr>
                                `).join('')}
                                <tr class="fw-bold" style="border-top: 2px solid #217346;">
                                    <td class="text-start">${_('total_capex')}</td>
                                    <td class="text-primary">$${formatDisplayCurrency(res.capex_breakdown.Total)}</td>
                                </tr>
                                <tr>
                                    <td class="text-start excel-sub-header" colspan="2">${_('monthly_opex')}</td>
                                </tr>
                                <tr><td class="text-start">${_('payroll')}</td><td>$${formatDisplayCurrency(res.opex_summary.staff_monthly)}</td></tr>
                                <tr><td class="text-start">${_('services_fixed')}</td><td>$${formatDisplayCurrency(res.opex_summary.services_monthly)}</td></tr>
                                <tr><td class="text-start">${_('pure_energy')}</td><td>$${res.energy_cost_per_mwh_pure.toFixed(2)}</td></tr>
                                <tr><td class="text-start">${_('variable_om')}</td><td>$${res.hourly_variable_maintenance.toFixed(2)}</td></tr>
                                <tr class="fw-bold" style="border-top: 2px solid #2e7d32; background-color: var(--bs-secondary-bg);">
                                    <td class="text-start">${_('unified_opc')}</td>
                                    <td class="text-success">$${res.opc_per_h.toFixed(2)}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="alert alert-info shadow-sm">
                        <i class="bi bi-info-circle-fill me-2"></i>
                        <strong>${_('technical_note')}:</strong> ${_('technical_note_msg')}
                    </div>
                </div>
            </div>
        </div>`;

    container.innerHTML = html;
}

// Event Listeners and Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Theme initialization
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);

    // Form handlers
    const mainForm = document.querySelector('form');
    if (mainForm) {
        mainForm.addEventListener('input', debounce(() => calculateResults(), 500));
        mainForm.addEventListener('change', debounce(() => calculateResults(), 500));
    }

    document.querySelectorAll('input, select').forEach(el => {
        el.addEventListener('change', debounce(() => calculateResults(), 500));
    });

    // Formatting initialization
    document.querySelectorAll('.price-input').forEach(el => {
        const val = parseDisplayCurrency(el.value);
        if (val > 0) el.value = formatDisplayCurrency(val);
    });

    // Tab switch handlers
    document.getElementById('benchmarks-tab')?.addEventListener('shown.bs.tab', () => {
        if (typeof renderBenchmarks === 'function') renderBenchmarks();
    });

    document.getElementById('monthly-dashboard-tab')?.addEventListener('shown.bs.tab', () => {
        if (typeof renderMonthlyDashboard === 'function') renderMonthlyDashboard();
    });

    // Initial power source
    if (typeof togglePowerSource === 'function') togglePowerSource();

    // Initial results
    if (typeof calculateResults === 'function') calculateResults();
});
