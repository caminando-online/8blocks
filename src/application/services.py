import json
import os
from decimal import Decimal
from typing import Dict, Any
from ..domain.entities import MiningFarm
from ..domain.value_objects import SimulationParams, BitcoinNetworkState, PriceProjectionMode

class MiningSimulationService:
    def __init__(self, backlog_path: str = None):
        # In a real app, this path would be injected
        self.backlog_path = backlog_path or os.path.join('src', 'infrastructure', 'price_backlog.json')
        self._backlog_data = None
        self._current_year_drift = Decimal('1')

    def _get_backlog_data(self):
        if self._backlog_data is None:
            try:
                with open(self.backlog_path, 'r') as f:
                    self._backlog_data = json.load(f)
            except Exception:
                self._backlog_data = []  # type: ignore
        return self._backlog_data

    def calculate_results(self, farm: MiningFarm, network: BitcoinNetworkState, params: SimulationParams, capex_breakdown: Dict[str, Decimal], power_source: str = "Direct Energy") -> Dict[str, Any]:
        effective_hashrate = farm.total_hashrate * (Decimal('1') - params.downtime_percent / Decimal('100'))
        
        daily_power_kwh = farm.total_consumption_kw * Decimal('24')
        daily_cost = daily_power_kwh * params.energy_cost_kwh
        monthly_opex = (daily_cost * Decimal('30.41')) + ((params.operational_costs_annual + params.energy_om_annual) / Decimal('12'))
        
        # Monthly BTC production (Will be recalculated in loop as difficulty changes)
        total_profits_usd = Decimal('0')
        current_price = network.price_btc_usd
        current_difficulty = network.difficulty
        backlog = self._get_backlog_data()
        self._current_year_drift = Decimal('1')
        
        # 8-year monthly simulation
        for month_idx in range(params.years * 12):
            year_idx = month_idx // 12
            month_of_year = month_idx % 12
            
            if params.price_mode == PriceProjectionMode.MANUAL:
                # Use provided annual price for the entire year
                if year_idx < len(params.manual_prices):
                    current_price = params.manual_prices[year_idx]
            else:
                # Backlog Based with Overrides
                if month_of_year == 0:
                    target_end_price = params.manual_prices[year_idx] if year_idx < len(params.manual_prices) else current_price
                    
                    year_start_price = current_price
                    temp_price = year_start_price
                    for m in range(12):
                        backlog_idx = month_idx + m
                        backlog_data = backlog[backlog_idx % len(backlog)]  # type: ignore
                        cp = Decimal(str(backlog_data['change_pct']))
                        temp_price = temp_price * (Decimal('1') + cp / Decimal('100'))
                    
                    natural_end_price = temp_price
                    if natural_end_price > 0 and target_end_price > 0:
                        drift_factor_annual = target_end_price / natural_end_price
                        self._current_year_drift = Decimal(str(pow(float(drift_factor_annual), 1/12)))  # type: ignore
                    else:
                        self._current_year_drift = Decimal('1')  # type: ignore

                change_pct = Decimal(str(backlog[month_idx % len(backlog)]['change_pct']))  # type: ignore
                current_price = current_price * (Decimal('1') + change_pct / Decimal('100')) * self._current_year_drift  # type: ignore
            
            # Update difficulty based on manual variations (monthly compound)
            if year_idx < len(params.manual_difficulty_variations):
                diff_change_pct = params.manual_difficulty_variations[year_idx]
                current_difficulty = current_difficulty * (Decimal('1') + diff_change_pct / Decimal('100'))

            # Recalculate monthly BTC production with current difficulty
            monthly_btc = (effective_hashrate * Decimal('1e12') / current_difficulty) * Decimal('144') * network.block_reward * Decimal('30.41')
            
            monthly_revenue = monthly_btc * current_price
            monthly_profit = monthly_revenue - monthly_opex
            total_profits_usd += monthly_profit

        total_other_capex = sum(capex_breakdown.values())
        total_investment = farm.total_investment + total_other_capex
        annual_depreciation = total_investment / Decimal(str(params.depreciation_years))
        annual_profit_usd = total_profits_usd / Decimal(str(params.years))
        
        roi = (total_profits_usd / total_investment * Decimal('100')) if total_investment > 0 else Decimal('0')
        
        network_hashrate_th = network.difficulty * Decimal(str(2**32)) / Decimal('600') / Decimal('1e12')
        network_percentage = (effective_hashrate / network_hashrate_th * Decimal('100')) if network_hashrate_th > 0 else Decimal('0')

        # Electricity summary metrics
        energy_cost_per_mwh_pure = params.energy_cost_kwh * Decimal('1000')
        
        # Monthly base for consistency (30.41 days * 24 hours = 729.84 hours)
        hours_per_month = Decimal('729.84')
        # Total OPEX for Electricity metrics includes both Project OPEX and Energy O&M
        total_monthly_opex = (params.operational_costs_annual + params.energy_om_annual) / Decimal('12')
        
        # Power in MW
        total_power_mw = farm.total_consumption_mw
        
        # 1. OPEX Horario ($/h)
        hourly_opex = total_monthly_opex / hours_per_month
        
        # 2. Costo Energía Horario ($/h)
        hourly_energy_cost = energy_cost_per_mwh_pure * total_power_mw
        
        # 3. Costo Total Horario ($/h)
        total_hourly_cost = hourly_opex + hourly_energy_cost
        
        # 4. OPC/h ($/MWh) - Total cost per unit of energy
        if total_power_mw > 0:
            opc_per_h = total_hourly_cost / total_power_mw
        else:
            opc_per_h = energy_cost_per_mwh_pure

        return {
            'daily_btc': monthly_btc / Decimal('30.41'),
            'daily_usd': (monthly_btc * current_price) / Decimal('30.41'), # Last month's price
            'daily_cost': daily_cost,
            'annual_profit_usd': annual_profit_usd,
            'total_profits_usd': total_profits_usd,
            'annual_depreciation': annual_depreciation,
            'roi': roi,
            'farm_name': farm.name,
            'investment': total_investment,
            'total_asic_hashrate': farm.total_hashrate,
            'total_asic_units': sum(item['units'] for item in farm.asics),
            'network_percentage': network_percentage,
            'asics': [
                {
                    'model': item['asic'].model,
                    'units': item['units'],
                    'price': item['asic'].price,
                    'hashrate': item['asic'].hashrate,
                    'consumption': item['asic'].consumption,
                    'usd_per_th': item['asic'].usd_per_th,
                    'j_per_th': item['asic'].j_per_th
                } for item in farm.asics
            ],
            'capex_breakdown': {
                'ASIC Investment': farm.total_investment,
                **capex_breakdown,
                'Total': total_investment
            },
            'energy_cost_per_mwh_pure': energy_cost_per_mwh_pure,
            'monthly_opex': total_monthly_opex,
            'opc_per_h': opc_per_h,
            'hourly_opex': hourly_opex,
            'hourly_energy_cost': hourly_energy_cost,
            'total_hourly_cost': total_hourly_cost,
            'total_power_consumption': total_power_mw,
            'power_source': power_source
        }
