function calculateResults(callback) {
    const form = document.querySelector('form');
    const formData = new FormData(form);

    // Clean formatted price and difficulty inputs before sending
    for (let [key, value] of formData.entries()) {
        if (key.includes('manual_price_') || key.includes('backlog_price_') || key.includes('manual_diff_var_')) {
            formData.set(key, parseDisplayCurrency(value));
        }
    }

    fetch('/calculate', {
        method: 'POST',
        body: formData
    })
        .then(response => response.text())
        .then(html => {
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.innerHTML = html;
            }
            if (typeof initPopovers === 'function') initPopovers();

            // Always try to render dashboard if the element exists
            if (typeof renderDashboard === 'function') {
                renderDashboard();
            }

            if (typeof renderMonthlyDashboard === 'function' && document.getElementById('monthly-dashboard-tab').classList.contains('active')) {
                renderMonthlyDashboard();
            }

            if (typeof callback === 'function') callback();
        })
        .catch(error => console.error('Error:', error));
}

function calculateGasPrice() {
    const gasPricePerUnitEl = document.getElementById('gas_price_per_unit');
    const gasKcalEl = document.getElementById('gas_kcal');
    const generatorEfficiencyEl = document.getElementById('generator_efficiency');
    const gasUnitEl = document.getElementById('gas_unit');
    const gasPricePerMwhEl = document.getElementById('gas_price_per_mwh');

    if (!gasPricePerUnitEl || !gasKcalEl || !generatorEfficiencyEl || !gasUnitEl || !gasPricePerMwhEl) return;

    const gasPricePerUnit = parseFloat(gasPricePerUnitEl.value) || 0;
    const gasKcal = parseFloat(gasKcalEl.value) || 8500;
    const generatorEfficiency = parseFloat(generatorEfficiencyEl.value) || 35;
    const unit = gasUnitEl.value;
    const standardKcal = 8500;
    const baseMbtuPerMwh = 3.412;
    let gasPricePerMwh;

    if (unit === 'MBTU') {
        gasPricePerMwh = (gasPricePerUnit * baseMbtuPerMwh) / (gasKcal / standardKcal) / (generatorEfficiency / 100);
    } else { // M3
        // Assuming 1 M3 = 10 MBTU approximately, but this might need adjustment
        const mbtuPerM3 = 10; // Placeholder, adjust as needed
        gasPricePerMwh = (gasPricePerUnit * mbtuPerM3 * baseMbtuPerMwh) / (gasKcal / standardKcal) / (generatorEfficiency / 100);
    }
    gasPricePerMwhEl.value = gasPricePerMwh.toFixed(2);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedCalculateResults = debounce(() => {
    calculateResults(() => {
        // If Benchmarks tab is active, re-render after calculation to ensure fresh energy costs
        if (document.getElementById('benchmarks-tab')?.classList.contains('active')) {
            if (typeof renderBenchmarks === 'function') renderBenchmarks();
        }
    });
}, 500);
