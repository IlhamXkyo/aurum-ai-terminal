"""
Agent 3: ICT / Smart Money Concepts (SMC) & Liquidity Hunt
Analyzes institutional Order Blocks (OB), Fair Value Gaps (FVG),
Optimal Trade Entry (OTE 61.8% - 78.6% Fib), and Liquidity Sweeps (BSL/SSL).
"""

from typing import Dict, Any

def analyze_smc_liquidity(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    high_d = snapshot["htf_daily"].get("high", price * 1.005)
    low_d = snapshot["htf_daily"].get("low", price * 0.995)
    pivots = snapshot["pivots"]
    cur_ind = snapshot["indicators_current_tf"]
    atr = cur_ind.get("atr", max((high_d - low_d) * 0.1, 1.0))

    # 1. Equilibrium & Premium vs Discount Valuation
    range_span = max(high_d - low_d, 0.0001)
    equilibrium = low_d + (range_span * 0.5)
    pct_range = (price - low_d) / range_span * 100

    # Optimal Trade Entry (OTE) Fibonacci Levels (61.8% to 78.6% retracement)
    ote_bull_low = round(low_d + (range_span * 0.214), digits)
    ote_bull_high = round(low_d + (range_span * 0.382), digits)

    ote_bear_low = round(low_d + (range_span * 0.618), digits)
    ote_bear_high = round(low_d + (range_span * 0.786), digits)

    if pct_range >= 65:
        pricing_zone = "PREMIUM ZONE (Area Distribusi Institusi / Optimal Sell)"
        pricing_bias = "BEARISH_FAVORABLE"
    elif pct_range <= 35:
        pricing_zone = "DISCOUNT ZONE (Area Akumulasi Institusi / Optimal Buy)"
        pricing_bias = "BULLISH_FAVORABLE"
    else:
        pricing_zone = "EQUILIBRIUM (Fair Value Zone 50%)"
        pricing_bias = "NEUTRAL"

    # 2. Buy-Side & Sell-Side Liquidity Targets (BSL / SSL)
    bsl_target = round(max(high_d, pivots["r1"]), digits)
    ssl_target = round(min(low_d, pivots["s1"]), digits)

    # 3. Institutional Order Block (OB) Zones
    # Bullish OB (Demand at lower range / discount)
    ob_bull_low = round(low_d, digits)
    ob_bull_high = round(low_d + (atr * 0.8), digits)

    # Bearish OB (Supply at higher range / premium)
    ob_bear_high = round(high_d, digits)
    ob_bear_low = round(high_d - (atr * 0.8), digits)

    # 4. Fair Value Gap (FVG) Modeling
    if abs(price - equilibrium) > atr:
        if price > equilibrium:
            fvg_zone = f"FVG Imbalance terdeteksi di area {round(equilibrium, digits)} - {round(price - (atr * 0.5), digits)} (Potensi magnet retest)"
        else:
            fvg_zone = f"FVG Imbalance terdeteksi di area {round(price + (atr * 0.5), digits)} - {round(equilibrium, digits)} (Potensi magnet retest)"
    else:
        fvg_zone = "Efisiensi harga tercapai, tidak ada FVG imbalance besar di sekitar harga aktif."

    # 5. Liquidity Sweep Check
    if price >= high_d * 0.998:
        sweep_state = "Uji Likuiditas BSL (Waspada Fakeout / Liquidity Sweep di atas swing high)"
    elif price <= low_d * 1.002:
        sweep_state = "Uji Likuiditas SSL (Waspada Stop Hunt / Liquidity Sweep di bawah swing low)"
    else:
        sweep_state = "Pergerakan harga berada di dalam internal liquidity range."

    narrative = (
        f"Valuasi SMC: {pricing_zone} ({pct_range:.1f}% rentang harian). "
        f"Zona Institutional Demand (Bullish OB): {ob_bull_low} - {ob_bull_high}. "
        f"Zona Institutional Supply (Bearish OB): {ob_bear_low} - {ob_bear_high}. "
        f"{sweep_state}. {fvg_zone}"
    )

    return {
        "agent": "ICT / SMC & Liquidity Hunt",
        "pricing_zone": pricing_zone,
        "pricing_bias": pricing_bias,
        "range_percentage": round(pct_range, 1),
        "equilibrium": round(equilibrium, digits),
        "bsl_target": bsl_target,
        "ssl_target": ssl_target,
        "order_block_bullish": {"low": ob_bull_low, "high": ob_bull_high},
        "order_block_bearish": {"low": ob_bear_low, "high": ob_bear_high},
        "fvg_zone": fvg_zone,
        "sweep_state": sweep_state,
        "narrative": narrative
    }
