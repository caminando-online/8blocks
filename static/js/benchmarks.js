let benchmarkSortKey = 'score';
let benchmarkSortDesc = true;

function renderBenchmarks() {
    const tbody = document.getElementById('benchmarks-tbody');
    if (!tbody) return;

    // Get current values from the Calculator tab safely
    const btcPriceEl = document.getElementById('btc_price_override');
    const valBtcPriceEl = document.getElementById('val_btc_price');
    const btcPrice = parseFloat(btcPriceEl?.value) || parseFloat(valBtcPriceEl?.dataset.raw) || parseDisplayCurrency(valBtcPriceEl?.innerText) || 90000;

    const diffOverrideEl = document.getElementById('difficulty_override');
    const valDifficultyEl = document.getElementById('val_difficulty');
    const difficulty = parseFloat(diffOverrideEl?.value) || parseDisplayCurrency(valDifficultyEl?.innerText) || 84000000000000;

    // Get energy cost from results if available (OPC/h includes OPEX), else fallback to inputs
    const opcPerHVal = document.getElementById('val_opc_per_h');
    let energyCostKwh = 0;

    if (opcPerHVal) {
        // OPC/h is already in $/MWh
        energyCostKwh = parseDisplayCurrency(opcPerHVal.innerText) / 1000;
    } else {
        const energyMwh = parseFloat(document.getElementById('energy_cost_per_mwh')?.value) || 0;
        const gasMwh = parseFloat(document.getElementById('gas_price_per_mwh')?.value) || 0;
        energyCostKwh = (energyMwh || gasMwh || 0) / 1000;
    }

    // Daily production BTC/TH
    const blockReward = 3.125;
    const btcPerThDay = (1e12 * 86400) / (difficulty * Math.pow(2, 32)) * blockReward;

    // Filter by selected models if toggle is on
    const filterSelected = document.getElementById('filter-selected-only')?.checked;
    let filteredAsics = ASIC_DATA;

    if (filterSelected) {
        const selectedModels = new Set();
        document.querySelectorAll('#asics_tbody tr[id^="asic_row_"] select').forEach(s => {
            if (s.value) selectedModels.add(s.value);
        });
        filteredAsics = ASIC_DATA.filter(a => selectedModels.has(a.model));
    }

    if (!filteredAsics || filteredAsics.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center">${filterSelected ? 'No hay modelos seleccionados en la calculadora' : 'No hay datos de ASICs disponibles'}</td></tr>`;
        return;
    }

    let data = filteredAsics.map(originalAsic => {
        let asic = { ...originalAsic };
        let modifiedFields = { price: false, hashrate: false, consumption: false };

        const override = ASIC_OVERRIDES[asic.model];
        if (override) {
            if (override.price !== null) { asic.price = override.price; modifiedFields.price = true; }
            if (override.hashrate !== null) { asic.hashrate = override.hashrate; modifiedFields.hashrate = true; }
            if (override.consumption !== null) { asic.consumption = override.consumption; modifiedFields.consumption = true; }
        }

        const dailyBtc = asic.hashrate * btcPerThDay;
        const dailyUsd = dailyBtc * btcPrice;
        const dailyEnergyKwh = (asic.consumption / 1000) * 24;
        const dailyEnergyCost = dailyEnergyKwh * energyCostKwh;
        const profitDaily = dailyUsd - dailyEnergyCost;

        // MWh Calculations
        const asicsPerMwh = asic.consumption > 0 ? (1000000 / asic.consumption) : 0;
        const revenueMwh = asicsPerMwh * dailyUsd / 24; // $/MWh = (ASICs * DailyUSD) / 24h

        const payback = profitDaily > 0 ? (asic.price / (profitDaily * 30.41)) : 999;
        const efficiency = asic.consumption / asic.hashrate;
        const usdPerTh = asic.price / asic.hashrate;

        return {
            ...asic,
            efficiency,
            usdPerTh,
            revenueMwh,
            profitDaily,
            payback,
            modifiedFields,
            score: 0 // Will calculate after
        };
    });

    // Scoring Algorithm
    const minEff = Math.min(...data.map(d => d.efficiency));
    const maxEff = Math.max(...data.map(d => d.efficiency));
    const minUsdTh = Math.min(...data.map(d => d.usdPerTh));
    const maxUsdTh = Math.max(...data.map(d => d.usdPerTh));
    const minPayback = Math.min(...data.map(d => d.payback));
    const maxPayback = Math.max(...data.map(d => d.payback));
    const maxRevMwh = Math.max(...data.map(d => d.revenueMwh));

    data = data.map(d => {
        const sEff = 100 * (1 - (d.efficiency - minEff) / (maxEff - minEff || 1));
        const sUsd = 100 * (1 - (d.usdPerTh - minUsdTh) / (maxUsdTh - minUsdTh || 1));
        const sPay = d.payback === 999 ? 0 : 100 * (1 - (d.payback - minPayback) / (maxPayback - minPayback || 1));
        const sMwh = 100 * (d.revenueMwh / (maxRevMwh || 1));

        d.score = Math.round((sEff * 0.35) + (sUsd * 0.25) + (sPay * 0.25) + (sMwh * 0.15));
        return d;
    });

    // Sorting
    data.sort((a, b) => {
        let valA = a[benchmarkSortKey];
        let valB = b[benchmarkSortKey];

        if (valA === undefined || valA === null) valA = 0;
        if (valB === undefined || valB === null) valB = 0;

        let comparison = 0;
        if (valA > valB) comparison = 1;
        else if (valA < valB) comparison = -1;

        if (comparison === 0) {
            comparison = a.model.localeCompare(b.model);
        }

        return benchmarkSortDesc ? (comparison * -1) : comparison;
    });

    const scoresSorted = [...data].sort((a, b) => b.score - a.score);
    const topThreshold = scoresSorted[Math.floor(scoresSorted.length * 0.15)]?.score || 999;

    const activeEl = document.activeElement;
    const activeId = activeEl ? activeEl.id : null;
    const selectionStart = activeEl ? activeEl.selectionStart : null;
    const selectionEnd = activeEl ? activeEl.selectionEnd : null;

    const currentlyInCalc = new Set();
    document.querySelectorAll('#asics_tbody tr[id^="asic_row_"] select').forEach(s => {
        if (s.value) currentlyInCalc.add(s.value);
    });

    const masterCheckbox = document.getElementById('benchmark-select-all');
    if (masterCheckbox) {
        const allSelected = data.every(d => currentlyInCalc.has(d.model));
        const someSelected = data.some(d => currentlyInCalc.has(d.model));
        masterCheckbox.checked = allSelected && data.length > 0;
        masterCheckbox.indeterminate = someSelected && !allSelected;
    }

    tbody.innerHTML = data.map(d => {
        const priceIndicator = d.modifiedFields.price ? `<span class="modified-indicator" data-bs-toggle="popover" data-bs-content="El precio ha sido modificado manualmente.">Mod</span>` : '';
        const hashrateIndicator = d.modifiedFields.hashrate ? `<span class="modified-indicator" data-bs-toggle="popover" data-bs-content="El hashrate ha sido modificado manualmente.">Mod</span>` : '';
        const consumptionIndicator = d.modifiedFields.consumption ? `<span class="modified-value"><span>${d.efficiency.toFixed(2)} (J/TH)</span><span class="modified-indicator" data-bs-toggle="popover" data-bs-content="El consumo ha sido modificado manualmente en la sección de detalles.">Mod</span></span>` : `<span>${d.efficiency.toFixed(2)} (J/TH)</span>`;

        const modelSafe = d.model.replace(/[^a-z0-9]/gi, '_');
        const priceInputId = `benchmark_price_${modelSafe}`;
        const hashrateInputId = `benchmark_hashrate_${modelSafe}`;

        const isChecked = currentlyInCalc.has(d.model) ? 'checked' : '';

        return `
            <tr class="${d.score >= topThreshold ? 'table-success' : ''}">
                <td class="text-center">
                    <input class="form-check-input" type="checkbox" ${isChecked} 
                           onchange="toggleAsicFromBenchmark('${d.model.replace(/'/g, "\\'")}', this.checked)">
                </td>
                <td>
                    <strong>${d.model}</strong>
                    ${d.score >= topThreshold ? '<span class="badge bg-success ms-1">Best Choice</span>' : ''}
                </td>
                <td class="text-center"><span class="badge ${d.cooling === 'Air' ? 'bg-info' : (d.cooling === 'Hydro' ? 'bg-primary' : 'bg-secondary')}">${d.cooling}</span></td>
                <td class="text-center">
                    <div class="modified-value">
                        <span class="currency-prefix">$</span>
                        <input type="number" class="benchmark-input price" id="${priceInputId}" value="${d.price}" 
                               onkeydown="return onlyNumbers(event, true)"
                               onchange="updateBenchmarkOverride('${d.model.replace(/'/g, "\\'")}', 'price', this.value)">
                        ${priceIndicator}
                    </div>
                </td>
                <td class="text-center">
                    <div class="modified-value">
                        <input type="number" class="benchmark-input hashrate" id="${hashrateInputId}" value="${d.hashrate}" 
                               onkeydown="return onlyNumbers(event, true)"
                               onchange="updateBenchmarkOverride('${d.model.replace(/'/g, "\\'")}', 'hashrate', this.value)">
                        <span class="unit-suffix">TH/s</span>
                        ${hashrateIndicator}
                    </div>
                </td>
                <td class="text-center">${consumptionIndicator}</td>
                <td class="text-center">$${d.usdPerTh.toFixed(2)}</td>
                <td class="text-center">$${formatDisplayCurrency(d.revenueMwh)}</td>
                <td class="text-center ${d.profitDaily > 0 ? 'text-success' : 'text-danger'}">
                    $${formatDisplayCurrency(d.profitDaily)}
                </td>
                <td class="text-center">${d.payback > 100 ? '>100' : d.payback.toFixed(1)}</td>
                <td class="text-center">
                    <div class="d-flex align-items-center">
                        <div class="progress flex-grow-1 me-2" style="height: 10px;">
                            <div class="progress-bar ${d.score > 80 ? 'bg-success' : d.score > 50 ? 'bg-warning' : 'bg-danger'}" 
                                 role="progressbar" style="width: ${d.score}%"></div>
                        </div>
                        <span class="fw-bold">${d.score}</span>
                    </div>
                </td>
            </tr>
        `}).join('');

    if (activeId) {
        const newActiveEl = document.getElementById(activeId);
        if (newActiveEl) {
            newActiveEl.focus();
            if (selectionStart !== null && selectionEnd !== null) {
                try {
                    newActiveEl.setSelectionRange(selectionStart, selectionEnd);
                } catch (e) { }
            }
        }
    }

    updateScoringPopover();
    if (typeof initPopovers === 'function') initPopovers();
}

