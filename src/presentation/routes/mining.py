from flask import Blueprint, render_template, request, jsonify  # type: ignore
from decimal import Decimal
from ..schemas.mining import SimulationRequest  # type: ignore
from ...domain.entities import MiningFarm  # type: ignore
from ...domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode, DifficultyProjectionMode  # type: ignore
from ...application.services import MiningSimulationService  # type: ignore
from ...infrastructure.repositories import JsonASICRepository  # type: ignore
from ...infrastructure.external_apis import ExternalBitcoinApiRepository  # type: ignore
import os

# Constants
HOURS_PER_YEAR = Decimal('8760')
MWH_TO_KWH = Decimal('1000')

mining_bp = Blueprint('mining', __name__)

# Dependecies (In a real app, these would be injected)
asic_repo = JsonASICRepository(os.path.join('src', 'infrastructure', 'asics.json'))
network_repo = ExternalBitcoinApiRepository()
simulation_service = MiningSimulationService()

def _clean_currency(value: str) -> str:
    """Removes currency symbols, thousands separators (dots) and replaces decimal comma with dot."""
    if not value or not isinstance(value, str):
        return '0'
    clean = value.replace('$', '').replace('€', '').strip()
    # Check if format is 1.234,56 (Spanish/European style)
    if '.' in clean and ',' in clean:
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        # Check if it's 1234,56
        clean = clean.replace(',', '.')
    return clean

@mining_bp.route('/')

def home():
    network_state = network_repo.get_current_state()
    asics = asic_repo.get_all()
    return render_template('index.html', 
                          asics_data=asics,
                          btc_price=network_state.price_btc_usd,
                          difficulty=network_state.difficulty,
                          current_block=network_state.current_block,
                          blocks_to_halving=network_state.blocks_to_halving,
                          months_to_halving=network_state.months_to_halving,
                          blocks_to_next_difficulty=network_state.blocks_to_next_difficulty,
                          estimated_next_diff_change=network_state.estimated_next_difficulty_change,
                          price_backlog=simulation_service._get_backlog_data(),
                          difficulty_backlog=simulation_service._get_difficulty_backlog_data(),
                          avg_change_6m=1.4,
                          avg_change_12m=1.3,
                          avg_change_24m=1.9,
                          avg_change_36m=3.2,
                          avg_change_48m=3.3)

