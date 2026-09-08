"""
Agent 2: Price Action & Momentum
Analyzes candlestick dynamics (wicks, rejections, engulfing bars),
RSI momentum & overbought/oversold states, and MACD trend acceleration.
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

    # Candlestick anatomy
    total_range = max(high_p - low_p, 0.00001)
    body_size = abs(price - open_p)
    is_green = price >= open_p
    upper_wick = high_p - max(price, open_p)
    lower_wick = min(price, open_p) - low_p

    body_ratio = body_size / total_range
    upper_wick_ratio = upper_wick / total_range
    lower_wick_ratio = lower_wick / total_range

    # Detect candle pattern
    if lower_wick_ratio >= 0.55 and body_ratio <= 0.35:
        pattern = "Bullish Pin Bar / Hammer (Penolakan Kuat di Zona Bawah)"
        candle_bias = "BULLISH"
    elif upper_wick_ratio >= 0.55 and body_ratio <= 0.35:
        pattern = "Bearish Shooting Star / Inverted Pin Bar (Penolakan di Zona Atas)"
        candle_bias = "BEARISH"
    elif body_ratio >= 0.70:
        if is_green:
            pattern = "Bullish Marubozu / Strong Expansion Candle"
            candle_bias = "STRONG_BULLISH"
        else:
            pattern = "Bearish Marubozu / Strong Sell Impulse"
            candle_bias = "STRONG_BEARISH"
    elif body_ratio <= 0.15:
        pattern = "Doji (Konsolidasi & Keraguan Pelaku Pasar)"
        candle_bias = "NEUTRAL"
    else:
        pattern = "Standard Candle (" + ("Bullish Continuation" if is_green else "Bearish Continuation") + ")"
        candle_bias = "BULLISH" if is_green else "BEARISH"

    # RSI Analysis
    if rsi >= 70:
        rsi_desc = f"RSI {rsi:.1f} (Zona Overbought - Waspada Exhaustion / Koreksi)"
        rsi_state = "OVERBOUGHT"
    elif rsi <= 30:
        rsi_desc = f"RSI {rsi:.1f} (Zona Oversold - Potensi Technical Bounce)"
        rsi_state = "OVERSOLD"
    elif rsi >= 55:
        rsi_desc = f"RSI {rsi:.1f} (Bullish Momentum Zone - Akumulasi Terkendali)"
        rsi_state = "BULLISH"
    elif rsi <= 45:
        rsi_desc = f"RSI {rsi:.1f} (Bearish Momentum Zone - Distribusi Aktif)"
        rsi_state = "BEARISH"
    else:
        rsi_desc = f"RSI {rsi:.1f} (Zona Netral 50 Equilibrium)"
        rsi_state = "NEUTRAL"

    # MACD Analysis
    if macd > macd_signal and macd_hist > 0:
        macd_desc = "MACD Bullish Cross dengan histogram mengembang positif."
        macd_bias = "BULLISH"
    elif macd < macd_signal and macd_hist < 0:
        macd_desc = "MACD Bearish Cross dengan histogram melemah negatif."
        macd_bias = "BEARISH"
    elif macd > macd_signal and macd_hist <= 0:
        macd_desc = "MACD di atas sinyal namun momentum histogram mulai menyusut."
        macd_bias = "WEAKENING_BULLISH"
    else:
        macd_desc = "MACD di bawah sinyal namun tekanan jual mulai melambat."
        macd_bias = "WEAKENING_BEARISH"

    # Trend Strength via ADX
    if adx > 28:
        trend_strength = f"Sangat Kuat (ADX: {adx:.1f})"
    elif adx > 20:
        trend_strength = f"Sedang / Aktif (ADX: {adx:.1f})"
    else:
        trend_strength = f"Lemah / Choppy Range (ADX: {adx:.1f})"

    # Overall Momentum Bias
    bull_points = (1 if candle_bias in ("BULLISH", "STRONG_BULLISH") else 0) + \
                  (1 if rsi_state in ("BULLISH", "OVERSOLD") else 0) + \
                  (1 if macd_bias == "BULLISH" else 0)
    bear_points = (1 if candle_bias in ("BEARISH", "STRONG_BEARISH") else 0) + \
                  (1 if rsi_state in ("BEARISH", "OVERBOUGHT") else 0) + \
                  (1 if macd_bias == "BEARISH" else 0)

    if bull_points >= 2:
        momentum_rating = "BULLISH"
    elif bear_points >= 2:
        momentum_rating = "BEARISH"
    else:
        momentum_rating = "NEUTRAL"

    narrative = f"Pola candlestick: {pattern}. {rsi_desc}. {macd_desc} Kekuatan tren saat ini: {trend_strength}."

    return {
        "agent": "Price Action & Momentum",
        "pattern": pattern,
        "candle_bias": candle_bias,
        "rsi": round(rsi, 1),
        "rsi_state": rsi_state,
        "macd_state": macd_bias,
        "trend_strength": trend_strength,
        "momentum_rating": momentum_rating,
        "narrative": narrative
    }
