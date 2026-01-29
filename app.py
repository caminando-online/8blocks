from flask import Flask, render_template, request, send_file
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from io import BytesIO
import os

app = Flask(__name__)

def safe_float(value, default=0):
    try:
        return float(value) if value else default
    except ValueError:
        return default

# Placeholder for API data fetching
def get_btc_price():
    try:
        # Try CoinGecko first
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get('bitcoin', {}).get('usd')
        if price:
            return price
    except Exception as e:
        print(f"CoinGecko failed: {e}")
    
    try:
        # Fallback to Binance
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Binance failed: {e}")
        return 95000  # fallback price

def get_network_difficulty():
    try:
        response = requests.get('https://blockchain.info/q/getdifficulty', timeout=10)
        response.raise_for_status()
        return float(response.text)
    except Exception as e:
        print(f"Error fetching difficulty: {e}")
        return 100000000000000  # fallback

def get_current_block():
    try:
        response = requests.get('https://blockchain.info/q/getblockcount', timeout=10)
        response.raise_for_status()
        return int(response.text)
    except Exception as e:
        print(f"Error fetching block count: {e}")
        return 850000  # fallback

def get_historical_difficulty():
    try:
        response = requests.get('https://api.blockchain.info/charts/difficulty?timespan=4years&format=json', timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('values', [])
    except Exception as e:
        print(f"Error fetching historical difficulty: {e}")
        return []

def calculate_avg_monthly_difficulty_change(values, months=12):
    # values: list of {'x': unix timestamp, 'y': difficulty}
    # Group by month, get first and last difficulty per month
    from datetime import datetime
    monthly = {}
    for v in values:
        dt = datetime.fromtimestamp(v['x'])
        key = (dt.year, dt.month)
        if key not in monthly:
            monthly[key] = {'start': v['y'], 'end': v['y']}
        else:
            monthly[key]['end'] = v['y']
    
    # Get last 'months' months
    sorted_keys = sorted(monthly.keys(), reverse=True)[:months]
    changes = []
    for key in sorted_keys:
        start = monthly[key]['start']
        end = monthly[key]['end']
        if start > 0:
            change = (end - start) / start * 100
            changes.append(change)
    
    if changes:
        return sum(changes) / len(changes)
    return 0

# Calculation functions (placeholders)
def calculate_roi(investment_usd, total_profits_usd):
    return (total_profits_usd / investment_usd) * 100 if investment_usd > 0 else 0

def simulate_mining(investment_usd, hashrate_th, energy_cost_per_kwh, btc_price, difficulty, asic_efficiency, depreciation_years, depreciation_method, operational_costs, downtime_percent, years=8):
    # Simplified simulation
    # Adjust for downtime
    effective_hashrate = hashrate_th * (1 - downtime_percent / 100)
    
    # Power consumption based on efficiency
    power_watts = effective_hashrate * asic_efficiency  # J/TH = W/TH
    daily_power_kwh = (power_watts / 1000) * 24
    daily_cost = daily_power_kwh * energy_cost_per_kwh
    
    # Daily BTC reward
    daily_btc = (effective_hashrate * 1e12 / difficulty) * 144 * 3.12
    daily_usd = daily_btc * btc_price
    
    daily_profit_usd = daily_usd - daily_cost - (operational_costs / 365)
    
    annual_profit_usd = daily_profit_usd * 365
    total_profits_usd = annual_profit_usd * years
    
    # Depreciation
    if depreciation_method == 'linear':
        annual_depreciation = investment_usd / depreciation_years
    else:  # declining
        annual_depreciation = investment_usd * 0.3  # simplified
    
    roi = calculate_roi(investment_usd, total_profits_usd)
    return {
        'daily_btc': daily_btc,
        'daily_usd': daily_usd,
        'daily_cost': daily_cost,
        'annual_profit_usd': annual_profit_usd,
        'total_profits_usd': total_profits_usd,
        'annual_depreciation': annual_depreciation,
        'roi': roi
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    # Fetch real-time data
    btc_price = get_btc_price()
    difficulty = get_network_difficulty()
    current_block = get_current_block()
    next_halving_block = ((current_block // 210000) + 1) * 210000
    blocks_to_halving = next_halving_block - current_block
    months_to_halving = blocks_to_halving / (144 * 30)  # Approximate: 144 blocks/day * 30 days/month

    # Historical difficulty changes
    hist_diff = get_historical_difficulty()
    avg_change_6m = calculate_avg_monthly_difficulty_change(hist_diff, 6)
    avg_change_12m = calculate_avg_monthly_difficulty_change(hist_diff, 12)
    avg_change_24m = calculate_avg_monthly_difficulty_change(hist_diff, 24)
    avg_change_36m = calculate_avg_monthly_difficulty_change(hist_diff, 36)
    avg_change_48m = calculate_avg_monthly_difficulty_change(hist_diff, 48)

    if request.method == 'POST':
        # Get CAPEX
        research = safe_float(request.form.get('research'))
        asics_unit_value = safe_float(request.form.get('asics_unit_value'))
        shelter = safe_float(request.form.get('shelter'))
        generator = safe_float(request.form.get('generator'))
        infrastructure = safe_float(request.form.get('infrastructure'))
        general_expenses = safe_float(request.form.get('general_expenses'))
        other_capex_total = 0
        other_capex_breakdown = {}
        for i in range(1, 21):  # Assume up to 20 others
            value = request.form.get(f'other_capex_{i}')
            name = request.form.get(f'other_capex_name_{i}')
            if value and name:
                val = safe_float(value)
                other_capex_total += val
                other_capex_breakdown[name] = val
        investment_usd = research + asics_unit_value + shelter + generator + infrastructure + general_expenses + other_capex_total

        # Collect ASIC table data
        asics = []
        total_hashrate = 0
        total_cost = 0
        for i in range(1, 21):  # Assume up to 20 rows
            model = request.form.get(f'asic_model_{i}')
            if model:
                units = int(safe_float(request.form.get(f'asic_units_{i}')))
                price = safe_float(request.form.get(f'asic_price_{i}'))
                hashrate = safe_float(request.form.get(f'asic_hashrate_{i}'))
                consumption = safe_float(request.form.get(f'asic_consumption_{i}'))
                asics.append({
                    'model': model,
                    'units': units,
                    'price': price,
                    'hashrate': hashrate,
                    'consumption': consumption
                })
                total_hashrate += hashrate * units
                total_cost += price * units
        hashrate_th = total_hashrate
        # Get Electricity
        power_source = request.form.get('power_source', 'Direct Energy')
        if power_source == 'Direct Energy':
            energy_cost_per_mwh = safe_float(request.form.get('energy_cost_per_mwh'))
            energy_cost_per_kwh = energy_cost_per_mwh / 1000
        else:
            gas_price_per_mwh = safe_float(request.form.get('gas_price_per_mwh'))
            energy_cost_per_kwh = gas_price_per_mwh / 1000
        hardware_type = request.form.get('hardware_type', 'Air')
        manufacturer = request.form.get('manufacturer', '')
        model = request.form.get('model', '')
        location = request.form.get('location', 'Neuquen')
        expansion_10mw = request.form.get('expansion_10mw', 'no') == 'yes'
        expansion_40mw = request.form.get('expansion_40mw', 'no') == 'yes'
        financing_rate = safe_float(request.form.get('financing_rate'))
        downtime_percent = safe_float(request.form.get('downtime_percent'))
        btc_price_override = request.form.get('btc_price_override')
        depreciation_years = int(safe_float(request.form.get('depreciation_years'), 3))
        depreciation_method = request.form.get('depreciation_method', 'linear')
        operational_costs = safe_float(request.form.get('operational_costs'))

        # Get OPEX
        # Staff
        staff_total = 0
        staff_breakdown = {}
        for i in range(1, 21):  # Assume up to 20 staff
            value = request.form.get(f'staff_{i}')
            name = request.form.get(f'staff_name_{i}')
            if value and name:
                val = safe_float(value)
                staff_total += val
                staff_breakdown[name] = val * 12  # Annual

        # Services
        insurance = safe_float(request.form.get('insurance'))
        software = safe_float(request.form.get('software'))
        internet = safe_float(request.form.get('internet'))
        security = safe_float(request.form.get('security'))
        accounting = safe_float(request.form.get('accounting'))
        lawyer = safe_float(request.form.get('lawyer'))
        services_total = insurance + software + internet + security + accounting + lawyer
        services_breakdown = {
            'Insurance': insurance * 12,
            'Software': software * 12,
            'Internet': internet * 12,
            'Security': security * 12,
            'Accounting': accounting * 12,
            'Lawyer': lawyer * 12
        }
        for i in range(1, 21):  # Dynamic services
            value = request.form.get(f'service_{i}')
            name = request.form.get(f'service_name_{i}')
            if value and name:
                val = safe_float(value)
                services_total += val
                services_breakdown[name] = val * 12

        # Others
        downtime_percent = safe_float(request.form.get('downtime_percent'))
        operational_costs = safe_float(request.form.get('operational_costs'))
        other_opex_total = operational_costs
        other_opex_breakdown = {
            'Additional Operational Costs': operational_costs * 12
        }
        for i in range(1, 21):  # Dynamic others
            value = request.form.get(f'other_opex_{i}')
            name = request.form.get(f'other_opex_name_{i}')
            if value and name:
                val = safe_float(value)
                other_opex_total += val
                other_opex_breakdown[name] = val * 12

        total_opex_annual = (staff_total + services_total + other_opex_total) * 12

        # Fetch or override BTC price
        btc_price = float(btc_price_override) if btc_price_override else btc_price
        # difficulty already fetched

        # Run simulation
        results = simulate_mining(investment_usd, hashrate_th, energy_cost_per_kwh, btc_price, difficulty, 30, depreciation_years, depreciation_method, total_opex_annual, downtime_percent)

        # Add CAPEX breakdown to results
        results['capex_breakdown'] = {
            'Research': research,
            'ASICs': asics_unit_value,
            'Shelter': shelter,
            'Generator': generator,
            'Infrastructure': infrastructure,
            'General Expenses': general_expenses,
            **other_capex_breakdown,
            'Total': investment_usd
        }
        results['opex_breakdown'] = {
            **staff_breakdown,
            **services_breakdown,
            **other_opex_breakdown,
            'Total Annual OPEX': total_opex_annual
        }
        results['asics'] = asics
        results['total_asic_hashrate'] = total_hashrate
        results['total_asic_cost'] = total_cost

        # Create chart (placeholder)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, 9)), y=[results['annual_profit_usd']] * 8, mode='lines', name='Annual Profit USD'))
        fig.add_trace(go.Scatter(x=list(range(1, 9)), y=[results['annual_depreciation']] * 8, mode='lines', name='Annual Depreciation USD'))
        chart_html = fig.to_html(full_html=False)

        return render_template('results.html', results=results, chart_html=chart_html, btc_price=btc_price, difficulty=difficulty, current_block=current_block, blocks_to_halving=blocks_to_halving, months_to_halving=months_to_halving, avg_change_6m=avg_change_6m, avg_change_12m=avg_change_12m, avg_change_24m=avg_change_24m, avg_change_36m=avg_change_36m, avg_change_48m=avg_change_48m)

    # For GET
    return render_template('index.html', btc_price=btc_price, difficulty=difficulty, current_block=current_block, blocks_to_halving=blocks_to_halving, months_to_halving=months_to_halving, avg_change_6m=avg_change_6m, avg_change_12m=avg_change_12m, avg_change_24m=avg_change_24m, avg_change_36m=avg_change_36m, avg_change_48m=avg_change_48m)

@app.route('/export_excel')
def export_excel():
    # Placeholder for Excel export
    df = pd.DataFrame({'Metric': ['ROI', 'Total Profits USD'], 'Value': [10, 100000]})
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name='mining_results.xlsx', as_attachment=True)

@app.route('/calculate', methods=['POST'])
def calculate():
    # Same as POST in index
    # Get CAPEX
    research = safe_float(request.form.get('research'))
    asics_unit_value = safe_float(request.form.get('asics_unit_value'))
    shelter = safe_float(request.form.get('shelter'))
    generator = safe_float(request.form.get('generator'))
    infrastructure = safe_float(request.form.get('infrastructure'))
    general_expenses = safe_float(request.form.get('general_expenses'))
    other_capex_total = 0
    other_capex_breakdown = {}
    for i in range(1, 21):  # Assume up to 20 others
        value = request.form.get(f'other_capex_{i}')
        name = request.form.get(f'other_capex_name_{i}')
        if value and name:
            val = safe_float(value)
            other_capex_total += val
            other_capex_breakdown[name] = val
    investment_usd = research + asics_unit_value + shelter + generator + infrastructure + general_expenses + other_capex_total

    # Collect ASIC table data
    asics = []
    total_hashrate = 0
    total_cost = 0
    for i in range(1, 21):  # Assume up to 20 rows
        model = request.form.get(f'asic_model_{i}')
        if model:
            units = int(safe_float(request.form.get(f'asic_units_{i}')))
            price = safe_float(request.form.get(f'asic_price_{i}'))
            hashrate = safe_float(request.form.get(f'asic_hashrate_{i}'))
            consumption = safe_float(request.form.get(f'asic_consumption_{i}'))
            asics.append({
                'model': model,
                'units': units,
                'price': price,
                'hashrate': hashrate,
                'consumption': consumption
            })
            total_hashrate += hashrate * units
            total_cost += price * units
    hashrate_th = total_hashrate
    # Get Electricity
    power_source = request.form.get('power_source', 'Direct Energy')
    if power_source == 'Direct Energy':
        energy_cost_per_mwh = safe_float(request.form.get('energy_cost_per_mwh'))
        energy_cost_per_kwh = energy_cost_per_mwh / 1000
    else:
        gas_price_per_mwh = safe_float(request.form.get('gas_price_per_mwh'))
        energy_cost_per_kwh = gas_price_per_mwh / 1000
    hardware_type = request.form.get('hardware_type', 'Air')
    manufacturer = request.form.get('manufacturer', '')
    model = request.form.get('model', '')
    location = request.form.get('location', 'Neuquen')
    expansion_10mw = request.form.get('expansion_10mw', 'no') == 'yes'
    expansion_40mw = request.form.get('expansion_40mw', 'no') == 'yes'
    financing_rate = safe_float(request.form.get('financing_rate'))
    downtime_percent = safe_float(request.form.get('downtime_percent'))
    btc_price_override = request.form.get('btc_price_override')
    depreciation_years = int(safe_float(request.form.get('depreciation_years'), 3))
    depreciation_method = request.form.get('depreciation_method', 'linear')
    operational_costs = safe_float(request.form.get('operational_costs'))

    # Get OPEX
    # Staff
    staff_total = 0
    staff_breakdown = {}
    for i in range(1, 21):  # Assume up to 20 staff
        value = request.form.get(f'staff_{i}')
        name = request.form.get(f'staff_name_{i}')
        if value and name:
            val = safe_float(value)
            staff_total += val
            staff_breakdown[name] = val * 12  # Annual

    # Services
    insurance = safe_float(request.form.get('insurance'))
    software = safe_float(request.form.get('software'))
    internet = safe_float(request.form.get('internet'))
    security = safe_float(request.form.get('security'))
    accounting = safe_float(request.form.get('accounting'))
    lawyer = safe_float(request.form.get('lawyer'))
    services_total = insurance + software + internet + security + accounting + lawyer
    services_breakdown = {
        'Insurance': insurance * 12,
        'Software': software * 12,
        'Internet': internet * 12,
        'Security': security * 12,
        'Accounting': accounting * 12,
        'Lawyer': lawyer * 12
    }
    for i in range(1, 21):  # Dynamic services
        value = request.form.get(f'service_{i}')
        name = request.form.get(f'service_name_{i}')
        if value and name:
            val = safe_float(value)
            services_total += val
            services_breakdown[name] = val * 12

    # Others
    downtime_percent = safe_float(request.form.get('downtime_percent'))
    operational_costs = safe_float(request.form.get('operational_costs'))
    other_opex_total = operational_costs
    other_opex_breakdown = {
        'Additional Operational Costs': operational_costs * 12
    }
    for i in range(1, 21):  # Dynamic others
        value = request.form.get(f'other_opex_{i}')
        name = request.form.get(f'other_opex_name_{i}')
        if value and name:
            val = safe_float(value)
            other_opex_total += val
            other_opex_breakdown[name] = val * 12

    total_opex_annual = (staff_total + services_total + other_opex_total) * 12

    # Fetch or override BTC price
    btc_price = float(btc_price_override) if btc_price_override else get_btc_price()
    difficulty = get_network_difficulty()
    current_block = get_current_block()
    next_halving_block = ((current_block // 210000) + 1) * 210000
    blocks_to_halving = next_halving_block - current_block
    months_to_halving = blocks_to_halving / (144 * 30)  # Approximate: 144 blocks/day * 30 days/month

    # Historical difficulty changes
    hist_diff = get_historical_difficulty()
    avg_change_6m = calculate_avg_monthly_difficulty_change(hist_diff, 6)
    avg_change_12m = calculate_avg_monthly_difficulty_change(hist_diff, 12)
    avg_change_24m = calculate_avg_monthly_difficulty_change(hist_diff, 24)
    avg_change_36m = calculate_avg_monthly_difficulty_change(hist_diff, 36)
    avg_change_48m = calculate_avg_monthly_difficulty_change(hist_diff, 48)

    # Run simulation
    results = simulate_mining(investment_usd, hashrate_th, energy_cost_per_kwh, btc_price, difficulty, 30, depreciation_years, depreciation_method, total_opex_annual, downtime_percent)

    # Add CAPEX breakdown to results
    results['capex_breakdown'] = {
        'Research': research,
        'ASICs': asics_unit_value,
        'Shelter': shelter,
        'Generator': generator,
        'Infrastructure': infrastructure,
        'General Expenses': general_expenses,
        **other_capex_breakdown,
        'Total': investment_usd
    }
    results['opex_breakdown'] = {
        **staff_breakdown,
        **services_breakdown,
        **other_opex_breakdown,
        'Total Annual OPEX': total_opex_annual
    }
    results['asics'] = asics
    results['total_asic_hashrate'] = total_hashrate
    results['total_asic_cost'] = total_cost

    # Create chart (placeholder)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(1, 9)), y=[results['annual_profit_usd']] * 8, mode='lines', name='Annual Profit USD'))
    fig.add_trace(go.Scatter(x=list(range(1, 9)), y=[results['annual_depreciation']] * 8, mode='lines', name='Annual Depreciation USD'))
    chart_html = fig.to_html(full_html=False)

    return render_template('results_partial.html', results=results, chart_html=chart_html, btc_price=btc_price, difficulty=difficulty, current_block=current_block, blocks_to_halving=blocks_to_halving, months_to_halving=months_to_halving, avg_change_6m=avg_change_6m, avg_change_12m=avg_change_12m, avg_change_24m=avg_change_24m, avg_change_36m=avg_change_36m, avg_change_48m=avg_change_48m)

if __name__ == '__main__':
    app.run(debug=True)