// Global state for attach/detach
let monthlyDashboardAttached = true;

// Format a raw difficulty number to a human-readable scaled string
// e.g. 1.45e+14 → "1.4500 T", 8.2e+16 → "82.0000 P"
function formatDifficulty(val) {
    const tiers = [
        { threshold: 1e18, divisor: 1e18, suffix: 'E' },
        { threshold: 1e15, divisor: 1e15, suffix: 'P' },
        { threshold: 1e12, divisor: 1e12, suffix: 'T' },
        { threshold: 1e9,  divisor: 1e9,  suffix: 'G' },
        { threshold: 1e6,  divisor: 1e6,  suffix: 'M' },
        { threshold: 1e3,  divisor: 1e3,  suffix: 'K' },
    ];
    for (const t of tiers) {
        if (val >= t.threshold) {
            return (val / t.divisor).toFixed(4) + ' ' + t.suffix;
        }
    }
    return val.toFixed(4);
}

function toggleMonthlyAttach() {
    monthlyDashboardAttached = !monthlyDashboardAttached;
    const btn = document.getElementById('monthly-attach-btn');
    if (btn) {
        btn.innerHTML = monthlyDashboardAttached
            ? '<span class="badge bg-success me-1">ON</span> Attached'
            : '<span class="badge bg-secondary me-1">OFF</span> Detached';
        btn.className = monthlyDashboardAttached
            ? 'btn btn-sm btn-outline-success'
            : 'btn btn-sm btn-outline-secondary';
    }
}

function applyGlobalMonthlyOverrides() {
    const priceVar = parseFloat(document.getElementById('global_price_var')?.value) || 0;
    const diffVar = parseFloat(document.getElementById('global_diff_var')?.value) || 0;

    for (let i = 1; i <= 12; i++) {
        const priceInput = document.getElementsByName(`monthly_price_var_${i}`)[0];
        const diffInput = document.getElementsByName(`monthly_diff_var_${i}`)[0];
        if (priceInput) priceInput.value = priceVar;
        if (diffInput) diffInput.value = diffVar;
    }

    if (typeof calculateResults === 'function') {
        calculateResults();
    }
}

