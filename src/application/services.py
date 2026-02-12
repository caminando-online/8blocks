import json
import os
from decimal import Decimal
from typing import Dict, Any
from ..domain.entities import MiningFarm
from ..domain.value_objects import SimulationParams, BitcoinNetworkState, PriceProjectionMode, FinancialMetrics

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
        daily_energy_cost = daily_power_kwh * params.energy_cost_kwh
        monthly_energy_cost = daily_energy_cost * Decimal('30.41')
        monthly_opex_only = (params.operational_costs_annual + params.energy_om_annual) / Decimal('12')
        
        # Monthly BTC production (Will be recalculated in loop as difficulty changes)
        total_profits_usd = Decimal('0')
        current_price = network.price_btc_usd
        total_investment = farm.total_investment + sum(capex_breakdown.values())
        
        current_difficulty = network.difficulty
        backlog = self._get_backlog_data()
        self._current_year_drift = Decimal('1')
        
        # 8-year monthly simulation tracer
        annual_results = []
        monthly_cash_flows = []
        monthly_btc_production = []
        
        # Year accumulators
        year_btc = Decimal('0')
        year_revenue = Decimal('0')
        year_energy_cost = Decimal('0')
        year_opex = Decimal('0')
        year_warranty_interest = Decimal('0')
        year_difficulty_sum = Decimal('0')
        year_had_halving = False
        
        simulation_block = network.current_block
        
        # Calculate Other Incomes totals
        total_units = sum(item['units'] for item in farm.asics)
        total_setup_fees = Decimal(str(total_units)) * params.setup_fee_per_unit
        total_disconnect_fees = Decimal(str(total_units)) * params.disconnect_fee_per_unit
        total_warranty_deposit = Decimal(str(total_units)) * params.power_warranty_per_unit
        
        monthly_warranty_interest = total_warranty_deposit * (params.power_warranty_interest_rate / Decimal('100')) / Decimal('12')

        # Add initial fees to total profits (Benefit for company)
        total_profits_usd += total_setup_fees
        total_profits_usd += total_disconnect_fees
        
        initial_cash_flow = total_setup_fees + total_disconnect_fees
        # We'll treat the initial fees as the "Month 0" cash flow for break-even
        if initial_cash_flow > 0:
            monthly_cash_flows.append(initial_cash_flow)
        
        for month_idx in range(params.years * 12):
            year_idx = month_idx // 12
            month_of_year = month_idx % 12
            
            if params.price_mode == PriceProjectionMode.MANUAL:
                if year_idx < len(params.manual_prices) and params.manual_prices[year_idx] > 0:
                    current_price = params.manual_prices[year_idx]
                else:
                    current_price = network.price_btc_usd
            else:
                if month_of_year == 0:
                    target_end_price = params.manual_prices[year_idx] if (year_idx < len(params.manual_prices) and params.manual_prices[year_idx] > 0) else current_price
                    year_start_price = current_price
                    temp_price = year_start_price
                    for m in range(12):
                        backlog_idx = month_idx + m
                        backlog_data = backlog[backlog_idx % len(backlog)]
                        cp = Decimal(str(backlog_data['change_pct']))
                        temp_price = temp_price * (Decimal('1') + cp / Decimal('100'))
                    
                    natural_end_price = temp_price
                    if natural_end_price > 0 and target_end_price > 0:
                        drift_factor_annual = target_end_price / natural_end_price
                        self._current_year_drift = Decimal(str(pow(float(drift_factor_annual), 1/12)))
                    else:
                        self._current_year_drift = Decimal('1')

                change_pct = Decimal(str(backlog[month_idx % len(backlog)]['change_pct']))
                current_price = current_price * (Decimal('1') + change_pct / Decimal('100')) * self._current_year_drift

            if year_idx < len(params.manual_difficulty_variations):
                diff_change_pct = params.manual_difficulty_variations[year_idx]
                current_difficulty = current_difficulty * (Decimal('1') + diff_change_pct / Decimal('100'))

            blocks_in_month = int(144 * 30.41)
            next_simulation_block = simulation_block + blocks_in_month
            halving_blocks = [840000, 1050000, 1260000]
            current_reward = self._get_reward_for_block(simulation_block)
            effective_reward = current_reward
            
            for hb in halving_blocks:
                if simulation_block < hb <= next_simulation_block:
                    year_had_halving = True
                    pre_ratio = Decimal(hb - simulation_block) / Decimal(blocks_in_month)
                    post_ratio = Decimal(1) - pre_ratio
                    new_reward = self._get_reward_for_block(hb)
                    effective_reward = (current_reward * pre_ratio) + (new_reward * post_ratio)
                    break

            simulation_block = next_simulation_block
            seconds_in_month = Decimal('3600') * Decimal('24') * Decimal('30.41')
            difficulty_factor = current_difficulty * Decimal(str(2**32))
            
            monthly_btc = (effective_hashrate * Decimal('1e12') * seconds_in_month / difficulty_factor) * effective_reward
            monthly_revenue = monthly_btc * current_price
            
            # Warranty interest is a benefit for the company
            monthly_net_profit = monthly_revenue - monthly_energy_cost - monthly_opex_only + monthly_warranty_interest
            
            year_btc += monthly_btc
            year_revenue += monthly_revenue
            year_energy_cost += monthly_energy_cost
            year_opex += monthly_opex_only
            year_warranty_interest += monthly_warranty_interest
            year_difficulty_sum += current_difficulty
            total_profits_usd += monthly_net_profit
            
            monthly_cash_flows.append(monthly_net_profit)
            monthly_btc_production.append(monthly_btc)

            if month_of_year == 11:
                total_power_mw = farm.total_consumption_mw
                annual_mwh = total_power_mw * Decimal('24') * Decimal('365')
                
                btc_per_mwh = (year_btc / annual_mwh) if annual_mwh > 0 else Decimal('0')
                usd_per_mwh = (year_revenue / annual_mwh) if annual_mwh > 0 else Decimal('0')
                
                gross_profit = year_revenue - year_energy_cost
                net_profit = gross_profit - year_opex + year_warranty_interest
                operating_margin = (net_profit / year_revenue * Decimal('100')) if year_revenue > 0 else Decimal('0')

                annual_results.append({
                    'year': year_idx + 1,
                    'btc_generated': year_btc,
                    'usd_revenue': year_revenue,
                    'electricity_cost': year_energy_cost,
                    'opex_cost': year_opex,
                    'warranty_income': year_warranty_interest,
                    'gross_profit': gross_profit,
                    'net_profit': net_profit,
                    'operating_margin': operating_margin,
                    'avg_difficulty': year_difficulty_sum / Decimal('12'),
                    'has_halving': year_had_halving,
                    'btc_per_mwh': btc_per_mwh,
                    'usd_per_mwh': usd_per_mwh
                })
                # Reset year accumulators
                year_btc = Decimal('0')
                year_revenue = Decimal('0')
                year_energy_cost = Decimal('0')
                year_opex = Decimal('0')
                year_warranty_interest = Decimal('0')
                year_difficulty_sum = Decimal('0')
                year_had_halving = False

        # Financial Metrics
        roi = FinancialMetrics.calculate_roi(total_profits_usd, total_investment)
        
        # CAGR based on Net Profit growth from first positive year to last year? 
        # Or based on Revenue? Usually based on Net Profit or Portfolio Value.
        # User asked for CAGR, I'll calculate it on annual Net Profit if possible.
        first_year_profit = annual_results[0]['net_profit']
        last_year_profit = annual_results[-1]['net_profit']
        cagr = FinancialMetrics.calculate_cagr(first_year_profit, last_year_profit, params.years - 1)
        
        # Break-even USD
        be_month_usd = FinancialMetrics.calculate_break_even_month(total_investment, monthly_cash_flows)
        be_usd_str = f"Año {((be_month_usd - 1) // 12) + 1}, Mes {((be_month_usd - 1) % 12) + 1}" if be_month_usd else "N/A"
        
        # Break-even BTC
        # How many BTC is the investment worth today?
        investment_in_btc = total_investment / network.price_btc_usd if network.price_btc_usd > 0 else Decimal('0')
        be_month_btc = FinancialMetrics.calculate_break_even_month(investment_in_btc, monthly_btc_production)
        be_btc_str = f"Año {((be_month_btc - 1) // 12) + 1}, Mes {((be_month_btc - 1) % 12) + 1}" if be_month_btc else "N/A"

        # Production cost per BTC
        total_costs = (month_idx + 1) * (monthly_energy_cost + monthly_opex_only)
        total_btc = sum(monthly_btc_production)
        cost_per_btc = total_costs / total_btc if total_btc > 0 else Decimal('0')

        # OPC/h calculation for electricity section
        energy_cost_per_mwh_pure = params.energy_cost_kwh * Decimal('1000')
        hours_per_month = Decimal('729.84')
        total_monthly_opex = (params.operational_costs_annual + params.energy_om_annual) / Decimal('12')
        total_power_mw = farm.total_consumption_mw
        hourly_opex = total_monthly_opex / hours_per_month
        hourly_energy_cost = energy_cost_per_mwh_pure * total_power_mw
        total_hourly_cost = hourly_opex + hourly_energy_cost
        opc_per_h = (total_hourly_cost / total_power_mw) if total_power_mw > 0 else energy_cost_per_mwh_pure

        return {
            'annual_generation': annual_results,
            'daily_btc': monthly_btc / Decimal('30.41'),
            'daily_usd': (monthly_btc * current_price) / Decimal('30.41'),
            'daily_cost': daily_energy_cost,
            'total_profits_usd': total_profits_usd,
            'roi': roi,
            'cagr': cagr,
            'break_even_usd': be_usd_str,
            'break_even_btc': be_btc_str,
            'investment_in_btc': investment_in_btc,
            'cost_per_btc': cost_per_btc,
            'farm_name': farm.name,
            'investment': total_investment,
            'total_asic_hashrate': farm.total_hashrate,
            'total_asic_units': total_units,
            'network_percentage': (effective_hashrate / (network.difficulty * Decimal(str(2**32)) / Decimal('600') / Decimal('1e12')) * Decimal('100')) if network.difficulty > 0 else Decimal('0'),
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
            'power_source': power_source,
            'other_incomes': {
                'setup_fees': total_setup_fees,
                'disconnect_fees': total_disconnect_fees,
                'warranty_deposit': total_warranty_deposit,
                'monthly_warranty_interest': monthly_warranty_interest,
                'annual_warranty_interest': monthly_warranty_interest * Decimal('12')
            }
        }

    def _get_reward_for_block(self, block: int) -> Decimal:
        if block < 840000:
            return Decimal('6.25')
        elif block < 1050000:
            return Decimal('3.125')
        elif block < 1260000:
            return Decimal('1.5625')
        else:
            return Decimal('0.78125')

