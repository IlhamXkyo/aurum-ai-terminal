"""
Agent 1: Market Structure & Fractal Trend (Institutional Grade)
Analyzes multi-timeframe fractal alignment (Daily -> 4H -> Intraday),
Wyckoff structural phases (Accumulation vs Distribution),
Break of Structure (BOS), and Change of Character (CHOCH).
"""

from typing import Dict, Any, List

def analyze_market_structure(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    htf_4h = snapshot["htf_4h"]
    htf_d = snapshot["htf_daily"]
    pivots = snapshot["pivots"]
    cur_ind = snapshot["indicators_current_tf"]

    # 1. Multi-Timeframe Fractal Trend
    ema50_4h = htf_4h.get("ema50", price)
    ema200_4h = htf_4h.get("ema200", price)
    ema50_d = htf_d.get("ema50", price)
    ema200_d = htf_d.get("ema200", price)
    
    bullish_4h = price > ema50_4h and ema50_4h > ema200_4h
    bearish_4h = price < ema50_4h and ema50_4h < ema200_4h
    bullish_daily = price > ema50_d and ema50_d > ema200_d
    bearish_daily = price < ema50_d and ema50_d < ema200_d

    if bullish_4h and bullish_daily:
        trend = "BULLISH_EXPANSION"
        htf_alignment = "ALIGNED_BULLISH"
        trend_desc = "Struktur tren fraktal (Daily & 4H) searah dalam fase ekspansi bullish kuat."
    elif bearish_4h and bearish_daily:
        trend = "BEARISH_EXPANSION"
        htf_alignment = "ALIGNED_BEARISH"
        trend_desc = "Struktur tren fraktal (Daily & 4H) searah dalam fase distribusi bearish dominan."
    elif price > ema50_4h and not bullish_daily:
        trend = "COUNTER_TREND_RALLY"
        htf_alignment = "MIXED_PULLBACK"
        trend_desc = "Rally jangka pendek pada 4H sedang menguji resistensi tren utama Daily."
    elif price < ema50_4h and bullish_daily:
        trend = "HEALTHY_DISCOUNT_PULLBACK"
        htf_alignment = "MIXED_PULLBACK"
        trend_desc = "Pullback sehat ke area discount pada tren makro Daily yang masih bullish."
    else:
        trend = "CONSOLIDATION_RANGE"
        htf_alignment = "NEUTRAL"
        trend_desc = "Harga berkonsolidasi dalam rentang rangebound."

    # 2. Wyckoff Phase Assessment
    rsi_4h = htf_4h.get("rsi", 50.0)
    if bullish_4h and rsi_4h > 60:
        wyckoff_phase = "Phase E (Markup / Trend Running)"
    elif bearish_4h and rsi_4h < 40:
        wyckoff_phase = "Phase E (Markdown / Selloff Running)"
    elif price <= pivots["s1"] and rsi_4h <= 38:
        wyckoff_phase = "Phase C (Spring / Potential Wyckoff Accumulation Trap)"
    elif price >= pivots["r1"] and rsi_4h >= 65:
        wyckoff_phase = "Phase C (UTAD / Upthrust After Distribution Trap)"
    else:
        wyckoff_phase = "Phase B (Building Cause / Liquidity Accumulation)"

    # 3. Key Institutional Levels (Daily Pivots)
    key_levels: List[Dict[str, Any]] = [
        {"name": "Resistance 2 (R2)", "price": round(pivots["r2"], digits), "type": "RESISTANCE"},
        {"name": "Resistance 1 (R1)", "price": round(pivots["r1"], digits), "type": "RESISTANCE"},
        {"name": "Daily Pivot Equilibrium", "price": round(pivots["middle"], digits), "type": "EQUILIBRIUM"},
        {"name": "Support 1 (S1)", "price": round(pivots["s1"], digits), "type": "SUPPORT"},
        {"name": "Support 2 (S2)", "price": round(pivots["s2"], digits), "type": "SUPPORT"},
    ]

    # 4. BOS (Break of Structure) & CHOCH (Change of Character)
    if price > pivots["r1"]:
        bos_signal = "BOS Bullish terkonfirmasi di atas R1 (Struktur higher-high terjaga)"
        structure_state = "BOS_BULLISH"
    elif price < pivots["s1"]:
        bos_signal = "BOS Bearish terkonfirmasi di bawah S1 (Struktur lower-low mendominasi)"
        structure_state = "BOS_BEARISH"
    elif price > pivots["middle"]:
        bos_signal = "Holding di atas Pivot Harian - Pembeli mengontrol area equilibrium"
        structure_state = "BULLISH_HOLD"
    else:
        bos_signal = "Trading di bawah Pivot Harian - Penjual menekan di bawah equilibrium"
        structure_state = "BEARISH_HOLD"

    narrative = f"{trend_desc} Fase Wyckoff: {wyckoff_phase}. Status struktur: {bos_signal}."

    return {
        "agent": "Market Structure & Fractal Trend",
        "trend": trend,
        "htf_alignment": htf_alignment,
        "structure_state": structure_state,
        "wyckoff_phase": wyckoff_phase,
        "ema50_4h": round(ema50_4h, digits),
        "ema200_4h": round(ema200_4h, digits),
        "pivot_point": round(pivots["middle"], digits),
        "key_levels": key_levels,
        "bos_signal": bos_signal,
        "narrative": narrative
    }