function renderMonthlyDashboard() {
    const container = document.getElementById('monthly-dashboard-container');
    const resultsDataEl = document.getElementById('results-data-json');
    if (!container || !resultsDataEl) return;

    const results = JSON.parse(resultsDataEl.textContent);
    if (!results || !results.monthly_year1) {
        container.innerHTML = `<div class="alert alert-info py-2">${_('monthly_update_msg')}</div>`;
        return;
    }

    // ── Preserve global adjustment values before re-render ──
    const savedGlobalPrice = document.getElementById('global_price_var')?.value || '';
    const savedGlobalDiff = document.getElementById('global_diff_var')?.value || '';

    const data = results.monthly_year1;
    const y1 = results.annual_generation[0];

    // ── Compute Y1 summary from monthly data ──
    const y1TotalBtc = data.reduce((sum, m) => sum + m.btc_generated, 0);
    const y1TotalRevenue = data.reduce((sum, m) => sum + m.total_revenue, 0);
    const y1TotalNetProfit = data.reduce((sum, m) => sum + m.net_profit, 0);
    const y1AvgMargin = data.length > 0 ? data.reduce((sum, m) => sum + m.operating_margin, 0) / data.length : 0;

    // ── KPIs ABOVE table ──
    let html = `
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="excel-kpi-box text-center">
                    <div class="excel-kpi-label">${_('total_btc_y1') || 'Total BTC Y1'}</div>
                    <div class="excel-kpi-value text-success">${y1TotalBtc.toFixed(4)}</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="excel-kpi-box text-center">
                    <div class="excel-kpi-label">${_('total_revenue') || 'Total Revenue'}</div>
                    <div class="excel-kpi-value text-primary">$${formatDisplayCurrency(y1TotalRevenue)}</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="excel-kpi-box text-center">
                    <div class="excel-kpi-label">${_('net_profit') || 'Net Profit'}</div>
                    <div class="excel-kpi-value ${y1TotalNetProfit >= 0 ? 'text-success' : 'text-danger'}">
                        $${formatDisplayCurrency(y1TotalNetProfit)}
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="excel-kpi-box text-center">
                    <div class="excel-kpi-label">${_('average_margin') || 'Average Margin'}</div>
                    <div class="excel-kpi-value text-info">${y1AvgMargin.toFixed(1)}%</div>
                </div>
            </div>
        </div>

        <!-- Table Section -->
        <div class="row g-3 mb-3 align-items-center">
            <div class="col-md-2">
                <div class="excel-kpi-box text-center p-3">
                    <div class="excel-kpi-label">${_('monthly_kpi_total_btc')}</div>
                    <div class="excel-kpi-value">${y1.btc_generated.toFixed(4)} BTC</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="excel-kpi-box text-center p-3">
                    <div class="excel-kpi-label">${_('monthly_kpi_total_revenue')}</div>
                    <div class="excel-kpi-value text-primary">$${formatDisplayCurrency(y1.usd_revenue)}</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="excel-kpi-box text-center p-3">
                    <div class="excel-kpi-label">${_('monthly_kpi_total_profit')}</div>
                    <div class="excel-kpi-value text-success">$${formatDisplayCurrency(y1.net_profit)}</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="excel-kpi-box text-center p-3">
                    <div class="excel-kpi-label">${_('monthly_kpi_avg_margin')}</div>
                    <div class="excel-kpi-value text-warning">${y1.operating_margin.toFixed(1)}%</div>
                </div>
            </div>
            <div class="col-md-2 text-center">
                <button type="button" id="monthly-attach-btn" class="btn btn-sm btn-outline-success" onclick="toggleMonthlyAttach()">
                    <span class="badge bg-success me-1">ON</span> Attached
                </button>
                <div class="text-muted" style="font-size: 0.7rem; margin-top: 4px;">Sync with 8Y Calculator</div>
            </div>
        </div>
    `;

    // ── Monthly Breakdown Table ──
    html += `
        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-gradient bg-primary text-white py-3">
                <h5 class="mb-0 text-center text-uppercase" style="letter-spacing: 2px;">${_('monthly_dashboard_title')}</h5>
                <p class="mb-0 text-center small opacity-75">${_('monthly_dashboard_subtitle')}</p>
            </div>
            <div class="card-body p-0">
                <div class="bg-body-tertiary border-bottom p-2 d-flex justify-content-start align-items-center gap-3">
                    <span class="small fw-bold text-muted">${_('global_adjustment') || 'Ajuste Global (Año 1):'}</span>
                    <div class="input-group input-group-sm" style="width: 160px;">
                        <span class="input-group-text">${_('price_short') || 'Precio'}</span>
                        <input type="number" step="0.1" class="form-control text-center" id="global_price_var" placeholder="0"
                            value="${savedGlobalPrice}"
                            oninput="event.stopPropagation()" onchange="event.stopPropagation()">
                        <span class="input-group-text">%</span>
                    </div>
                    <div class="input-group input-group-sm" style="width: 170px;">
                        <span class="input-group-text">${_('difficulty') || 'Dificultad'}</span>
                        <input type="number" step="0.1" class="form-control text-center" id="global_diff_var" placeholder="0"
                            value="${savedGlobalDiff}"
                            oninput="event.stopPropagation()" onchange="event.stopPropagation()">
                        <span class="input-group-text">%</span>
                    </div>
                    <button type="button" class="btn btn-sm btn-primary" onclick="applyGlobalMonthlyOverrides()">
                        <i class="bi bi-check2-all"></i> ${_('apply_all') || 'Aplicar a todos'}
                    </button>
                </div>
                <div class="table-responsive">
                    <table class="table table-sm table-hover align-middle mb-0 excel-table" style="font-size: 0.95rem;">
                        <thead class="table-dark text-center">
                            <tr>
                                <th class="py-3">${_('month_label')}</th>
                                <th class="py-3">
                                    ${_('month_btc_price')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_btc_price')}" data-bs-content="Precio base * (1 + % variaci贸n acumulada)"></i>
                                </th>
                                <th class="py-3">% Adj. Price</th>
                                <th class="py-3">
                                    ${_('month_difficulty')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_difficulty')}" data-bs-content="Dificultad base * (1 + % variaci贸n acumulada)"></i>
                                </th>
                                <th class="py-3">% Adj. Diff.</th>
                                <th class="py-3 text-nowrap">
                                    ${_('month_btc_prod')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_btc_prod')}" data-bs-content="(Hashrate Propio / Hashrate Red) * Recompensa bloque * Bloques por mes"></i>
                                </th>
                                <th class="py-3 text-nowrap">
                                    ${_('month_mining_rev')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_mining_rev')}" data-bs-content="BTC Producidos * Precio BTC"></i>
                                </th>
                                <th class="py-3 text-success">
                                    ${_('month_other_income')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_other_income')}" data-bs-content="Ingresos por Hosting, Setup Fees, Intereses de Garant铆a, etc."></i>
                                </th>
                                <th class="py-3">
                                    ${_('month_total_rev')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_total_rev')}" data-bs-content="Mining Revenue + Other Incomes"></i>
                                </th>
                                <th class="py-3 text-danger text-nowrap">
                                    ${_('month_elec_cost')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_elec_cost')}" data-bs-content="Consumo (MW) * Horas mes * Precio Energ铆a ($/MWh)"></i>
                                </th>
                                <th class="py-3 text-danger">
                                    ${_('month_opex')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_opex')}" data-bs-content="Gastos operativos fijos: Personal, Servicios, Seguros, Mantenimiento, etc."></i>
                                </th>
                                <th class="py-3">
                                    ${_('month_ebitda')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_ebitda')}" data-bs-content="Total Revenue - Electric Cost - OPEX Cost"></i>
                                </th>
                                <th class="py-3 fw-bold">
                                    ${_('month_net_profit')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_net_profit')}" data-bs-content="Resultado neto despu茅s de todos los costos operativos antes de impuestos e intereses financieros."></i>
                                </th>
                                <th class="py-3">
                                    ${_('month_margin')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_margin')}" data-bs-content="Net Profit / Total Revenue"></i>
                                </th>
                                <th class="py-3">
                                    ${_('month_cost_btc')}
                                    <i class="bi bi-info-circle ms-1 small opacity-75" role="button" data-bs-toggle="popover" title="${_('month_cost_btc')}" data-bs-content="(Elec cost + OPEX cost) / BTC Producidos"></i>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    data.forEach((m, idx) => {
        const priceVal = document.getElementsByName(`monthly_price_var_${idx + 1}`)[0]?.value || m.price_variation || 0;
        const diffVal = document.getElementsByName(`monthly_diff_var_${idx + 1}`)[0]?.value || m.difficulty_variation || 0;

        html += `
            <tr class="${m.halving_month ? 'table-warning' : ''}">
                <td class="text-center fw-bold bg-light">M${m.month}</td>
                <td class="text-end font-monospace">$${formatDisplayCurrency(m.btc_price)}</td>
                <td class="text-center" style="width: 100px;">
                    <div class="input-group input-group-sm">
                        <input type="number" step="0.1" class="form-control text-center py-0" 
                            name="monthly_price_var_${m.month}" 
                            value="${priceVal}" 
                            oninput="event.stopPropagation()"
                            onchange="event.stopPropagation(); debouncedCalculateResults()"
                            style="font-size: 0.8rem; height: 24px;">
                        <span class="input-group-text py-0" style="font-size: 0.7rem;">%</span>
                    </div>
                </td>
                <td class="text-end font-monospace small">${formatDifficulty(m.difficulty)}</td>
                <td class="text-center" style="width: 100px;">
                    <div class="input-group input-group-sm">
                        <input type="number" step="0.1" class="form-control text-center py-0" 
                            name="monthly_diff_var_${m.month}" 
                            value="${diffVal}" 
                            oninput="event.stopPropagation()"
                            onchange="event.stopPropagation(); debouncedCalculateResults()"
                            style="font-size: 0.8rem; height: 24px;">
                        <span class="input-group-text py-0" style="font-size: 0.7rem;">%</span>
                    </div>
                </td>
                <td class="text-end font-monospace">${m.btc_generated.toFixed(4)}</td>
                <td class="text-end font-monospace">$${formatDisplayCurrency(m.usd_revenue)}</td>
                <td class="text-end font-monospace text-success">+$${formatDisplayCurrency(m.other_income)}</td>
                <td class="text-end font-monospace fw-bold">$${formatDisplayCurrency(m.total_revenue)}</td>
                <td class="text-end font-monospace text-danger">-$${formatDisplayCurrency(m.electricity_cost)}</td>
                <td class="text-end font-monospace text-danger">-$${formatDisplayCurrency(m.opex_cost)}</td>
                <td class="text-end font-monospace">$${formatDisplayCurrency(m.ebitda)}</td>
                <td class="text-end font-monospace fw-bold ${m.net_profit > 0 ? 'text-success' : 'text-danger'}">$${formatDisplayCurrency(m.net_profit)}</td>
                <td class="text-center">
                    <span class="badge ${m.operating_margin > 20 ? 'bg-success' : (m.operating_margin > 0 ? 'bg-warning text-dark' : 'bg-danger')}">
                        ${m.operating_margin.toFixed(0)}%
                    </span>
                </td>
                <td class="text-end font-monospace text-primary fw-bold">$${formatDisplayCurrency(m.cost_per_btc)}</td>
            </tr>
        `;
    });

    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Duplicated Inputs: Electricity & ASICs -->
        <div class="row g-3 mb-4" id="md_duplicated_inputs_container">
            ${renderDuplicatedInputs()}
        </div>
    `;

    // ── Input Summary Sections BELOW table ──
    html += renderMonthlySummarySections(results);

    container.innerHTML = html;

    // Initialize popovers for the newly added headers
    if (typeof initPopovers === 'function') {
        initPopovers();
    }
}

