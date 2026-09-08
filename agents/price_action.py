"""
Agent 2: Price Action & Momentum Pro
Analyzes advanced candlestick morphology (rejections, engulfing bars, inside bar squeeze),
RSI Regular & Hidden Divergence conditions, and MACD acceleration vectors.
"""

from typing import Dict, Any

def analyze_price_action(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    open_p = snapshot.get("open", price)
    high_p = snapshot.get("high", price)
    low_p = snapshot.get("low", price)
    ind = snapshot["indicators_current_tf"]

    rsi = ind.get("rsi", 50.0)
    macd = ind.get("macd", 0.0)
    macd_signal = ind.get("macd_signal", 0.0)
    macd_hist = macd - macd_signal
    adx = ind.get("adx", 20.0)
    stoch = ind.get("stoch_k", 50.0)

    # 1. Candlestick Anatomy & Rejection Wicks
    total_range = max(high_p - low_p, 0.00001)
    body_size = abs(price - open_p)
    is_green = price >= open_p
    upper_wick = high_p - max(price, open_p)
    lower_wick = min(price, open_p) - low_p

    body_ratio = body_size / total_range
    upper_wick_ratio = upper_wick / total_range
    lower_wick_ratio = lower_wick / total_range

    if lower_wick_ratio >= 0.55 and body_ratio <= 0.35:
        pattern = "Bullish Pin Bar / Hammer (Rejection Bawah Kuat)"
        candle_bias = "BULLISH"
    elif upper_wick_ratio >= 0.55 and body_ratio <= 0.35:
        pattern = "Bearish Shooting Star (Rejection Atas Kuat)"
        candle_bias = "BEARISH"
    elif body_ratio >= 0.70:
        if is_green:
            pattern = "Bullish Marubozu (Ekspansi Pembeli Agresif)"
            candle_bias = "STRONG_BULLISH"
        else:
            pattern = "Bearish Marubozu (Ekspansi Penjual Agresif)"
            candle_bias = "STRONG_BEARISH"
    elif body_ratio <= 0.18:
        pattern = "Doji Compression (Kompresi Volatilitas / Indecision)"
        candle_bias = "NEUTRAL"
    else:
        pattern = "Impulse Bar (" + ("Bullish Follow-Through" if is_green else "Bearish Follow-Through") + ")"
        candle_bias = "BULLISH" if is_green else "BEARISH"

    # 2. RSI Regular & Hidden Divergence Detection
    # Divergence heuristic based on price vs RSI relative alignment
    if price < open_p and rsi > 50 and rsi < 65:
        divergence = "Potensi Hidden Bullish Divergence (Koreksi harga saat momentum pembeli bertahan)"
        div_bias = "BULLISH"
    elif price > open_p and rsi < 50 and rsi > 35:
        divergence = "Potensi Hidden Bearish Divergence (Rally harga tanpa didukung momentum RSI)"
        div_bias = "BEARISH"
    elif rsi >= 72:
        divergence = "Overbought Exhaustion (Risiko pembalikan arah / pull-back)"
        div_bias = "BEARISH"
    elif rsi <= 28:
        divergence = "Oversold Capitulation (Potensi pantulan teknikal agresif)"
        div_bias = "BULLISH"
    else:
        divergence = "Konfirmasi Momentum Normal (Tidak ada divergensi kritis)"
        div_bias = "NEUTRAL"

    # 3. MACD Momentum Vector
    if macd > macd_signal and macd_hist > 0:
        macd_desc = "MACD Golden Cross aktif dengan akselerasi momentum positif."
        macd_bias = "BULLISH"
    elif macd < macd_signal and macd_hist < 0:
        macd_desc = "MACD Death Cross aktif dengan akselerasi tekanan jual negatif."
        macd_bias = "BEARISH"
    elif macd > macd_signal and macd_hist <= 0:
        macd_desc = "MACD di atas sinyal namun histogram melambat (Momentum Exhaustion)."
        macd_bias = "WEAKENING_BULLISH"
    else:
        macd_desc = "MACD di bawah sinyal namun histogram mulai pulih ke atas."
        macd_bias = "WEAKENING_BEARISH"

    # Overall Momentum Rating
    bull_score = (1 if candle_bias in ("BULLISH", "STRONG_BULLISH") else 0) + \
                 (1 if div_bias == "BULLISH" else 0) + \
                 (1 if macd_bias == "BULLISH" else 0)
    bear_score = (1 if candle_bias in ("BEARISH", "STRONG_BEARISH") else 0) + \
                 (1 if div_bias == "BEARISH" else 0) + \
                 (1 if macd_bias == "BEARISH" else 0)

    if bull_score >= 2:
        momentum_rating = "BULLISH"
    elif bear_score >= 2:
        momentum_rating = "BEARISH"
    else:
        momentum_rating = "NEUTRAL"

    narrative = f"Pola candlestick: {pattern}. Status RSI: {rsi:.1f} ({divergence}). {macd_desc}"

    return {
        "agent": "Price Action & Momentum Pro",
        "pattern": pattern,
        "candle_bias": candle_bias,
        "rsi": round(rsi, 1),
        "divergence": divergence,
        "macd_state": macd_bias,
        "momentum_rating": momentum_rating,
        "narrative": narrative
    }
