import aiohttp
import os
from typing import Dict, Any

class CoinMarketCapClient:
    def __init__(self):
        self.api_key = os.getenv("COINMARKETCAP_API_KEY")
        # Updated for 2025+ with enhanced endpoints and DEX API
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.dex_url = "https://pro-api.coinmarketcap.com/v2"  # New DEX API endpoints
        # 2025+ rate limiting (updated limits)
        self.basic_limit = 300  # calls per minute (increased from 333/day)
        self.standard_limit = 3000  # calls per minute
        self.session_timeout = 30  # Connection timeout
        
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make request to CoinMarketCap API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accepts": "application/json"
        }
        
        if self.api_key:
            headers["X-CMC_PRO_API_KEY"] = self.api_key
            
        if params is None:
            params = {}
            
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"CoinMarketCap API error {response.status}: {error_text}")
    
    async def get_cryptocurrency_quotes(self, symbols: str) -> Dict:
        """Get latest market quotes for cryptocurrencies"""
        try:
            params = {"symbol": symbols}
            data = await self._make_request("/cryptocurrency/quotes/latest", params)
            return data.get("data", {})
        except Exception as e:
            print(f"Error fetching CoinMarketCap data: {e}")
            return {}
    
    async def get_global_metrics(self) -> Dict:
        """Get global cryptocurrency market metrics"""
        try:
            data = await self._make_request("/global-metrics/quotes/latest")
            return data.get("data", {})
        except Exception as e:
            print(f"Error fetching global metrics: {e}")
            return {}