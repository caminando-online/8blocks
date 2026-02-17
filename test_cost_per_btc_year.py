from decimal import Decimal
from src.domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode, DifficultyProjectionMode
from src.domain.entities import MiningFarm
from src.application.services import MiningSimulationService

def test_cost_per_btc_year():
    service = MiningSimulationService()
    farm = MiningFarm(name="Test Farm")
    # 100 TH/s, 3000W
    farm.add_asics(ASIC(model="S19", price=Decimal('0'), hashrate=Decimal('100'), consumption=Decimal('3000')), 1)
    
    network = BitcoinNetworkState(
        difficulty=Decimal('80e12'),
        price_btc_usd=Decimal('60000'),
        current_block=840000
    )
    
    # Electricity: $0.05/kWh -> $50/MWh
    # OPEX: $1000/month
    params = SimulationParams(
        years=1,
        energy_cost_kwh=Decimal('0.05'),
        operational_costs_annual=Decimal('12000'),
        price_mode=PriceProjectionMode.MANUAL,
        manual_prices=[Decimal('0')]*8,
        difficulty_mode=DifficultyProjectionMode.MANUAL,
        manual_difficulty_variations=[Decimal('0')]*8
    )
    
    results = service.calculate_results(farm, network, params, {})
    
    year_1 = results['annual_generation'][0]
    btc_gen = year_1['btc_generated']
    elec_cost = year_1['electricity_cost']
    opex_cost = year_1['opex_cost']
    cost_per_btc_calc = year_1['cost_per_btc']
    
    expected_cost_per_btc = (elec_cost + opex_cost) / btc_gen
    
    print(f"BTC Generated: {btc_gen}")
    print(f"Elec Cost: {elec_cost}")
    print(f"OPEX Cost: {opex_cost}")
    print(f"Cost per BTC: {cost_per_btc_calc}")
    print(f"Expected Cost per BTC: {expected_cost_per_btc}")
    
    assert abs(cost_per_btc_calc - expected_cost_per_btc) < Decimal('0.01'), "Cost per BTC calculation mismatch!"
    print("✅ test_cost_per_btc_year passed!")

if __name__ == "__main__":
    test_cost_per_btc_year()