@mining_bp.route('/network_data')
def get_network_data():
    try:
        network_state = network_repo.get_current_state()
        return jsonify({
            "btc_price": float(network_state.price_btc_usd),
            "difficulty": float(network_state.difficulty),
            "current_block": network_state.current_block,
            "blocks_to_halving": network_state.blocks_to_halving,
            "months_to_halving": round(network_state.months_to_halving, 2),
            "blocks_to_next_difficulty": network_state.blocks_to_next_difficulty,
            "estimated_next_diff_change": float(network_state.estimated_next_difficulty_change)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _extract_capex_breakdown(form_data: dict) -> dict:
    # Create the base dictionary
    base_capex = {
        'Research': Decimal(form_data.get('research', '0') or '0'),
        'ASICs': Decimal(form_data.get('asics_unit_value', '0') or '0'),
        'Shelter': Decimal(form_data.get('shelter', '0') or '0'),
        'Generator': Decimal(form_data.get('generator', '0') or '0'),
        'Infrastructure': Decimal(form_data.get('infrastructure', '0') or '0'),
        'General Expenses': Decimal(form_data.get('general_expenses', '0') or '0'),
    }
    
    # Extract dynamic CAPEX items
    for key, value in form_data.items():
        if key.startswith('other_capex_name_'):
            idx = key.split('_')[-1]
            item_name = value
            item_value = Decimal(form_data.get(f'other_capex_{idx}', '0') or '0')
            if item_name:
                base_capex[item_name] = item_value

    # Calculate Subtotal before financing
    subtotal = sum(base_capex.values())
    
    # Financing Cost
    financing_rate = Decimal(form_data.get('financing_rate', '0') or '0')
    financial_cost = subtotal * (financing_rate / Decimal('100'))
    
    if financial_cost > 0:
        base_capex['Financial Cost'] = financial_cost

    # Calculate Total and add it to the breakdown
    total_val = subtotal + financial_cost
    
    result_breakdown: dict = dict(base_capex)
    result_breakdown['Total'] = total_val
    return result_breakdown


def _extract_asics(form_data: dict) -> list:
    asics = []
    for i in range(1, 21):
        model = form_data.get(f'asic_model_{i}')
        if model:
            asics.append({
                'model': model,
                'units': int(form_data.get(f'asic_units_{i}', '0')),
                'price': Decimal(form_data.get(f'asic_price_{i}', '0') or '0'),
                'hashrate': Decimal(form_data.get(f'asic_hashrate_{i}', '0') or '0'),
                'consumption': Decimal(form_data.get(f'asic_consumption_{i}', '0') or '0')
            })
    return asics

def _extract_capex_breakdown(form_data: dict) -> dict:
    # Helper to extract CAPEX items for reporting
    capex = {}
    
    # Static fields
    static_fields = {
        'research': 'Research',
        'shelter': 'Shelter',
        'generator': 'Generator',
        'infrastructure': 'Infrastructure',
        'general_expenses': 'General Expenses'
    }
    
    for field, label in static_fields.items():
        val = form_data.get(field, '0')
        if val and Decimal(val) > 0:
            capex[label] = Decimal(val)

    # Dynamic items
    for key, value in form_data.items():
        if key.startswith('other_capex_') and not key.startswith('other_capex_name_'):
            idx = key.split('_')[-1]
            name = form_data.get(f'other_capex_name_{idx}', f'Other CAPEX {idx}')
            if value and Decimal(value) > 0:
                capex[name] = Decimal(value)
    return capex

def _extract_opex_breakdown(form_data: dict) -> dict:
    # Fixed monthly costs (captured under services/operational)
    fixed_services = [
        'insurance', 'software', 'internet', 'security', 
        'accounting', 'lawyer'
    ]
    
    staff_monthly = Decimal('0')  # type: ignore
    services_monthly = Decimal('0')  # type: ignore
    other_monthly = Decimal('0')  # type: ignore
    
    for field in fixed_services:
        services_monthly = services_monthly + Decimal(form_data.get(field, '0') or '0')  # type: ignore
    
    # Additional operational costs fall under "Others" in the UI
    other_monthly = other_monthly + Decimal(form_data.get('operational_costs', '0') or '0')  # type: ignore
    
    # Dynamic monthly costs (staff, service, other)
    for key, value in form_data.items():
        if '_name_' in key:
            continue
        
        if key.startswith('staff_'):
            staff_monthly = staff_monthly + Decimal(value or '0')  # type: ignore
        elif key.startswith('service_'):
            services_monthly = services_monthly + Decimal(value or '0')  # type: ignore
        elif key.startswith('other_') and not key.startswith('other_capex_'):
            other_monthly = other_monthly + Decimal(value or '0')  # type: ignore
                
    total_monthly = staff_monthly + services_monthly + other_monthly  # type: ignore
    
    return {
        'total_monthly': total_monthly,
        'total_annual': total_monthly * Decimal('12'),
        'staff_monthly': staff_monthly,
        'services_monthly': services_monthly,
        'other_monthly': other_monthly
    }

@mining_bp.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.form.to_dict()
        asics_list = _extract_asics(data)
        
        # Build Domain objects
        farm = MiningFarm(name="My Mining Farm")
        for asic_data in asics_list:
            asic = ASIC(
                model=asic_data['model'], 
                price=asic_data['price'], 
                hashrate=asic_data['hashrate'], 
                consumption=asic_data['consumption']
            )
            farm.add_asics(asic, asic_data['units'])
            
        network_state = network_repo.get_current_state()
        btc_price_override = data.get('btc_price_override')
        difficulty_override = data.get('difficulty_override')
        
        if btc_price_override or difficulty_override:
            network_state = BitcoinNetworkState(
                difficulty=Decimal(difficulty_override) if difficulty_override else network_state.difficulty,
                price_btc_usd=Decimal(btc_price_override) if btc_price_override else network_state.price_btc_usd,
                current_block=network_state.current_block,
                estimated_next_difficulty_change=network_state.estimated_next_difficulty_change
            )
            
        # Determine MWh cost based on source
        power_source = data.get('power_source', 'Direct Energy')
        if power_source == 'Gas powered':
            mwh_cost = Decimal(data.get('gas_price_per_mwh', '0') or '0')
            # O&M and Overhauling could be considered additional OPEX
            # om_annual = (om_per_mwh * farm_kw * 8760) / 1000
            om_annual = Decimal(data.get('om_per_mwh', '0') or '0') * farm.total_consumption_kw * (HOURS_PER_YEAR / MWH_TO_KWH)
            # Note: Overhauling is usually a one-time or infrequent large cost, 
            # for now we'll add it once if provided, but normally it should be amortized.
            overhauling = Decimal(data.get('overhauling', '0') or '0')
        else:
            mwh_cost = Decimal(data.get('energy_cost_per_mwh', '0') or '0')
            om_annual = Decimal('0')
            overhauling = Decimal('0')

        opex_breakdown = _extract_opex_breakdown(data)
        
        params = SimulationParams(
            energy_cost_kwh=mwh_cost / Decimal('1000'),
            energy_om_annual=om_annual + overhauling,
            downtime_percent=Decimal(_clean_currency(data.get('downtime_percent', '0'))),
            operational_costs_annual=opex_breakdown['total_annual'],
            depreciation_years=int(data.get('depreciation_years', '3')),
            price_mode=PriceProjectionMode(data.get('price_method', 'manual')),
            difficulty_mode=DifficultyProjectionMode(data.get('difficulty_method', 'manual')),
            manual_prices=[Decimal(_clean_currency(data.get(f'manual_price_{i}' if data.get('price_method') == 'manual' else f'backlog_price_{i}', '0'))) for i in range(1, 9)],
            manual_difficulty_variations=[Decimal(_clean_currency(data.get(f'manual_diff_var_{i}' if data.get('difficulty_method') == 'manual' else f'backlog_diff_var_{i}', '0'))) for i in range(1, 9)],
            # Other Incomes
            setup_fee_per_unit=Decimal(_clean_currency(data.get('setup_fee_per_unit', '0'))),
            disconnect_fee_per_unit=Decimal(_clean_currency(data.get('disconnect_fee_per_unit', '0'))),
            power_warranty_per_unit=Decimal(_clean_currency(data.get('power_warranty_per_unit', '0'))),
            power_warranty_interest_rate=Decimal(_clean_currency(data.get('power_warranty_interest_rate', '0')))
        )

        
        capex_breakdown = _extract_capex_breakdown(data)
        
        # Execute Use Case
        results = simulation_service.calculate_results(farm, network_state, params, capex_breakdown, power_source=power_source)
        
        # Add OPEX breakdown to results for the template
        # Include Electricity O&M/Overhauling for full visibility
        results['opex_summary'] = {
            'monthly_total': opex_breakdown['total_monthly'] + ((om_annual + overhauling) / Decimal('12')),
            'annual_total': opex_breakdown['total_annual'] + om_annual + overhauling,
            'staff_monthly': opex_breakdown['staff_monthly'],
            'staff_annual': opex_breakdown['staff_monthly'] * Decimal('12'),
            'services_monthly': opex_breakdown['services_monthly'],
            'services_annual': opex_breakdown['services_monthly'] * Decimal('12'),
            'other_monthly': opex_breakdown['other_monthly'],
            'other_annual': opex_breakdown['other_monthly'] * Decimal('12'),
            'energy_om_monthly': (om_annual + overhauling) / Decimal('12'),
            'energy_om_annual': om_annual + overhauling
        }
        
        return render_template('results_partial.html', results=results, btc_price=network_state.price_btc_usd)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@mining_bp.route('/export_excel')
def export_excel():
    import pandas as pd  # type: ignore
    from io import BytesIO
    from flask import send_file  # type: ignore
    # Placeholder for Excel export
    df = pd.DataFrame({'Metric': ['Note'], 'Value': ['Refactored structure active. Simulation state needs persistent storage for export.']})
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name='mining_results.xlsx', as_attachment=True)

@mining_bp.route('/update_asics')
def update_asics():
    # Placeholder for dynamic update from Bitmain/WhatsMiner shops
    # In a real app, this would trigger a background task or update the JSON repo
    return jsonify({"message": "ASIC hardware list update triggered (Placeholder)"})
