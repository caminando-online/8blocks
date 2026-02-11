from dataclasses import dataclass, field
from typing import List, Dict
from decimal import Decimal
from .value_objects import ASIC

@dataclass
class MiningFarm:
    name: str
    asics: List[Dict] = field(default_factory=list)  # List of {'asic': ASIC, 'units': int}
    location: str = "Neuquen"
    
    def add_asics(self, asic: ASIC, units: int):
        self.asics.append({'asic': asic, 'units': units})
        
    @property
    def total_hashrate(self) -> Decimal:
        return sum(item['asic'].hashrate * Decimal(str(item['units'])) for item in self.asics)
        
    @property
    def total_consumption_kw(self) -> Decimal:
        power_w = sum(item['asic'].consumption * Decimal(str(item['units'])) for item in self.asics)
        return power_w / Decimal('1000')

    @property
    def total_consumption_mw(self) -> Decimal:
        return self.total_consumption_kw / Decimal('1000')
        
    @property
    def total_investment(self) -> Decimal:
        return sum(item['asic'].price * Decimal(str(item['units'])) for item in self.asics)
