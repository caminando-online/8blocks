from decimal import Decimal
from src.domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode, DifficultyProjectionMode
from src.domain.entities import MiningFarm
from src.application.services import MiningSimulationService

def test_downtime_impact():
    service = MiningSimulationService()
    farm = MiningFarm(name="Test Farm")
    # 100 TH/s, 3000W
    farm.add_asics(ASIC(model="S19", price=Decimal('0'), hashrate=Decimal('100'), consumption=Decimal('3000')), 1)
    
    network = BitcoinNetworkState(
        difficulty=Decimal('80e12'),
        price_btc_usd=Decimal('60000'),
        current_block=840000
    )
    
    # scenario 1: 0% downtime
    params_0 = SimulationParams(
        years=1,
        energy_cost_kwh=Decimal('0.05'),
        energy_om_annual=Decimal('1200'), # $100/mo variable O&M
        operational_costs_annual=Decimal('12000'), # $1000/mo fixed staff
        downtime_percent=Decimal('0'),
        price_mode=PriceProjectionMode.MANUAL,
        manual_prices=[Decimal('0')]*8,
        difficulty_mode=DifficultyProjectionMode.MANUAL,
        manual_difficulty_variations=[Decimal('0')]*8
    )
    
    results_0 = service.calculate_results(farm, network, params_0, {})
    elec_0 = results_0['annual_generation'][0]['electricity_cost']
    opex_0 = results_0['annual_generation'][0]['opex_cost']
    btc_0 = results_0['annual_generation'][0]['btc_generated']
    
    print(f"0% Downtime: BTC={btc_0:.6f}, Elec+OM={elec_0:.2f}, FixedOPEX={opex_0:.2f}")
    
    # scenario 2: 10% downtime
    params_10 = SimulationParams(
        years=1,
        energy_cost_kwh=Decimal('0.05'),
        energy_om_annual=Decimal('1200'),
        operational_costs_annual=Decimal('12000'),
        downtime_percent=Decimal('10'),
        price_mode=PriceProjectionMode.MANUAL,
        manual_prices=[Decimal('0')]*8,
        difficulty_mode=DifficultyProjectionMode.MANUAL,
        manual_difficulty_variations=[Decimal('0')]*8
    )
    
    results_10 = service.calculate_results(farm, network, params_10, {})
    elec_10 = results_10['annual_generation'][0]['electricity_cost']
    opex_10 = results_10['annual_generation'][0]['opex_cost']
    btc_10 = results_10['annual_generation'][0]['btc_generated']
    
    print(f"10% Downtime: BTC={btc_10:.6f}, Elec+OM={elec_10:.2f}, FixedOPEX={opex_10:.2f}")
    
    # Assertions
    assert btc_10 < btc_0, "BTC generation should be lower with downtime"
    assert abs(btc_10 - btc_0 * Decimal('0.9')) < Decimal('0.0001'), "BTC generation should be reduced by approx 10%"
    
    assert elec_10 < elec_0, "Electricity cost should be lower with downtime"
    assert abs(elec_10 - elec_0 * Decimal('0.9')) < Decimal('1'), "Elec+OM should be reduced by approx 10%"
    
    assert opex_10 == opex_0, f"Fixed OPEX should NOT be affected by downtime, got {opex_10} vs {opex_0}"
    
    print("✅ Downtime impact verification passed!")

if __name__ == "__main__":
    test_downtime_impact()
