from fastapi import FastAPI, HTTPException
import ccxt
import re
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

app = FastAPI()

# Initialize the ccxt Binance instances for spot and futures
binance_spot = ccxt.binance()
binance_futures = ccxt.binance({'options': {'defaultType': 'future'}})

# List of pairs to attach to spot_not_in_futures
additional_spot_pairs = {"1000PEPE/USDT", "XAI/USDT", "FET/USDT", "WIF/USDT", "1000SATS/USDT", "FRONT/USDT", "ZEC/USDT", "SOL/USDT", "TRU/USDT"}

def get_binance_spot_pairs():
    markets = binance_spot.load_markets()
    # Filter for active pairs only and pairs ending with '/USDT'
    return [market for market, data in markets.items() if market.endswith('/USDT') and data['active']]

def normalize_futures_pair(pair: str, spot_pairs: set) -> str:
    base_symbol = pair.split(':')[0]
    
    # If the direct comparison does not find a match, attempt normalization
    if base_symbol not in spot_pairs:
        # Remove numeric prefixes (like '1000')
        base_symbol = re.sub(r'^\d+', '', base_symbol)
    
    return base_symbol

def get_binance_futures_pairs(spot_pairs: set):
    markets = binance_futures.load_markets()
    # Normalize the futures pairs only if necessary and filter active pairs
    normalized_markets = [
        normalize_futures_pair(market, spot_pairs) for market, data in markets.items() if market.endswith(':USDT') and data['active']
    ]
    return normalized_markets

@app.get("/spot_pairs_not_in_futures")
@cache(expire=60)
async def get_spot_pairs_not_in_futures():
    spot_pairs = set(get_binance_spot_pairs())  # Convert to set for faster lookups
    futures_pairs = set(get_binance_futures_pairs(spot_pairs))

    spot_not_in_futures = sorted(list((spot_pairs - futures_pairs) | additional_spot_pairs))

    return {
        "pairs": spot_not_in_futures,
        "refresh_period": 1800  # Refresh period in seconds (e.g., 1800 seconds = 30 minutes)
    }

@app.get("/refresh_cache")
async def refresh_cache():
    # Clear the entire cache
    await FastAPICache.clear()

    spot_pairs = set(get_binance_spot_pairs())  # Convert to set for faster lookups
    futures_pairs = set(get_binance_futures_pairs(spot_pairs))

    spot_not_in_futures = sorted(list((spot_pairs - futures_pairs) | additional_spot_pairs))

    # Manually cache the refreshed result using the cache backend
    backend = FastAPICache.get_backend()
    await backend.set("spot_not_in_futures", spot_not_in_futures, expire=1800)

    return {"status": "Cache refreshed"}

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
