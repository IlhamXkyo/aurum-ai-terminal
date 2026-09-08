"""
Agent 1: Market Structure & Higher Timeframe (HTF) Trend
Analyzes market structure breaks (BOS), change of character (CHOCH),
EMA trend filters, and institutional pivot support/resistance levels.
"""

from typing import Dict, Any, List

def analyze_market_structure(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    htf_4h = snapshot["htf_4h"]
    htf_d = snapshot["htf_daily"]
    pivots = snapshot["pivots"]
    cur_ind = snapshot["indicators_current_tf"]

    # 4H EMA Trend Assessment
    ema50_4h = htf_4h.get("ema50", price)
    ema200_4h = htf_4h.get("ema200", price)
    
    bullish_4h = price > ema50_4h and ema50_4h > ema200_4h
    bearish_4h = price < ema50_4h and ema50_4h < ema200_4h
    
    # Alignment with Daily
    ema50_d = htf_d.get("ema50", price)
    ema200_d = htf_d.get("ema200", price)
    bullish_daily = price > ema50_d
    bearish_daily = price < ema50_d

    if bullish_4h and bullish_daily:
        trend = "BULLISH"
        htf_alignment = "ALIGNED_BULLISH"
        structure_desc = "Struktur pasar HTF (4H & Daily) dalam fase uptrend yang solid. Harga bertengger di atas EMA 50 & EMA 200."
    elif bearish_4h and bearish_daily:
        trend = "BEARISH"
        htf_alignment = "ALIGNED_BEARISH"
        structure_desc = "Struktur pasar HTF (4H & Daily) dalam fase downtrend dominan. Tekanan jual menekan harga di bawah EMA 50 & 200."
    elif price > ema50_4h and not bullish_daily:
        trend = "BULLISH_RECOVERY"
        htf_alignment = "MIXED_PULLBACK"
        structure_desc = "Pemulihan bullish jangka pendek pada 4H, namun berhadapan dengan resistensi struktur Daily."
    elif price < ema50_4h and bullish_daily:
        trend = "HEALTHY_RETRACEMENT"
        htf_alignment = "MIXED_PULLBACK"
        structure_desc = "Retracement sehat pada tren utama Daily. Harga sedang menguji area demand 4H."
    else:
        trend = "SIDEWAYS / CONSOLIDATION"
        htf_alignment = "NEUTRAL"
        structure_desc = "Pasar berada di zona konsolidasi atau akumulasi rangebound."

    # Key Institutional Levels
    key_levels: List[Dict[str, Any]] = [
        {"name": "Resistance 2 (R2)", "price": round(pivots["r2"], digits), "type": "RESISTANCE"},
        {"name": "Resistance 1 (R1)", "price": round(pivots["r1"], digits), "type": "RESISTANCE"},
        {"name": "Pivot Central Point", "price": round(pivots["middle"], digits), "type": "EQUILIBRIUM"},
        {"name": "Support 1 (S1)", "price": round(pivots["s1"], digits), "type": "SUPPORT"},
        {"name": "Support 2 (S2)", "price": round(pivots["s2"], digits), "type": "SUPPORT"},
    ]

    # BOS & CHOCH assessment
    if price > pivots["r1"]:
        bos_signal = "BOS Bullish terkonfirmasi (Harga berhasil menembus R1, mengincar R2)"
        structure_state = "EXPANSION_UP"
    elif price < pivots["s1"]:
        bos_signal = "BOS Bearish terkonfirmasi (Harga breakdown di bawah S1, mengincar S2)"
        structure_state = "EXPANSION_DOWN"
    elif price > pivots["middle"]:
        bos_signal = "Holding di atas Pivot Central - Menunjukkan kekuatan pembeli mempertahankan level kontrol."
        structure_state = "BULLISH_CONTROL"
    else:
        bos_signal = "Trading di bawah Pivot Central - Penjual mendominasi distribusi harga intraday."
        structure_state = "BEARISH_CONTROL"

    return {
        "agent": "Market Structure & Trend",
        "trend": trend,
        "htf_alignment": htf_alignment,
        "structure_state": structure_state,
        "ema50_4h": round(ema50_4h, digits),
        "ema200_4h": round(ema200_4h, digits),
        "pivot_point": round(pivots["middle"], digits),
        "key_levels": key_levels,
        "bos_signal": bos_signal,
        "narrative": f"{structure_desc} {bos_signal}"
    }
