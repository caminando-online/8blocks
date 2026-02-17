import json
import os
from decimal import Decimal
from typing import Dict, Any
from ..domain.entities import MiningFarm
from ..domain.value_objects import SimulationParams, BitcoinNetworkState, PriceProjectionMode, DifficultyProjectionMode

# Constants
HOURS_PER_YEAR = Decimal('8760')

class MiningSimulationService:
    def __init__(self, backlog_path: str = None, difficulty_backlog_path: str = None):
        # In a real app, this path would be injected
        self.backlog_path = backlog_path or os.path.join('src', 'infrastructure', 'price_backlog.json')
        self.difficulty_backlog_path = difficulty_backlog_path or os.path.join('src', 'infrastructure', 'difficulty_backlog.json')
        self._backlog_data = None
        self._difficulty_backlog_data = None
        self._current_year_drift = Decimal('1')
        self._current_diff_year_drift = Decimal('1')

    def _get_backlog_data(self):
        if self._backlog_data is None:
            try:
                with open(self.backlog_path, 'r') as f:
                    self._backlog_data = json.load(f)
            except Exception:
                self._backlog_data = []  # type: ignore
        return self._backlog_data

    def _get_difficulty_backlog_data(self):
        if self._difficulty_backlog_data is None:
            try:
                with open(self.difficulty_backlog_path, 'r') as f:
                    self._difficulty_backlog_data = json.load(f)
            except Exception:
                self._difficulty_backlog_data = []  # type: ignore
        return self._difficulty_backlog_data

    def calculate_results(self, farm: MiningFarm, network: BitcoinNetworkState, params: SimulationParams, capex_breakdown: Dict[str, Decimal], power_source: str = "Direct Energy") -> Dict[str, Any]:
        uptime_ratio = Decimal('1') - (params.downtime_percent / Decimal('100'))
        effective_hashrate = farm.total_hashrate * uptime_ratio
        
        daily_power_kwh = farm.total_consumption_kw * Decimal('24')
        # Electricity is a variable cost, affected by downtime
        daily_electricity_cost = daily_power_kwh * params.energy_cost_kwh * uptime_ratio
        monthly_electricity_cost = daily_electricity_cost * Decimal('30.41')
        
        # Energy O&M is considered variable (per MWh produced/consumed), 
        # so it's also affected by downtime.
        # However, Overhauling might be fixed. 
        # In mining.py, energy_om_annual = om_per_mwh * farm_kw * (8760 / 1000) + overhauling.
        # We need to separate them if we want precision, but for now, 
        # let's assume the user provided energy_om_annual as the variable part.
        energy_om_monthly_variable = (params.energy_om_annual / Decimal('12')) * uptime_ratio
        
        # Fixed OPEX is NOT reduced by downtime (staff, services, etc.)
        monthly_opex_fixed = params.operational_costs_annual / Decimal('12')
        
        # Other Incomes / Fees
        total_units = sum(item['units'] for item in farm.asics)
        setup_fees = params.setup_fee_per_unit * Decimal(str(total_units))
        disconnect_fees = params.disconnect_fee_per_unit * Decimal(str(total_units))
        warranty_deposit = params.power_warranty_per_unit * Decimal(str(total_units))
        monthly_warranty_interest = warranty_deposit * (params.power_warranty_interest_rate / Decimal('100') / Decimal('12'))
        
        # Simulation state
        total_profits_usd = Decimal('0')
        total_btc_generated = Decimal('0')
        total_opex_cost = Decimal('0')
        total_electricity_cost = Decimal('0')
        total_warranty_income = Decimal('0')
        
        current_price = network.price_btc_usd
        current_difficulty = network.difficulty
        backlog = self._get_backlog_data()
        difficulty_backlog = self._get_difficulty_backlog_data()
        self._current_year_drift = Decimal('1')
        self._current_diff_year_drift = Decimal('1')
        
        annual_results = []
        year_btc = Decimal('0')
        year_revenue = Decimal('0')
        year_electricity = Decimal('0')
        year_opex = Decimal('0')
        year_warranty = Decimal('0')
        year_difficulty_sum = Decimal('0')
        year_halving_month = None
        
        # Depreciation state
        total_asic_investment = farm.total_investment
        depreciation_years = params.depreciation_years
        annual_depreciation_amount = total_asic_investment / Decimal(str(depreciation_years)) if depreciation_years > 0 else Decimal('0')
        accumulated_depreciation = Decimal('0')
        
        simulation_block = network.current_block
        
        for month_idx in range(params.years * 12):
            year_idx = month_idx // 12
            month_of_year = month_idx % 12
            
            # Price Projection
            if params.price_mode == PriceProjectionMode.MANUAL:
                # manual_prices[year_idx] is now Annual % growth
                if month_of_year == 0:
                    annual_growth_pct = params.manual_prices[year_idx % len(params.manual_prices)]
                    # We could apply it once a year or spread it monthly. 
                    # For consistency with backlog (which is monthly), we can spread it.
                    self._current_year_drift = Decimal(str(pow(float(1 + annual_growth_pct / 100), 1/12)))
                
                current_price = current_price * self._current_year_drift
            else:
                if month_of_year == 0:
                    target_end_price_pct = params.manual_prices[year_idx % len(params.manual_prices)]
                    year_start_price = current_price
                    
                    # Backlog projections are monthly jumps.
                    # We drift them so the annual growth matches the user's manual % target.
                    temp_price = year_start_price
                    for m in range(12):
                        backlog_idx = month_idx + m
                        backlog_data = backlog[backlog_idx % len(backlog)]
                        cp = Decimal(str(backlog_data['change_pct']))
                        temp_price = temp_price * (Decimal('1') + cp / Decimal('100'))
                    
                    natural_end_price = temp_price
                    # User target price based on annual growth %
                    target_end_price = year_start_price * (1 + target_end_price_pct / Decimal('100'))
                    
                    if natural_end_price > 0 and target_end_price > 0:
                        drift_factor_annual = target_end_price / natural_end_price
                        self._current_year_drift = Decimal(str(pow(float(drift_factor_annual), 1/12)))
                    else:
                        self._current_year_drift = Decimal('1')

                change_pct = Decimal(str(backlog[month_idx % len(backlog)]['change_pct']))
                current_price = current_price * (Decimal('1') + change_pct / Decimal('100')) * self._current_year_drift

            # Difficulty Projection: Uses 8 separate years of Average Monthly % variation
            # (passed in params.manual_difficulty_variations)
            diff_change_pct = params.manual_difficulty_variations[year_idx % len(params.manual_difficulty_variations)]
            current_difficulty = current_difficulty * (Decimal('1') + diff_change_pct / Decimal('100'))

            # Rewards and Production
            blocks_in_month = int(144 * 30.41)
            next_simulation_block = simulation_block + blocks_in_month
            halving_blocks = [840000, 1050000, 1260000]
            current_reward = self._get_reward_for_block(simulation_block)
            effective_reward = current_reward
            
            for hb in halving_blocks:
                if simulation_block < hb <= next_simulation_block:
                    year_halving_month = month_of_year + 1
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
            
            # Monthly Incomes/Costs
            # Note: energy_om_monthly_variable is added to electricity cost for consistency with the plan
            monthly_variable_costs = monthly_electricity_cost + energy_om_monthly_variable
            monthly_profit = monthly_revenue - monthly_variable_costs - monthly_opex_fixed + monthly_warranty_interest
            if month_idx == 0:
                monthly_profit += setup_fees
            if month_idx == (params.years * 12 - 1):
                monthly_profit += disconnect_fees

            year_btc += monthly_btc
            year_revenue += monthly_revenue
            year_electricity += monthly_variable_costs
            year_opex += monthly_opex_fixed
            year_warranty += monthly_warranty_interest
            year_difficulty_sum += current_difficulty
            
            total_btc_generated += monthly_btc
            total_profits_usd += monthly_profit
            total_electricity_cost += monthly_variable_costs
            total_opex_cost += monthly_opex_fixed
            total_warranty_income += monthly_warranty_interest

            if month_of_year == 11:
                # Annual Depreciation
                current_year_depreciation = Decimal('0')
                if (year_idx + 1) <= depreciation_years:
                    current_year_depreciation = annual_depreciation_amount
                elif (year_idx + 1) == (depreciation_years + 1):
                    # In case of non-integer years, but here it's int. 
                    # If it was exactly depreciation_years, it's already done.
                    pass
                
                accumulated_depreciation += current_year_depreciation
                book_value = max(Decimal('0'), total_asic_investment - accumulated_depreciation)

                total_power_mw = farm.total_consumption_mw
                annual_mwh = total_power_mw * Decimal('24') * Decimal('365')
                btc_per_mwh = (year_btc / annual_mwh) if annual_mwh > 0 else Decimal('0')
                usd_per_mwh = (year_revenue / annual_mwh) if annual_mwh > 0 else Decimal('0')
                
                gross_profit_year = year_revenue - year_electricity
                net_profit_year = year_revenue - year_electricity - year_opex + year_warranty
                if year_idx == 0: net_profit_year += setup_fees
                if year_idx == params.years - 1: net_profit_year += disconnect_fees

                other_income_year = year_warranty
                if year_idx == 0: other_income_year += setup_fees
                if year_idx == params.years - 1: other_income_year += disconnect_fees

                cost_per_btc_year = (year_electricity + year_opex) / year_btc if year_btc > 0 else Decimal('0')

                annual_results.append({
                    'year': year_idx + 1,
                    'btc_generated': year_btc,
                    'usd_revenue': year_revenue,
                    'other_income': other_income_year,
                    'total_revenue': year_revenue + other_income_year,
                    'avg_difficulty': year_difficulty_sum / Decimal('12'),
                    'halving_month': year_halving_month,
                    'btc_per_mwh': btc_per_mwh,
                    'usd_per_mwh': usd_per_mwh,
                    'cost_per_btc': cost_per_btc_year,
                    'electricity_cost': year_electricity,
                    'opex_cost': year_opex,
                    'warranty_income': year_warranty,
                    'gross_profit': gross_profit_year,
                    'net_profit': net_profit_year,
                    'operating_margin': (net_profit_year / (year_revenue + other_income_year) * 100) if (year_revenue + other_income_year) > 0 else 0,
                    'has_halving': year_halving_month is not None,
                    'depreciation': current_year_depreciation,
                    'accumulated_depreciation': accumulated_depreciation,
                    'book_value': book_value
                })
                # Reset
                year_btc, year_revenue, year_electricity, year_opex, year_warranty, year_difficulty_sum = Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')
                year_halving_month = None

        # Filter out keys that will be added explicitly to avoid double counting
        allowed_capex = {k: v for k, v in capex_breakdown.items() if k not in ['Total', 'ASICs', 'ASIC Investment', 'Financial Cost']}
        
        # Calculate other capex subtotal (including Financial Cost if it was passed)
        total_other_capex = sum(allowed_capex.values())
        if 'Financial Cost' in capex_breakdown:
            total_other_capex += capex_breakdown['Financial Cost']
            allowed_capex['Financial Cost'] = capex_breakdown['Financial Cost']

        total_investment = farm.total_investment + total_other_capex
        total_investment_btc = total_investment / network.price_btc_usd if network.price_btc_usd > 0 else Decimal('0')
        
        roi = (total_profits_usd / total_investment * Decimal('100')) if total_investment > 0 else Decimal('0')
        
        # CAGR calculation
        if total_investment > 0 and total_profits_usd > 0:
            cagr = (pow(float((total_profits_usd + total_investment) / total_investment), 1/params.years) - 1) * 100
        else:
            cagr = 0

        # Metrics for consistency
        energy_cost_per_mwh_pure = params.energy_cost_kwh * Decimal('1000')
        hours_per_month = Decimal('729.84')
        total_monthly_opex = params.operational_costs_annual / Decimal('12')
        total_power_mw = farm.total_consumption_mw
        hourly_opex = total_monthly_opex / hours_per_month
        
        # Hourly Energy Cost + Variable O&M (Calculated at full capacity for reference metrics)
        hourly_variable_maintenance = (params.energy_om_annual / HOURS_PER_YEAR)
        hourly_energy_cost = energy_cost_per_mwh_pure * total_power_mw
        
        total_hourly_cost = hourly_opex + hourly_energy_cost + hourly_variable_maintenance
        opc_per_h = total_hourly_cost / total_power_mw if total_power_mw > 0 else (energy_cost_per_mwh_pure + (hourly_variable_maintenance / total_power_mw if total_power_mw > 0 else 0))

        cost_per_btc = (total_electricity_cost + total_opex_cost) / total_btc_generated if total_btc_generated > 0 else 0
        
        # Break Even Calculations
        break_even_usd = total_investment / (total_profits_usd / (params.years * 12)) if total_profits_usd > 0 else "N/A"
        
        # BTC Break Even and Net Result
        accumulated_net_btc = Decimal('0')
        break_even_btc_month = None
        
        temp_price = network.price_btc_usd
        self._current_year_drift = Decimal('1') 
        # We need to simulate the month-by-month profit in BTC to find BE point
        simulation_block_be = network.current_block
        
        for month_idx in range(params.years * 12):
            year_idx = month_idx // 12
            month_of_year = month_idx % 12
            
            # Use same price/diff logic as the main simulation to be consistent
            if params.price_mode == PriceProjectionMode.MANUAL:
                if month_of_year == 0:
                    annual_growth_pct = params.manual_prices[year_idx % len(params.manual_prices)]
                    self._current_year_drift = Decimal(str(pow(float(1 + annual_growth_pct / 100), 1/12)))
                temp_price = temp_price * self._current_year_drift
            else:
                if month_of_year == 0:
                    target_end_price_pct = params.manual_prices[year_idx % len(params.manual_prices)]
                    year_start_price = temp_price
                    t_price = year_start_price
                    for m in range(12):
                        b_idx = month_idx + m
                        b_data = backlog[b_idx % len(backlog)]
                        cp = Decimal(str(b_data['change_pct']))
                        t_price = t_price * (Decimal('1') + cp / Decimal('100'))
                    
                    if t_price > 0 and (year_start_price * (1 + target_end_price_pct / Decimal('100'))) > 0:
                        drift = (year_start_price * (1 + target_end_price_pct / Decimal('100'))) / t_price
                        self._current_year_drift = Decimal(str(pow(float(drift), 1/12)))
                    else: self._current_year_drift = Decimal('1')

                change_pct = Decimal(str(backlog[month_idx % len(backlog)]['change_pct']))
                temp_price = temp_price * (Decimal('1') + change_pct / Decimal('100')) * self._current_year_drift

            # Monthly reward logic (simplified for speed but needs to match halving)
            blocks_in_month = int(144 * 30.41)
            next_simulation_block_be = simulation_block_be + blocks_in_month
            current_reward_be = self._get_reward_for_block(simulation_block_be)
            effective_reward_be = current_reward_be
            for hb in [840000, 1050000, 1260000]:
                if simulation_block_be < hb <= next_simulation_block_be:
                    pre_ratio = Decimal(hb - simulation_block_be) / Decimal(blocks_in_month)
                    effective_reward_be = (current_reward_be * pre_ratio) + (self._get_reward_for_block(hb) * (Decimal(1) - pre_ratio))
                    break
            simulation_block_be = next_simulation_block_be

            # Diff change
            diff_change_pct = params.manual_difficulty_variations[year_idx % len(params.manual_difficulty_variations)]
            current_difficulty_be = network.difficulty * ((Decimal('1') + diff_change_pct / Decimal('100')) ** (month_idx + 1))
            
            monthly_btc = (effective_hashrate * Decimal('1e12') * (Decimal('3600') * Decimal('24') * Decimal('30.41')) / (current_difficulty_be * Decimal(str(2**32)))) * effective_reward_be
            
            # Costs in BTC
            m_costs_usd = monthly_variable_costs + monthly_opex_fixed - monthly_warranty_interest
            if month_idx == 0: m_costs_usd -= setup_fees
            if month_idx == (params.years * 12 - 1): m_costs_usd -= disconnect_fees
            
            monthly_net_btc = monthly_btc - (m_costs_usd / temp_price if temp_price > 0 else Decimal('0'))
            accumulated_net_btc += monthly_net_btc
            
            if break_even_btc_month is None and accumulated_net_btc >= total_investment_btc:
                break_even_btc_month = month_idx + 1

        total_net_btc = accumulated_net_btc

        return {
            'annual_generation': annual_results,
            'daily_btc': total_btc_generated / Decimal(str(params.years * 365)),
            'daily_usd': (total_btc_generated * current_price) / Decimal(str(params.years * 365)),
            'daily_cost': (monthly_variable_costs + monthly_opex_fixed) / Decimal('30.41'),
            'annual_profit_usd': total_profits_usd / params.years,
            'total_profits_usd': total_profits_usd,
            'total_net_btc': total_net_btc,
            'downtime_impact': {
                'uptime_percent': Decimal('100') - params.downtime_percent,
                'downtime_percent': params.downtime_percent,
                'lost_btc_annual': (total_btc_generated / uptime_ratio * (params.downtime_percent / Decimal('100'))) / params.years if uptime_ratio > 0 else Decimal('0'),
                'saved_costs_annual': (total_electricity_cost / uptime_ratio * (params.downtime_percent / Decimal('100'))) / params.years if uptime_ratio > 0 else Decimal('0'),
                'uptime_days_annual': Decimal('365') * uptime_ratio,
                'downtime_days_annual': Decimal('365') * (params.downtime_percent / Decimal('100'))
            },
            'roi': float(roi),
            'cagr': float(cagr),
            'cost_per_btc': float(cost_per_btc),
            'break_even_usd': f"{float(break_even_usd):.1f} meses" if isinstance(break_even_usd, (Decimal, float)) else break_even_usd,
            'break_even_btc': f"{break_even_btc_month} meses" if break_even_btc_month else "N/A",
            'farm_name': farm.name,
            'investment': total_investment,
            'total_asic_hashrate': farm.total_hashrate,
            'total_asic_units': total_units,
            'network_percentage': (effective_hashrate / (network.difficulty * Decimal(str(2**32)) / Decimal('600') / Decimal('1e12')) * 100) if network.difficulty > 0 else 0,
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
            'other_incomes': {
                'setup_fees': setup_fees,
                'disconnect_fees': disconnect_fees,
                'warranty_deposit': warranty_deposit,
                'monthly_warranty_interest': monthly_warranty_interest,
                'annual_warranty_interest': monthly_warranty_interest * 12
            },
            'energy_cost_per_mwh_pure': energy_cost_per_mwh_pure,
            'hourly_variable_maintenance': hourly_variable_maintenance,
            'monthly_opex': total_monthly_opex,
            'opc_per_h': opc_per_h,
            'hourly_opex': hourly_opex,
            'hourly_energy_cost': hourly_energy_cost,
            'total_hourly_cost': total_hourly_cost,
            'total_power_consumption': total_power_mw,
            'power_source': power_source,
            'depreciation_summary': {
                'total_investment': total_asic_investment,
                'depreciation_years': depreciation_years,
                'annual_amount': annual_depreciation_amount
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