function sortBenchmarks(key) {
    if (benchmarkSortKey === key) {
        benchmarkSortDesc = !benchmarkSortDesc;
    } else {
        benchmarkSortKey = key;
        benchmarkSortDesc = true;
    }
    renderBenchmarks();
}

function updateBenchmarkOverride(model, field, value) {
    const original = ASIC_DATA.find(a => a.model === model);
    if (!original) return;

    const numValue = parseFloat(value) || 0;

    if (!ASIC_OVERRIDES[model]) {
        ASIC_OVERRIDES[model] = { price: null, hashrate: null, consumption: null };
    }

    if (Math.abs(numValue - original[field]) > 0.01) {
        ASIC_OVERRIDES[model][field] = numValue;
    } else {
        ASIC_OVERRIDES[model][field] = null;
    }

    syncBenchmarkToDetails(model, field, numValue);
    renderBenchmarks();
}

function syncBenchmarkToDetails(model, field, value) {
    const allRows = document.querySelectorAll('#asics_tbody tr[id^="asic_row_"]');
    allRows.forEach(r => {
        const rModel = r.querySelector('select').value;
        if (rModel === model) {
            const input = r.querySelector(`input[name*="${field}"]`);
            if (input && Math.abs(parseFloat(input.value) - value) > 0.01) {
                input.value = value;
                const id = r.id.split('_').pop();
                const price = parseFloat(r.querySelector(`input[name="asic_price_${id}"]`).value) || 0;
                const hashrate = parseFloat(r.querySelector(`input[name="asic_hashrate_${id}"]`).value) || 0;
                const consumption = parseFloat(r.querySelector(`input[name="asic_consumption_${id}"]`).value) || 0;
                r.querySelector(`input[name="asic_usd_per_th_${id}"]`).value = hashrate > 0 ? (price / hashrate).toFixed(2) : 0;
                r.querySelector(`input[name="asic_j_per_th_${id}"]`).value = hashrate > 0 ? (consumption / hashrate).toFixed(2) : 0;
            }
        }
    });
    if (typeof updateAsicsTotal === 'function') updateAsicsTotal();
}

