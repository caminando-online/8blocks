from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from enum import Enum

class PriceProjectionMode(str, Enum):
    MANUAL = "manual"
    BACKLOG = "backlog"

class DifficultyProjectionMode(str, Enum):
    MANUAL = "manual"
    BACKLOG = "backlog"

@dataclass(frozen=True)
class ASIC:
    model: str
    price: Decimal
    hashrate: Decimal  # TH/s
    consumption: Decimal  # W
    cooling: str = "Air"
    
    @property
    def usd_per_th(self) -> Decimal:
        if self.hashrate == 0:
            return Decimal('0')
        return self.price / self.hashrate
        
    @property
    def j_per_th(self) -> Decimal:
        if self.hashrate == 0:
            return Decimal('0')
        return self.consumption / self.hashrate

@dataclass(frozen=True)
class BitcoinNetworkState:
    difficulty: Decimal
    price_btc_usd: Decimal
    current_block: int
    network_hashrate_eh: Optional[Decimal] = None
    estimated_next_difficulty_change: Decimal = Decimal('0.0')
    
    @property
    def block_reward(self) -> Decimal:
        # Simplified: Check halving logic based on current_block
        # April 2024 halving was at block 840,000
        if self.current_block < 840000:
            return Decimal('6.25')
        elif self.current_block < 1050000:
            return Decimal('3.125')
        elif self.current_block < 1260000:
            return Decimal('1.5625')
        else:
            return Decimal('0.78125')


    @property
    def blocks_to_halving(self) -> int:
        return 210000 - (self.current_block % 210000)
        
    @property
    def months_to_halving(self) -> float:
        return float(self.blocks_to_halving) / (144 * 30)
        
    @property
    def blocks_to_next_difficulty(self) -> int:
        return 2016 - (self.current_block % 2016)

@dataclass(frozen=True)
class SimulationParams:
    years: int = 8
    energy_cost_kwh: Decimal = Decimal('0')
    energy_om_annual: Decimal = Decimal('0')
    downtime_percent: Decimal = Decimal('0')
    operational_costs_annual: Decimal = Decimal('0')
    depreciation_years: int = 3
    price_mode: PriceProjectionMode = PriceProjectionMode.MANUAL
    difficulty_mode: DifficultyProjectionMode = DifficultyProjectionMode.MANUAL
    manual_prices: list[Decimal] = field(default_factory=lambda: [Decimal('0')] * 8)
    manual_difficulty_variations: list[Decimal] = field(default_factory=lambda: [Decimal('0')] * 8)