function renderMonthlySummarySections(results) {
    let html = '';

    // ── Energy Configuration ──
    html += `
        <div class="row g-3 mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header py-2 d-flex justify-content-between align-items-center" 
                         data-bs-toggle="collapse" data-bs-target="#monthly-energy-collapse" 
                         role="button" style="cursor: pointer;">
                        <h6 class="mb-0"><i class="bi bi-lightning-charge"></i> ${_('energy_config')}</h6>
                        <span class="text-muted small">▼</span>
                    </div>
                    <div class="collapse show" id="monthly-energy-collapse">
                        <div class="card-body p-2">
                            <div class="row g-2 text-center mb-2">
                                <div class="col-4">
                                    <div class="p-2 border rounded h-100 d-flex flex-column justify-content-center">
                                        <div class="text-muted small">${_('mwh_puro')}</div>
                                        <div class="fw-bold" style="font-size: 1.3rem;">$${results.energy_cost_per_mwh_pure?.toFixed(2) || '0.00'}</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="p-2 border rounded h-100 d-flex flex-column justify-content-center">
                                        <div class="text-muted small">${_('source')}</div>
                                        <div class="text-primary fw-bold" style="font-size: 1.1rem;">${results.power_source || '-'}</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="p-2 border rounded h-100 d-flex flex-column justify-content-center">
                                        <div class="text-muted small">${_('consumption_short')}</div>
                                        <div class="fw-bold" style="font-size: 1.3rem;">${results.total_power_consumption || 0} MW</div>
                                    </div>
                                </div>
                            </div>
                            <div class="row g-2 text-center">
                                <div class="col-3">
                                    <div class="p-2 border rounded">
                                        <div class="text-muted small">${_('elec_h')}</div>
                                        <div class="fw-bold">$${results.hourly_energy_cost?.toFixed(0) || '0'}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded">
                                        <div class="text-muted small">${_('opex_fixed_h')}</div>
                                        <div class="fw-bold">$${results.hourly_opex?.toFixed(0) || '0'}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded">
                                        <div class="text-muted small">${_('total_h')}</div>
                                        <div class="text-primary fw-bold">$${results.total_hourly_cost?.toFixed(0) || '0'}</div>
                                    </div>
                                </div>
                                <div class="col-3">
                                    <div class="p-2 border rounded">
                                        <div class="text-muted small">${_('unified_opc_h')}</div>
                                        <div class="text-success fw-bold">$${results.opc_per_h?.toFixed(2) || '0.00'}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // ── ASIC Configuration ──
    let asicRows = '';
    if (results.asics && results.asics.length > 0) {
        results.asics.forEach(asic => {
            asicRows += `
                <tr>
                    <td>${asic.model}</td>
                    <td class="text-center">${asic.units}</td>
                    <td class="text-end">$${formatDisplayCurrency(asic.price)}</td>
                    <td class="text-end">${asic.hashrate}</td>
                    <td class="text-end">$${typeof asic.usd_per_th === 'number' ? asic.usd_per_th.toFixed(2) : asic.usd_per_th}</td>
                    <td class="text-end">${asic.j_per_th}</td>
                </tr>`;
        });
    }

    html += `
        <div class="card mb-4">
            <div class="card-header py-2 d-flex justify-content-between align-items-center"
                 data-bs-toggle="collapse" data-bs-target="#monthly-asic-collapse"
                 role="button" style="cursor: pointer;">
                <h6 class="mb-0"><i class="bi bi-cpu"></i> ${_('asic_config')}</h6>
                <span class="text-muted small">▼</span>
            </div>
            <div class="collapse show" id="monthly-asic-collapse">
                <div class="card-body p-2">
                    <div class="row g-2 mb-3">
                        <div class="col-4 text-center">
                            <div class="fw-bold" style="font-size: 0.9rem;">${results.total_asic_hashrate || 0}</div>
                            <div class="text-muted small">${_('total_th')}</div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="fw-bold" style="font-size: 0.9rem;">${results.total_asic_units || 0}</div>
                            <div class="text-muted small">${_('units_label')}</div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="fw-bold" style="font-size: 0.9rem;">${results.network_percentage?.toFixed(4) || '0.0000'}%</div>
                            <div class="text-muted small">${_('network_percent')}</div>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-sm table-striped mb-0" style="font-size: 0.8rem;">
                            <thead>
                                <tr>
                                    <th>${_('model_short')}</th>
                                    <th>${_('unds_short')}</th>
                                    <th>${_('price_short')}</th>
                                    <th>${_('th_s_short')}</th>
                                    <th>${_('usd_th_short')}</th>
                                    <th>${_('j_th_short')}</th>
                                </tr>
                            </thead>
                            <tbody>${asicRows}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;

    // ── CAPEX & OPEX Summary side by side ──
    let capexRows = '';
    let capexTotal = 0;
    if (results.capex_breakdown) {
        for (const [key, value] of Object.entries(results.capex_breakdown)) {
            if (key === 'Total') {
                capexTotal = value;
                continue;
            }
            capexRows += `<tr><td>${key}</td><td class="text-end">$${formatDisplayCurrency(value)}</td></tr>`;
        }
    }

    let opexSummary = results.opex_summary || {};
    html += `
        <div class="row g-3 mb-4">
            <div class="col-xl-6 col-md-12">
                <div class="card h-100">
                    <div class="card-header py-2 d-flex justify-content-between align-items-center"
                         data-bs-toggle="collapse" data-bs-target="#monthly-capex-collapse"
                         role="button" style="cursor: pointer;">
                        <h6 class="mb-0"><i class="bi bi-cash-stack"></i> ${_('capex_summary')}</h6>
                        <span class="text-muted small">▼</span>
                    </div>
                    <div class="collapse show" id="monthly-capex-collapse">
                        <div class="card-body p-2">
                            <div class="table-responsive">
                                <table class="table table-sm table-striped mb-0" style="font-size: 0.85rem;">
                                    <thead><tr><th>${_('concept')}</th><th>${_('amount_usd')}</th></tr></thead>
                                    <tbody>${capexRows}</tbody>
                                    <tfoot>
                                        <tr class="table-dark">
                                            <th>${_('total_capex')}</th>
                                            <th class="text-end">$${formatDisplayCurrency(capexTotal)}</th>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-xl-6 col-md-12">
                <div class="card h-100">
                    <div class="card-header py-2 d-flex justify-content-between align-items-center"
                         data-bs-toggle="collapse" data-bs-target="#monthly-opex-collapse"
                         role="button" style="cursor: pointer;">
                        <h6 class="mb-0"><i class="bi bi-receipt"></i> ${_('opex_summary')}</h6>
                        <span class="text-muted small">▼</span>
                    </div>
                    <div class="collapse show" id="monthly-opex-collapse">
                        <div class="card-body p-2">
                            <div class="table-responsive">
                                <table class="table table-sm table-striped mb-0" style="font-size: 0.85rem;">
                                    <thead><tr><th>${_('concept')}</th><th>${_('monthly_usd')}</th><th>${_('annual_usd')}</th></tr></thead>
                                    <tbody>
                                        <tr>
                                            <td>${_('total_staff')}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.staff_monthly || 0)}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.staff_annual || 0)}</td>
                                        </tr>
                                        <tr>
                                            <td>${_('total_services')}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.services_monthly || 0)}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.services_annual || 0)}</td>
                                        </tr>
                                        <tr>
                                            <td>${_('total_others')}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.other_monthly || 0)}</td>
                                            <td class="text-end">$${formatDisplayCurrency(opexSummary.other_annual || 0)}</td>
                                        </tr>
                                    </tbody>
                                    <tfoot>
                                        <tr class="table-dark">
                                            <th>${_('total_opex')}</th>
                                            <th class="text-end">$${formatDisplayCurrency(opexSummary.monthly_total || 0)}</th>
                                            <th class="text-end">$${formatDisplayCurrency(opexSummary.annual_total || 0)}</th>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // ── Other Incomes ──
    let otherIncomes = results.other_incomes || {};
    html += `
        <div class="card mb-4">
            <div class="card-header py-2 d-flex justify-content-between align-items-center"
                 data-bs-toggle="collapse" data-bs-target="#monthly-incomes-collapse"
                 role="button" style="cursor: pointer;">
                <h6 class="mb-0"><i class="bi bi-piggy-bank"></i> ${_('other_incomes_summary')}</h6>
                <span class="text-muted small">▼</span>
            </div>
            <div class="collapse show" id="monthly-incomes-collapse">
                <div class="card-body p-2">
                    <div class="table-responsive">
                        <table class="table table-sm mb-0" style="font-size: 0.9rem;">
                            <tbody>
                                <tr>
                                    <td class="ps-3">${_('setup_fees')}</td>
                                    <td class="text-end fw-bold">$${formatDisplayCurrency(otherIncomes.setup_fees || 0)}</td>
                                    <td class="text-muted small">${_('unique_charge_msg')}</td>
                                </tr>
                                <tr>
                                    <td class="ps-3">${_('disconnect_fees')}</td>
                                    <td class="text-end fw-bold">$${formatDisplayCurrency(otherIncomes.disconnect_fees || 0)}</td>
                                    <td class="text-muted small">${_('contract_end_msg')}</td>
                                </tr>
                                <tr>
                                    <td class="ps-3">${_('warranty_deposit')}</td>
                                    <td class="text-end fw-bold">$${formatDisplayCurrency(otherIncomes.warranty_deposit || 0)}</td>
                                    <td class="text-muted small">${_('refundable_msg')}</td>
                                </tr>
                                <tr style="background-color: rgba(25, 135, 84, 0.08);">
                                    <td class="ps-3 text-success-emphasis fw-medium">${_('monthly_interest_label')}</td>
                                    <td class="text-end text-success fw-bold">$${formatDisplayCurrency(otherIncomes.monthly_warranty_interest || 0)}</td>
                                    <td class="text-muted small">${_('recurrent_msg')}</td>
                                </tr>
                                <tr style="background-color: rgba(25, 135, 84, 0.08);">
                                    <td class="ps-3 text-success-emphasis fw-medium">${_('annual_interest_label')}</td>
                                    <td class="text-end text-success fw-bold">$${formatDisplayCurrency(otherIncomes.annual_warranty_interest || 0)}</td>
                                    <td class="text-muted small">${_('projected_msg')}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;

    return html;
}

