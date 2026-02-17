from decimal import Decimal
from src.domain.entities import MiningFarm
from src.domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode, DifficultyProjectionMode
from src.application.services import MiningSimulationService

def test_capex_calculation():
    service = MiningSimulationService()
    
    # Setup Farm with 1 ASIC @ $1000
    farm = MiningFarm(name="Test Farm")
    asic = ASIC(model="S21", price=Decimal("1000"), hashrate=Decimal("200"), consumption=Decimal("3500"))
    farm.add_asics(asic, 1)
    
    # Setup Network
    network = BitcoinNetworkState(difficulty=Decimal("80e12"), price_btc_usd=Decimal("90000"), current_block=840000)
    
    # Setup Params
    params = SimulationParams(
        energy_cost_kwh=Decimal("0.05"),
        years=1,
        manual_prices=[Decimal("0")]*8,
        manual_difficulty_variations=[Decimal("0")]*8
    )
    
    # Capex breakdown from presentation (cleaned)
    capex_breakdown = {
        'Research': Decimal("100"),
        'Financial Cost': Decimal("50")
    }
    
    results = service.calculate_results(farm, network, params, capex_breakdown)
    
    print(f"ASIC Investment: {results['capex_breakdown']['ASIC Investment']}")
    print(f"Research: {results['capex_breakdown'].get('Research')}")
    print(f"Financial Cost: {results['capex_breakdown'].get('Financial Cost')}")
    print(f"Total Investment: {results['investment']}")
    
    # Expected: 1000 (ASIC) + 100 (Research) + 50 (Finance) = 1150
    assert results['investment'] == Decimal("1150")
    assert 'ASICs' not in results['capex_breakdown']
    assert 'Total' in results['capex_breakdown']
    assert results['capex_breakdown']['Total'] == Decimal("1150")
    
    print("Verification SUCCESSFUL!")

if __name__ == "__main__":
    test_capex_calculation()
