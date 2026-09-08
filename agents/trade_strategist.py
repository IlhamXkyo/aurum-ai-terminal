"""
Agent 4: Chief Trade Strategist & Synthesizer
Synthesizes signals from Market Structure, Price Action, and SMC/Liquidity agents
to generate a high-conviction trade plan with Entry, SL, TP1, TP2, and Risk/Reward.
"""

from typing import Dict, Any, List

def synthesize_trade_plan(
    snapshot: Dict[str, Any],
    structure: Dict[str, Any],
    price_action: Dict[str, Any],
    smc: Dict[str, Any]
) -> Dict[str, Any]:
    price = snapshot["price"]
    digits = snapshot.get("digits", 2)
    atr = snapshot["indicators_current_tf"].get("atr", price * 0.003)
    pivots = snapshot["pivots"]

    # Point system across 3 parallel agents
    bull_score = 0
    bear_score = 0

    # 1. Structure scoring (Weight: 35%)
    trend = structure.get("trend", "")
    if "BULLISH" in trend:
        bull_score += 35
    elif "BEARISH" in trend:
        bear_score += 35
    else:
        bull_score += 15
        bear_score += 15

    # 2. Price Action scoring (Weight: 30%)
    mom = price_action.get("momentum_rating", "")
    if mom == "BULLISH":
        bull_score += 30
    elif mom == "BEARISH":
        bear_score += 30
    else:
        bull_score += 15
        bear_score += 15

    # 3. SMC Pricing & Liquidity (Weight: 35%)
    smc_bias = smc.get("pricing_bias", "")
    if smc_bias == "BULLISH_FAVORABLE":
        bull_score += 35
    elif smc_bias == "BEARISH_FAVORABLE":
        bear_score += 35
    else:
        bull_score += 15
        bear_score += 15

    # Determine Bias & Action
    if bull_score >= 70:
        action = "BUY"
        bias = "STRONG_BULLISH"
        confidence = min(bull_score + 10, 95)
    elif bull_score > bear_score + 15:
        action = "BUY"
        bias = "BULLISH"
        confidence = min(bull_score, 88)
    elif bear_score >= 70:
        action = "SELL"
        bias = "STRONG_BEARISH"
        confidence = min(bear_score + 10, 95)
    elif bear_score > bull_score + 15:
        action = "SELL"
        bias = "BEARISH"
        confidence = min(bear_score, 88)
    else:
        action = "WAIT"
        bias = "NEUTRAL / RANGING"
        confidence = 60

    # Calculate Realistic Intraday Entry, SL, TP1, TP2, and R:R based on ATR & Local Structure
    # On 15m/1h, SL should be based on recent swing / ATR buffer (e.g. 1.2x to 1.8x ATR)
    sl_distance = max(atr * 1.5, price * 0.002)

    if action == "BUY":
        entry_low = round(price - (atr * 0.2), digits)
        entry_high = round(price, digits)
        entry_mid = (entry_low + entry_high) / 2
        
        # Stop Loss placed logically below entry based on ATR buffer
        stop_loss = round(entry_low - sl_distance, digits)
        risk = max(entry_mid - stop_loss, 0.0001)

        # TP targets based on realistic Risk-to-Reward (1:1.5 and 1:2.5)
        tp1 = round(entry_mid + (risk * 1.5), digits)
        tp2 = round(entry_mid + (risk * 2.5), digits)
        
        # If daily R1 is near and above TP1, it can serve as a logical TP target
        if pivots.get("r1") and pivots["r1"] > entry_mid:
            if entry_mid + (risk * 1.2) <= pivots["r1"] <= entry_mid + (risk * 3.0):
                tp2 = round(pivots["r1"], digits)

        reward_avg = ((tp1 - entry_mid) + (tp2 - entry_mid)) / 2
        rr_ratio = round(reward_avg / risk, 2)
        
    elif action == "SELL":
        entry_low = round(price, digits)
        entry_high = round(price + (atr * 0.2), digits)
        entry_mid = (entry_low + entry_high) / 2
        
        # Stop Loss placed logically above entry based on ATR buffer
        stop_loss = round(entry_high + sl_distance, digits)
        risk = max(stop_loss - entry_mid, 0.0001)

        # TP targets based on realistic Risk-to-Reward (1:1.5 and 1:2.5)
        tp1 = round(entry_mid - (risk * 1.5), digits)
        tp2 = round(entry_mid - (risk * 2.5), digits)

        # If daily S1 is near and below TP1, it can serve as a logical TP target
        if pivots.get("s1") and pivots["s1"] < entry_mid:
            if entry_mid - (risk * 3.0) <= pivots["s1"] <= entry_mid - (risk * 1.2):
                tp2 = round(pivots["s1"], digits)

        reward_avg = ((entry_mid - tp1) + (entry_mid - tp2)) / 2
        rr_ratio = round(reward_avg / risk, 2)

    else: # WAIT
        entry_low = round(price - (atr * 0.2), digits)
        entry_high = round(price + (atr * 0.2), digits)
        stop_loss = round(price - (atr * 1.5), digits)
        tp1 = round(price + (atr * 1.5), digits)
        tp2 = round(price + (atr * 2.5), digits)
        rr_ratio = 1.6

    # Tactical Checklist
    checklist = [
        f"Struktur Pasar: {structure['trend']} (Kesesuaian HTF: {structure['htf_alignment']})",
        f"Price Action: {price_action['pattern']} | RSI: {price_action['rsi']} ({price_action['rsi_state']})",
        f"Smart Money: {smc['pricing_zone']}",
        f"Target Likuiditas Utama: {smc['bsl_target'] if action == 'BUY' else smc['ssl_target']}",
        f"Kalkulasi Rasio Risiko terhadap Imbalan (R:R): 1 : {rr_ratio}"
    ]

    narrative = (
        f"Keputusan Konsensus Agen: {action} ({bias}) dengan tingkat keyakinan {confidence}%. "
        f"Zona Entry di rentang {entry_low} - {entry_high}, Invalidation/Stop Loss ketat di {stop_loss}, "
        f"Target Profit 1 di {tp1} dan Target Profit 2 di {tp2} (Proyeksi R:R 1 : {rr_ratio})."
    )

    return {
        "agent": "Chief Trade Strategist",
        "action": action,
        "bias": bias,
        "confidence": confidence,
        "entry_range": f"{entry_low} - {entry_high}",
        "stop_loss": stop_loss,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "risk_reward": f"1 : {rr_ratio}",
        "checklist": checklist,
        "narrative": narrative
    }