function toggleAsicFromBenchmark(model, checked) {
    if (checked) {
        if (typeof addAsicRow === 'function') addAsicRow(model);
    } else {
        const allRows = document.querySelectorAll('#asics_tbody tr[id^="asic_row_"]');
        let removed = false;
        allRows.forEach(r => {
            const select = r.querySelector('select');
            if (select && select.value === model) {
                r.remove();
                removed = true;
            }
        });

        if (removed) {
            if (typeof updateAsicsTotal === 'function') updateAsicsTotal();
            if (document.getElementById('filter-selected-only')?.checked) {
                renderBenchmarks();
            }
        }
    }
}

function toggleAllBenchmarks(checked) {
    const tbody = document.getElementById('benchmarks-tbody');
    const checkboxes = tbody?.querySelectorAll('input[type="checkbox"]');
    checkboxes?.forEach(cb => {
        if (cb.checked !== checked) {
            cb.checked = checked;
            cb.dispatchEvent(new Event('change'));
        }
    });
}

function resetAsicOverrides() {
    if (Object.keys(ASIC_OVERRIDES).length === 0) return;

    if (confirm('¿Estás seguro de que deseas volver a los valores originales del catálogo? Se borrarán todas las modificaciones manuales.')) {
        for (let model in ASIC_OVERRIDES) {
            const original = ASIC_DATA.find(a => a.model === model);
            if (original) {
                syncBenchmarkToDetails(model, 'price', original.price);
                syncBenchmarkToDetails(model, 'hashrate', original.hashrate);
                syncBenchmarkToDetails(model, 'consumption', original.consumption);
            }
        }
        for (let key in ASIC_OVERRIDES) delete ASIC_OVERRIDES[key];
        renderBenchmarks();
        if (typeof debouncedCalculateResults === 'function') debouncedCalculateResults();
    }
}

function updateScoringPopover() {
    const popoverContent = `
        <div class="small">
            <p>El score (0-100) pondera los siguientes factores:</p>
            <ul>
                <li><strong>Eficiencia (35%):</strong> J/TH (Menos es mejor). Protege contra el Halving.</li>
                <li><strong>Costo Capital (25%):</strong> $/TH (Menos es mejor).</li>
                <li><strong>Payback (25%):</strong> Meses para recuperar inversión.</li>
                <li><strong>Infraestructura (15%):</strong> USD generado por cada MWh.</li>
            </ul>
        </div>
    `;
    const popoverEl = document.getElementById('scoring-popover');
    if (popoverEl) {
        const existing = bootstrap.Popover.getInstance(popoverEl);
        if (existing) existing.dispose();
        new bootstrap.Popover(popoverEl, {
            content: popoverContent,
            html: true,
            trigger: 'hover',
            placement: 'left'
        });
    }
}
