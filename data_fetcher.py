"""
TradingView Multi-Timeframe Direct Data Fetcher
Fetches real-time price, technical indicators, and pivot points across multiple timeframes
directly from TradingView's scanner infrastructure.
"""

import time
import requests
from typing import Dict, Any

PAIR_CONFIG = {
    "XAUUSD": {"ticker": "OANDA:XAUUSD", "scanner": "cfd", "name": "Gold / US Dollar", "digits": 2},
    "EURUSD": {"ticker": "FX:EURUSD", "scanner": "forex", "name": "Euro / US Dollar", "digits": 5},
    "GBPUSD": {"ticker": "FX:GBPUSD", "scanner": "forex", "name": "British Pound / US Dollar", "digits": 5},
    "USDJPY": {"ticker": "FX:USDJPY", "scanner": "forex", "name": "US Dollar / Japanese Yen", "digits": 3},
    "BTCUSD": {"ticker": "BITSTAMP:BTCUSD", "scanner": "crypto", "name": "Bitcoin / US Dollar", "digits": 2},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SEC = 2.0


def _build_column_list(selected_tf: str = "15") -> list[str]:
    tf_suffix = f"|{selected_tf}" if selected_tf not in ("1D", "D", "") else ""
    
    cols = [
        "close", "open", "high", "low", "change", "change_abs", "volume",
        "Pivot.M.Classic.Middle", "Pivot.M.Classic.R1", "Pivot.M.Classic.S1", 
        "Pivot.M.Classic.R2", "Pivot.M.Classic.S2",
        "Pivot.M.Fibonacci.R1", "Pivot.M.Fibonacci.S1",
        "Recommend.All", "Recommend.MA", "Recommend.Other",
        "EMA20", "EMA50", "EMA200", "SMA50", "SMA200", "RSI", "MACD.macd", "MACD.signal", "ADX", "ATR",
        "close|240", "open|240", "high|240", "low|240", "RSI|240", "EMA20|240", "EMA50|240", "EMA200|240", "MACD.macd|240", "MACD.signal|240", "Recommend.All|240",
        "close|60", "open|60", "high|60", "low|60", "RSI|60", "EMA20|60", "EMA50|60", "EMA200|60", "MACD.macd|60", "MACD.signal|60",
    ]
    
    if tf_suffix and tf_suffix not in ("|240", "|60"):
        extra_cols = [
            f"close{tf_suffix}", f"open{tf_suffix}", f"high{tf_suffix}", f"low{tf_suffix}",
            f"RSI{tf_suffix}", f"EMA20{tf_suffix}", f"EMA50{tf_suffix}", f"EMA200{tf_suffix}",
            f"MACD.macd{tf_suffix}", f"MACD.signal{tf_suffix}", f"ADX{tf_suffix}", f"ATR{tf_suffix}",
            f"Stoch.K{tf_suffix}", f"Stoch.D{tf_suffix}", f"CCI20{tf_suffix}", f"Recommend.All{tf_suffix}"
        ]
        for ec in extra_cols:
            if ec not in cols:
                cols.append(ec)

    return cols


def fetch_market_snapshot(symbol: str = "XAUUSD", timeframe: str = "15") -> Dict[str, Any]:
    symbol = symbol.upper()
    if symbol not in PAIR_CONFIG:
        symbol = "XAUUSD"
        
    cfg = PAIR_CONFIG[symbol]
    cache_key = f"{symbol}_{timeframe}"
    now = time.time()
    
    if cache_key in _CACHE:
        cached_entry = _CACHE[cache_key]
        if now - cached_entry["timestamp"] < CACHE_TTL_SEC:
            return cached_entry["data"]

    scanner = cfg["scanner"]
    url = f"https://scanner.tradingview.com/{scanner}/scan"
    
    cols = _build_column_list(timeframe)
    payload = {
        "symbols": {"tickers": [cfg["ticker"]]},
        "columns": cols
    }
    
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=8)
        resp.raise_for_status()
        res_data = resp.json().get("data", [])
        if not res_data:
            raise ValueError(f"No data returned for ticker {cfg['ticker']}")
            
        raw_values = res_data[0]["d"]
        data_map = dict(zip(cols, raw_values))
        
        tf_suffix = f"|{timeframe}" if timeframe not in ("1D", "D", "") else ""
        
        def get_val(base_col: str, fallback=None):
            if tf_suffix:
                specific = f"{base_col}{tf_suffix}"
                if specific in data_map and data_map[specific] is not None:
                    return data_map[specific]
            if base_col in data_map and data_map[base_col] is not None:
                return data_map[base_col]
            return fallback

        current_price = get_val("close", 0.0)
        open_price = get_val("open", current_price)
        high_price = get_val("high", current_price)
        low_price = get_val("low", current_price)
        
        parsed = {
            "symbol": symbol,
            "name": cfg["name"],
            "ticker": cfg["ticker"],
            "digits": cfg["digits"],
            "timeframe": timeframe,
            "timestamp": now,
            "price": current_price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "change_pct": data_map.get("change", 0.0) or 0.0,
            "indicators_current_tf": {
                "rsi": get_val("RSI", 50.0),
                "ema20": get_val("EMA20", current_price),
                "ema50": get_val("EMA50", current_price),
                "ema200": get_val("EMA200", current_price),
                "macd": get_val("MACD.macd", 0.0),
                "macd_signal": get_val("MACD.signal", 0.0),
                "adx": get_val("ADX", 20.0),
                "atr": get_val("ATR", 1.0),
                "stoch_k": get_val("Stoch.K", 50.0),
                "recommend_all": get_val("Recommend.All", 0.0),
            },
            "htf_4h": {
                "close": data_map.get("close|240", current_price),
                "high": data_map.get("high|240", high_price),
                "low": data_map.get("low|240", low_price),
                "rsi": data_map.get("RSI|240", 50.0),
                "ema50": data_map.get("EMA50|240", current_price),
                "ema200": data_map.get("EMA200|240", current_price),
                "macd": data_map.get("MACD.macd|240", 0.0),
                "macd_signal": data_map.get("MACD.signal|240", 0.0),
                "recommend": data_map.get("Recommend.All|240", 0.0),
            },
            "htf_daily": {
                "close": data_map.get("close", current_price),
                "high": data_map.get("high", high_price),
                "low": data_map.get("low", low_price),
                "rsi": data_map.get("RSI", 50.0),
                "ema50": data_map.get("EMA50", current_price),
                "ema200": data_map.get("EMA200", current_price),
                "recommend": data_map.get("Recommend.All", 0.0),
            },
            "pivots": {
                "middle": data_map.get("Pivot.M.Classic.Middle", current_price),
                "r1": data_map.get("Pivot.M.Classic.R1", current_price * 1.01),
                "s1": data_map.get("Pivot.M.Classic.S1", current_price * 0.99),
                "r2": data_map.get("Pivot.M.Classic.R2", current_price * 1.02),
                "s2": data_map.get("Pivot.M.Classic.S2", current_price * 0.98),
                "fib_r1": data_map.get("Pivot.M.Fibonacci.R1", current_price * 1.008),
                "fib_s1": data_map.get("Pivot.M.Fibonacci.S1", current_price * 0.992),
            },
            "tv_ratings": {
                "all": data_map.get("Recommend.All", 0.0),
                "ma": data_map.get("Recommend.MA", 0.0),
                "oscillators": data_map.get("Recommend.Other", 0.0),
            }
        }
        
        _CACHE[cache_key] = {"timestamp": now, "data": parsed}
        return parsed
        
    except Exception as e:
        if cache_key in _CACHE:
            return _CACHE[cache_key]["data"]
        raise e
