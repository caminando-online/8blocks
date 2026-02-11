import json
from decimal import Decimal
from typing import List, Optional
from ..domain.value_objects import ASIC
from ..domain.interfaces import ASICRepository

class JsonASICRepository(ASICRepository):
    def __init__(self, json_path: str):
        self.json_path = json_path
        
    def _load_data(self) -> List[ASIC]:
        with open(self.json_path, 'r') as f:
            data = json.load(f)
            return [
                ASIC(
                    model=item['model'],
                    price=Decimal(str(item['price'])),
                    hashrate=Decimal(str(item['hashrate'])),
                    consumption=Decimal(str(item['consumption'])),
                    cooling=item.get('cooling', 'Air')
                )
                for item in data
            ]
            
    def get_all(self) -> List[ASIC]:
        return self._load_data()
        
    def get_by_model(self, model: str) -> Optional[ASIC]:
        asics = self._load_data()
        for asic in asics:
            if asic.model == model:
                return asic
        return None
