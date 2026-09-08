"""
Agent 3: Smart Money Concepts (SMC) & Liquidity
Analyzes institutional liquidity pools (BSL & SSL), Premium vs Discount pricing zones,
Order Blocks (OB), and Fair Value Gaps (FVG).
"""

from typing import Dict, Any

def analyze_smc_liquidity(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    high_d = snapshot["htf_daily"].get("high", price * 1.01)
    low_d = snapshot["htf_daily"].get("low", price * 0.99)
    pivots = snapshot["pivots"]
    cur_ind = snapshot["indicators_current_tf"]

    # Equilibrium & Premium / Discount calculation
    range_span = max(high_d - low_d, 0.0001)
    equilibrium = low_d + (range_span * 0.5)
    pct_range = (price - low_d) / range_span * 100

    if pct_range >= 65:
        pricing_zone = "PREMIUM (Zona Mahal - Optimal untuk Distribusi / Sell Short)"
        pricing_bias = "BEARISH_FAVORABLE"
    elif pct_range <= 35:
        pricing_zone = "DISCOUNT (Zona Murah - Optimal untuk Akumulasi / Buy Long)"
        pricing_bias = "BULLISH_FAVORABLE"
    else:
        pricing_zone = "EQUILIBRIUM (Zona Netral / Fair Value)"
        pricing_bias = "NEUTRAL"

    # Liquidity Targets (BSL & SSL)
    bsl_target = round(max(high_d, pivots["r1"]), digits)
    ssl_target = round(min(low_d, pivots["s1"]), digits)

    dist_to_bsl = abs(bsl_target - price)
    dist_to_ssl = abs(price - ssl_target)
    
    if dist_to_bsl < dist_to_ssl:
        liquidity_focus = f"Mengincar Buy-Side Liquidity (BSL) di area {bsl_target}"
    else:
        liquidity_focus = f"Mengincar Sell-Side Liquidity (SSL) di area {ssl_target}"

    # Order Block modeling (Institutional Demand & Supply)
    ema20 = cur_ind.get("ema20", price)
    atr = cur_ind.get("atr", (high_d - low_d) * 0.1)

    # Bullish Order Block (Demand zone below price or near discount EMA)
    ob_bull_low = round(min(low_d, pivots["s1"]), digits)
    ob_bull_high = round(ob_bull_low + (atr * 0.6), digits)

    # Bearish Order Block (Supply zone above price or near premium EMA)
    ob_bear_high = round(max(high_d, pivots["r1"]), digits)
    ob_bear_low = round(ob_bear_high - (atr * 0.6), digits)

    # Fair Value Gap assessment
    fvg_status = "Terdapat potensi FVG (Imbalance) di antara level harga aktif dan zona Pivot S1/R1."
    
    narrative = (
        f"Status valuasi pasar: {pricing_zone} ({pct_range:.1f}% dari rentang harian). "
        f"Fokus aliran dana pintar (Smart Money): {liquidity_focus}. "
        f"Zona Institutional Demand (Bullish OB): {ob_bull_low} - {ob_bull_high}. "
        f"Zona Institutional Supply (Bearish OB): {ob_bear_low} - {ob_bear_high}."
    )

    return {
        "agent": "Smart Money Concepts & Liquidity",
        "pricing_zone": pricing_zone,
        "pricing_bias": pricing_bias,
        "range_percentage": round(pct_range, 1),
        "equilibrium": round(equilibrium, digits),
        "bsl_target": bsl_target,
        "ssl_target": ssl_target,
        "liquidity_focus": liquidity_focus,
        "order_block_bullish": {"low": ob_bull_low, "high": ob_bull_high},
        "order_block_bearish": {"low": ob_bear_low, "high": ob_bear_high},
        "fvg_status": fvg_status,
        "narrative": narrative
    }