// ==========================================
// Proxy Sync Logic for Duplicated Inputs
// ==========================================

function renderDuplicatedInputs() {
    // Read masters
    const powerSource = document.getElementById('power_source')?.value || '';
    const energyCost = document.getElementById('energy_cost_per_mwh')?.value || 0;

    // Gas values
    const gasUnit = document.getElementById('gas_unit')?.value || 'MBTU';
    const gasPrice = document.getElementById('gas_price_per_unit')?.value || 0;
    const gasKcal = document.getElementById('gas_kcal')?.value || 8500;
    const genEff = document.getElementById('generator_efficiency')?.value || 35;
    const omVal = document.getElementById('om_per_mwh')?.value || 0;

    // Read ASICs
    const asicRows = Array.from(document.querySelectorAll('#asics_tbody tr[id^="asic_row_"]'));
    let asicsHtml = '';

    // Generate inner ASIC Dropdowns like master
    const bitmain = ASIC_DATA?.filter(a => a.model.toLowerCase().includes('antminer') || a.model.includes('HOST Antminer')) || [];
    const whatsminer = ASIC_DATA?.filter(a => a.model.toLowerCase().includes('whatsminer')) || [];
    let optionsCoreHtml = '<option value="">-- Seleccionar --</option><optgroup label="BITMAIN">';
    bitmain.forEach(a => { optionsCoreHtml += `<option value="${a.model}">${a.model}</option>`; });
    optionsCoreHtml += '</optgroup><optgroup label="WHATSMINER">';
    whatsminer.forEach(a => { optionsCoreHtml += `<option value="${a.model}">${a.model}</option>`; });
    optionsCoreHtml += '</optgroup>';

    asicRows.forEach(row => {
        const idStr = row.id.replace('asic_row_', ''); // e.g. "1"
        const model = row.querySelector(`select[name="asic_model_${idStr}"]`)?.value || '';
        const units = row.querySelector(`input[name="asic_units_${idStr}"]`)?.value || 0;
        const price = row.querySelector(`input[name="asic_price_${idStr}"]`)?.value || 0;
        const hashrate = row.querySelector(`input[name="asic_hashrate_${idStr}"]`)?.value || 0;
        const consumption = row.querySelector(`input[name="asic_consumption_${idStr}"]`)?.value || 0;
        const jPerTh = row.querySelector(`input[name="asic_j_per_th_${idStr}"]`)?.value || 0;

        asicsHtml += `
            <tr id="md_asic_row_${idStr}">
                <td>
                    <select class="form-control form-control-sm" onchange="mdUpdateAsicMaster('${idStr}', 'model', this.value)">
                        ${optionsCoreHtml.replace(`value="${model}"`, `value="${model}" selected`)}
                    </select>
                </td>
                <td><input type="number" class="form-control form-control-sm" value="${units}" onkeydown="return onlyNumbers(event, false)" onchange="mdUpdateAsicMaster('${idStr}', 'units', this.value)"></td>
                <td><input type="number" class="form-control form-control-sm" value="${price}" onkeydown="return onlyNumbers(event, true)" onchange="mdUpdateAsicMaster('${idStr}', 'price', this.value)"></td>
                <td><input type="number" class="form-control form-control-sm" value="${hashrate}" onkeydown="return onlyNumbers(event, true)" onchange="mdUpdateAsicMaster('${idStr}', 'hashrate', this.value)"></td>
                <td><input type="number" class="form-control form-control-sm" value="${consumption}" onkeydown="return onlyNumbers(event, false)" onchange="mdUpdateAsicMaster('${idStr}', 'consumption', this.value)"></td>
                <td><input type="number" step="0.01" class="form-control form-control-sm" value="${jPerTh}" readonly></td>
                <td><button type="button" class="btn btn-danger btn-sm" onclick="mdRemoveAsicMaster('${idStr}')"><i class="bi bi-trash"></i></button></td>
            </tr>
        `;
    });

    let html = `
        <div class="col-md-4">
            <div class="card shadow-sm border-0" style="background: var(--bs-tertiary-bg);">
                <div class="card-header border-bottom excel-sub-header d-flex justify-content-between align-items-center">
                    <span>${_('electricity')} (Quick Edit)</span>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label x-small">${_('power_source')}</label>
                        <select class="form-select form-select-sm" id="md_power_source" onchange="mdSyncGeneralMaster('power_source', this.value, true)">
                            <option value="" ${powerSource === '' ? 'selected' : ''}>--select--</option>
                            <option value="Direct Energy" ${powerSource === 'Direct Energy' ? 'selected' : ''}>${_('direct_energy')}</option>
                            <option value="Gas powered" ${powerSource === 'Gas powered' ? 'selected' : ''}>${_('gas_powered')}</option>
                        </select>
                    </div>
    `;

    if (powerSource === 'Direct Energy') {
        html += `
                    <div class="mb-3">
                        <label class="form-label x-small">Energy Cost ($/MWh)</label>
                        <input type="number" step="0.01" class="form-control form-control-sm" value="${energyCost}" onchange="mdSyncGeneralMaster('energy_cost_per_mwh', this.value)">
                    </div>
        `;
    } else if (powerSource === 'Gas powered') {
        html += `
                    <div class="row g-2">
                        <div class="col-6 mb-2">
                            <label class="form-label x-small">Gas Unit</label>
                            <select class="form-select form-select-sm" onchange="mdSyncGeneralMaster('gas_unit', this.value)">
                                <option value="MBTU" ${gasUnit === 'MBTU' ? 'selected' : ''}>MBTU</option>
                                <option value="M3" ${gasUnit === 'M3' ? 'selected' : ''}>M3</option>
                            </select>
                        </div>
                        <div class="col-6 mb-2">
                            <label class="form-label x-small">Gas Price</label>
                            <input type="number" step="0.01" class="form-control form-control-sm" value="${gasPrice}" onchange="mdSyncGeneralMaster('gas_price_per_unit', this.value)">
                        </div>
                        <div class="col-6 mb-2">
                            <label class="form-label x-small">Gas kCal</label>
                            <input type="number" class="form-control form-control-sm" value="${gasKcal}" onchange="mdSyncGeneralMaster('gas_kcal', this.value)">
                        </div>
                        <div class="col-6 mb-2">
                            <label class="form-label x-small">Eff. (%)</label>
                            <input type="number" step="0.01" class="form-control form-control-sm" value="${genEff}" onchange="mdSyncGeneralMaster('generator_efficiency', this.value)">
                        </div>
                        <div class="col-12">
                            <label class="form-label x-small">O&M ($/MWh)</label>
                            <input type="number" step="0.01" class="form-control form-control-sm" value="${omVal}" onchange="mdSyncGeneralMaster('om_per_mwh', this.value)">
                        </div>
                    </div>
        `;
    }

    html += `
                </div>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card shadow-sm border-0" style="background: var(--bs-tertiary-bg);">
                <div class="card-header border-bottom excel-sub-header d-flex justify-content-between align-items-center">
                    <span>${_('asics_details')} (Quick Edit)</span>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered mb-0 align-middle" style="font-size: 0.85rem;">
                            <thead class="table-dark text-center">
                                <tr>
                                    <th>${_('model')}</th>
                                    <th style="width: 80px;">${_('units')}</th>
                                    <th style="width: 90px;">${_('price')}</th>
                                    <th style="width: 80px;">${_('hashrate')}</th>
                                    <th style="width: 80px;">Watts</th>
                                    <th style="width: 80px;">J/TH</th>
                                    <th style="width: 40px;"></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${asicsHtml}
                            </tbody>
                        </table>
                    </div>
                    <div class="p-2 border-top bg-light text-end">
                        <button class="btn btn-sm btn-primary" onclick="mdAddAsicMaster()">${_('add_asic') || '+ Add ASIC'}</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    return html;
}

// Proxies to update master elements
function mdSyncGeneralMaster(elemId, val, isPowerSource = false) {
    const masterEl = document.getElementById(elemId);
    if (masterEl) {
        masterEl.value = val;

        if (isPowerSource && typeof togglePowerSource === 'function') {
            togglePowerSource(); // This will regenerate the master gas fields
        }

        if (typeof debouncedCalculateResults === 'function') {
            debouncedCalculateResults(); // This recalculates and ultimately re-renders this dashboard
        } else {
            // Fallback: manually update dashboard HTML
            reloadDuplicatedInputs();
        }
    }
}

function mdUpdateAsicMaster(idStr, field, val) {
    const selector = `[name="asic_${field}_${idStr}"]`;
    const masterField = document.querySelector(`#asic_row_${idStr} ${selector}`);
    if (masterField) {
        masterField.value = val;

        // Trigger master event handlers natively so all side effects run
        if (field === 'model') {
            masterField.dispatchEvent(new Event('change'));
        } else if (field === 'units') {
            masterField.dispatchEvent(new Event('change'));
        } else {
            if (typeof updateAsicRowMetrics === 'function') updateAsicRowMetrics(idStr);
            if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
        }
    }
}

function mdAddAsicMaster() {
    if (typeof addAsicRow === 'function') {
        addAsicRow();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
        reloadDuplicatedInputs();
    }
}

function mdRemoveAsicMaster(idStr) {
    if (typeof removeAsicRow === 'function') {
        removeAsicRow(idStr);
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
        reloadDuplicatedInputs();
    }
}

function reloadDuplicatedInputs() {
    const container = document.getElementById('md_duplicated_inputs_container');
    if (container) {
        container.innerHTML = renderDuplicatedInputs();
    }
}
