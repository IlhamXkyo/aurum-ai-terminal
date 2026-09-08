"""
Agent 5: Chief Trade Strategist & Institutional Risk Desk
Synthesizes signals from Market Structure, Price Action, SMC/Liquidity, and Macro/Session agents.
Calculates exact Pip distances, realistic dynamic SL/TP levels, Breakeven triggers,
and prepares the on-chart visual coordinates.
"""

from typing import Dict, Any, List

def calculate_pips(symbol: str, price_diff: float) -> int:
    """Calculate pip count based on asset class conventions."""
    diff = abs(price_diff)
    if symbol == "XAUUSD":
        # In Gold, 0.10 movement = 1 pip (or $1 = 10 pips)
        return int(round(diff * 10))
    elif symbol in ("EURUSD", "GBPUSD"):
        # In Forex majors, 0.0001 = 1 pip
        return int(round(diff * 10000))
    elif symbol == "USDJPY":
        # In JPY pairs, 0.01 = 1 pip
        return int(round(diff * 100))
    else: # BTC or crypto
        return int(round(diff))


def synthesize_trade_plan(
    snapshot: Dict[str, Any],
    structure: Dict[str, Any],
    price_action: Dict[str, Any],
    smc: Dict[str, Any],
    macro: Dict[str, Any]
) -> Dict[str, Any]:
    symbol = snapshot["symbol"]
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    atr = snapshot["indicators_current_tf"].get("atr", max(price * 0.003, 1.0))
    pivots = snapshot["pivots"]

    # Point system across 4 parallel institutional agents
    bull_score = 0
    bear_score = 0

    # 1. Structure scoring (Weight: 30%)
    trend = structure.get("trend", "")
    if "BULLISH" in trend:
        bull_score += 30
    elif "BEARISH" in trend:
        bear_score += 30
    else:
        bull_score += 15
        bear_score += 15

    # 2. Price Action & Divergence scoring (Weight: 25%)
    mom = price_action.get("momentum_rating", "")
    if mom == "BULLISH":
        bull_score += 25
    elif mom == "BEARISH":
        bear_score += 25
    else:
        bull_score += 12
        bear_score += 12

    # 3. SMC Pricing & Liquidity (Weight: 25%)
    smc_bias = smc.get("pricing_bias", "")
    if smc_bias == "BULLISH_FAVORABLE":
        bull_score += 25
    elif smc_bias == "BEARISH_FAVORABLE":
        bear_score += 25
    else:
        bull_score += 12
        bear_score += 12

    # 4. Macro & Session Sentiment (Weight: 20%)
    macro_bias = macro.get("macro_bias", "")
    if "BULLISH" in macro_bias:
        bull_score += 20
    elif "BEARISH" in macro_bias:
        bear_score += 20
    else:
        bull_score += 10
        bear_score += 10

    # Decision Matrix
    if bull_score >= 70:
        action = "BUY"
        bias = "STRONG_BULLISH"
        confidence = min(bull_score + 8, 96)
    elif bull_score > bear_score + 15:
        action = "BUY"
        bias = "BULLISH"
        confidence = min(bull_score, 88)
    elif bear_score >= 70:
        action = "SELL"
        bias = "STRONG_BEARISH"
        confidence = min(bear_score + 8, 96)
    elif bear_score > bull_score + 15:
        action = "SELL"
        bias = "BEARISH"
        confidence = min(bear_score, 88)
    else:
        action = "WAIT"
        bias = "NEUTRAL / CONSOLIDATION"
        confidence = 60

    # Realistic Intraday Sizing: SL buffer 1.4x to 1.8x ATR
    sl_dist = max(atr * 1.5, price * 0.002)

    if action == "BUY":
        entry_low = round(price - (atr * 0.2), digits)
        entry_high = round(price, digits)
        entry_mid = round((entry_low + entry_high) / 2, digits)

        stop_loss = round(entry_low - sl_dist, digits)
        risk = max(entry_mid - stop_loss, 0.0001)

        tp1 = round(entry_mid + (risk * 1.5), digits)
        tp2 = round(entry_mid + (risk * 2.5), digits)

        if pivots.get("r1") and pivots["r1"] > entry_mid:
            if entry_mid + (risk * 1.2) <= pivots["r1"] <= entry_mid + (risk * 3.0):
                tp2 = round(pivots["r1"], digits)

        reward_avg = ((tp1 - entry_mid) + (tp2 - entry_mid)) / 2
        rr_ratio = round(reward_avg / risk, 2)

    elif action == "SELL":
        entry_low = round(price, digits)
        entry_high = round(price + (atr * 0.2), digits)
        entry_mid = round((entry_low + entry_high) / 2, digits)

        stop_loss = round(entry_high + sl_dist, digits)
        risk = max(stop_loss - entry_mid, 0.0001)

        tp1 = round(entry_mid - (risk * 1.5), digits)
        tp2 = round(entry_mid - (risk * 2.5), digits)

        if pivots.get("s1") and pivots["s1"] < entry_mid:
            if entry_mid - (risk * 3.0) <= pivots["s1"] <= entry_mid - (risk * 1.2):
                tp2 = round(pivots["s1"], digits)

        reward_avg = ((entry_mid - tp1) + (entry_mid - tp2)) / 2
        rr_ratio = round(reward_avg / risk, 2)

    else: # WAIT
        entry_low = round(price - (atr * 0.2), digits)
        entry_high = round(price + (atr * 0.2), digits)
        entry_mid = price
        stop_loss = round(price - (atr * 1.5), digits)
        risk = max(price - stop_loss, 0.0001)
        tp1 = round(price + (atr * 1.5), digits)
        tp2 = round(price + (atr * 2.5), digits)
        rr_ratio = 1.6

    # Exact Pip calculations
    sl_pips = calculate_pips(symbol, abs(entry_mid - stop_loss))
    tp1_pips = calculate_pips(symbol, abs(tp1 - entry_mid))
    tp2_pips = calculate_pips(symbol, abs(tp2 - entry_mid))

    # Trade Management Rules
    breakeven_trigger = f"Setelah harga mencapai TP1 (+{tp1_pips} pips), geser Stop Loss ke titik masuk ({entry_mid}) untuk mengunci posisi risk-free."
    partial_tp_rule = f"Amankan 50% lot di TP1 (+{tp1_pips} pips), biarkan sisa 50% posisi berlari menuju TP2 (+{tp2_pips} pips)."

    # Institutional Checklist
    checklist = [
        f"Struktur Pasar: {structure['trend']} ({structure['wyckoff_phase']})",
        f"Price Action: {price_action['pattern']} (Divergensi: {price_action['divergence']})",
        f"SMC Liquidity: {smc['pricing_zone']}",
        f"Sesi Pasar: {macro['session_name']} (Killzone: {'Aktif' if macro['killzone_active'] else 'Non-Aktif'})",
        f"Kalkulasi Risiko: SL {sl_pips} pips | Potensi Cuan: TP1 +{tp1_pips} pips, TP2 +{tp2_pips} pips (R:R 1 : {rr_ratio})"
    ]

    narrative = (
        f"Sintesis Konsensus: {action} ({bias}) dengan tingkat keyakinan {confidence}%. "
        f"Zona Entry di {entry_low} - {entry_high}, Stop Loss ketat di {stop_loss} ({sl_pips} pips), "
        f"Target Profit 1 di {tp1} (+{tp1_pips} pips), Target Profit 2 di {tp2} (+{tp2_pips} pips). "
        f"Rasio Risk-to-Reward terukur 1 : {rr_ratio}."
    )

    # On-Chart Visual Levels payload (consumed by frontend chart HUD)
    chart_levels = {
        "action": action,
        "entry_mid": entry_mid,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "sl_pips": sl_pips,
        "tp1_pips": tp1_pips,
        "tp2_pips": tp2_pips,
        "rr_ratio": f"1 : {rr_ratio}"
    }

    return {
        "agent": "Chief Trade Strategist & Risk Desk",
        "action": action,
        "bias": bias,
        "confidence": confidence,
        "entry_range": f"{entry_low} - {entry_high}",
        "entry_mid": entry_mid,
        "stop_loss": stop_loss,
        "sl_pips": sl_pips,
        "take_profit_1": tp1,
        "tp1_pips": tp1_pips,
        "take_profit_2": tp2,
        "tp2_pips": tp2_pips,
        "risk_reward": f"1 : {rr_ratio}",
        "breakeven_trigger": breakeven_trigger,
        "partial_tp_rule": partial_tp_rule,
        "chart_levels": chart_levels,
        "checklist": checklist,
        "narrative": narrative
    }
