from typing import Protocol, List, Optional
from .value_objects import ASIC, BitcoinNetworkState

class ASICRepository(Protocol):
    def get_all(self) -> List[ASIC]:
        ...
        
    def get_by_model(self, model: str) -> Optional[ASIC]:
        ...

class BitcoinNetworkRepository(Protocol):
    def get_current_state(self) -> BitcoinNetworkState:
        ...
