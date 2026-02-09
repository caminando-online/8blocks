from flask import Blueprint, render_template, request, jsonify
from decimal import Decimal
from ..schemas.mining import SimulationRequest
from ...domain.entities import MiningFarm
from ...domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode
from ...application.services import MiningSimulationService
from ...infrastructure.repositories import JsonASICRepository
from ...infrastructure.external_apis import ExternalBitcoinApiRepository
import os

mining_bp = Blueprint('mining', __name__)

# Dependecies (In a real app, these would be injected)
asic_repo = JsonASICRepository(os.path.join('src', 'infrastructure', 'asics.json'))
network_repo = ExternalBitcoinApiRepository()
simulation_service = MiningSimulationService()

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
                'price': Decimal(form_data.get(f'asic_price_{i}', '0')),
                'hashrate': Decimal(form_data.get(f'asic_hashrate_{i}', '0')),
                'consumption': Decimal(form_data.get(f'asic_consumption_{i}', '0'))
            })
    return asics

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
            
        params = SimulationParams(
            energy_cost_kwh=Decimal(data.get('energy_cost_per_mwh', '0')) / Decimal('1000'),
            downtime_percent=Decimal(data.get('downtime_percent', '0')),
            operational_costs_annual=Decimal(data.get('operational_costs', '0')) * Decimal('12'),
            depreciation_years=int(data.get('depreciation_years', '3')),
            price_mode=PriceProjectionMode(data.get('price_method', 'manual')),
            manual_prices=[Decimal(data.get(f'manual_price_{i}' if data.get('price_method') == 'manual' else f'backlog_price_{i}', '0')) for i in range(1, 9)],
            manual_difficulty_variations=[Decimal(data.get(f'manual_diff_var_{i}', '0')) for i in range(1, 9)]
        )
        
        capex_breakdown = _extract_capex_breakdown(data)
        
        # Execute Use Case
        results = simulation_service.calculate_results(farm, network_state, params, capex_breakdown)
        
        return render_template('results_partial.html', results=results, btc_price=network_state.price_btc_usd)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@mining_bp.route('/export_excel')
def export_excel():
    import pandas as pd
    from io import BytesIO
    from flask import send_file
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
