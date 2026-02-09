import requests
from decimal import Decimal
from typing import Optional
from ..domain.value_objects import BitcoinNetworkState
from ..domain.interfaces import BitcoinNetworkRepository

import time

class ExternalBitcoinApiRepository(BitcoinNetworkRepository):
    def __init__(self):
        self._cache = None
        self._last_update = 0
        self._cache_duration = 300  # 5 minutes

    def get_current_state(self) -> BitcoinNetworkState:
        now = time.time()
        if self._cache and (now - self._last_update < self._cache_duration):
            return self._cache

        price = self._get_btc_price()
        difficulty = self._get_network_difficulty()
        block_count = self._get_current_block()
        estimated_change = self._get_difficulty_adjustment()
        
        self._cache = BitcoinNetworkState(
            difficulty=Decimal(str(difficulty)),
            price_btc_usd=Decimal(str(price)),
            current_block=block_count,
            estimated_next_difficulty_change=Decimal(str(estimated_change))
        )
        self._last_update = int(now)
        return self._cache



    def _get_difficulty_adjustment(self) -> float:
        try:
            response = requests.get('https://mempool.space/api/v1/difficulty-adjustment', timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data.get('difficultyChange', 0.0))
        except Exception:
            return 0.0
        
    def _get_btc_price(self) -> float:
        try:
            response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['bitcoin']['usd'])
        except Exception:
            # Fallback to Binance
            try:
                response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
                response.raise_for_status()
                return float(response.json()['price'])
            except Exception:
                return 95000.0  # Fallback

    def _get_network_difficulty(self) -> float:
        try:
            response = requests.get('https://blockchain.info/q/getdifficulty', timeout=10)
            response.raise_for_status()
            return float(response.text)
        except Exception:
            return 100000000000000.0

    def _get_current_block(self) -> int:
        try:
            response = requests.get('https://blockchain.info/q/getblockcount', timeout=10)
            response.raise_for_status()
            return int(response.text)
        except Exception:
            return 850000
