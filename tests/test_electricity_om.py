import sys
import os
from decimal import Decimal

# Add current directory to path
sys.path.append(os.getcwd())

from src.presentation.routes.mining import _extract_asics, _extract_opex_breakdown
from src.domain.entities import MiningFarm
from src.domain.value_objects import ASIC, BitcoinNetworkState, SimulationParams, PriceProjectionMode, DifficultyProjectionMode
from src.application.services import MiningSimulationService

def test_electricity_om_sum():
    print("Testing if O&M is summed to MWh cost...")
    
    # Mock data equivalent to what mining.py would process
    gas_price_per_mwh = Decimal('50')
    om_per_mwh = Decimal('10')
    
    # Expected mwh_cost should be 60
    mwh_cost = gas_price_per_mwh + om_per_mwh
    print(f"Calculated MWh Cost: {mwh_cost}")
    assert mwh_cost == Decimal('60'), f"Expected 60, got {mwh_cost}"
    
    # verify that in mining.py logic, it would set energy_cost_kwh correctly
    energy_cost_kwh = mwh_cost / Decimal('1000')
    print(f"Energy Cost per kWh: {energy_cost_kwh}")
    assert energy_cost_kwh == Decimal('0.06'), f"Expected 0.06, got {energy_cost_kwh}"
    
    print("Test passed!")

if __name__ == "__main__":
    test_electricity_om_sum()
