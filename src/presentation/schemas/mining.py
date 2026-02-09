from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import List, Optional

class AsicInput(BaseModel):
    model: str
    units: int = Field(ge=0)
    price: Decimal = Field(ge=0)
    hashrate: Decimal = Field(ge=0)
    consumption: Decimal = Field(ge=0)

class SimulationRequest(BaseModel):
    # CAPEX
    research: Decimal = Field(default=Decimal('0'), ge=0)
    asics_unit_value: Decimal = Field(default=Decimal('0'), ge=0)
    shelter: Decimal = Field(default=Decimal('0'), ge=0)
    generator: Decimal = Field(default=Decimal('0'), ge=0)
    infrastructure: Decimal = Field(default=Decimal('0'), ge=0)
    general_expenses: Decimal = Field(default=Decimal('0'), ge=0)
    
    # ASICs list
    asics: List[AsicInput] = []
    
    # Operation
    energy_cost_per_mwh: Decimal = Field(default=Decimal('0'), ge=0)
    downtime_percent: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    operational_costs_annual: Decimal = Field(default=Decimal('0'), ge=0)
    depreciation_years: int = Field(default=3, ge=1, le=10)
    
    # BTC Price Override
    btc_price_override: Optional[Decimal] = Field(default=None, ge=0)
    
    @property
    def energy_cost_per_kwh(self) -> Decimal:
        return self.energy_cost_per_mwh / Decimal('1000')
