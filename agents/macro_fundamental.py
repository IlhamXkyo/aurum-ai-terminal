"""
Agent 4: Macro & Market Session Analyst
Analyzes intermarket macro drivers, Dollar Index (DXY) inverse correlation,
Global Risk Sentiment (Risk-On vs Risk-Off), and Trading Session Killzones
(Asian Range, London Open, New York Session, and London-NY Overlap).
"""

from datetime import datetime, timezone
from typing import Dict, Any

def analyze_macro_session(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    symbol = snapshot["symbol"]
    price = snapshot["price"]
    change_pct = snapshot.get("change_pct", 0.0)

    # 1. Trading Session & Killzone Detection (UTC Time)
    now_utc = datetime.now(timezone.utc)
    hour_utc = now_utc.hour + (now_utc.minute / 60.0)

    session_name = "Off-Peak / Quiet Hours"
    killzone_active = False
    killzone_desc = "Volatilitas rendah di luar jam pasar utama."

    # Sessions:
    # Asian: 00:00 - 08:00 UTC
    # London: 07:00 - 15:30 UTC
    # New York: 12:00 - 20:30 UTC
    # London-NY Overlap (Peak Killzone): 12:00 - 15:30 UTC

    if 12.0 <= hour_utc <= 15.5:
        session_name = "LONDON - NEW YORK OVERLAP KILLZONE"
        killzone_active = True
        killzone_desc = "Zona likuiditas tertinggi dunia. Pelaku institusional aktif mengeksekusi order volume besar."
    elif 12.0 <= hour_utc <= 20.5:
        session_name = "NEW YORK SESSION (US Market)"
        killzone_active = True
        killzone_desc = "Sesi New York aktif. Pergerakan dipengaruhi rilis data ekonomi AS & pergerakan imbal hasil obligasi."
    elif 7.0 <= hour_utc <= 15.5:
        session_name = "LONDON SESSION (European Market)"
        killzone_active = True
        killzone_desc = "Sesi London aktif. Sering terjadi manipulasi/sweep terhadap rentang sesi Asia (Judas Swing)."
    elif 0.0 <= hour_utc <= 8.0:
        session_name = "ASIAN SESSION (Tokyo / Sydney)"
        killzone_active = False
        killzone_desc = "Sesi Asia sedang membentuk rentang konsolidasi akumulasi likuiditas (Asian Range)."

    # 2. Intermarket & Macro Bias
    # For Gold (XAUUSD) & Majors (EURUSD, GBPUSD), DXY (US Dollar Index) is inversely correlated
    if symbol in ("XAUUSD", "EURUSD", "GBPUSD"):
        is_inverse_to_usd = True
    elif symbol == "USDJPY":
        is_inverse_to_usd = False
    else:
        is_inverse_to_usd = True

    # Assess Macro Momentum from Daily Change & HTF Indicators
    htf_d = snapshot.get("htf_daily", {})
    rsi_d = htf_d.get("rsi", 50.0)

    if symbol == "XAUUSD":
        asset_nature = "Safe-Haven Komoditas & Lindung Nilai Inflasi"
        if rsi_d >= 55:
            macro_flow = "Risk-Off Safe Haven Demand (Permintaan lindung nilai emas kuat)"
            macro_bias = "BULLISH_MACRO"
        elif rsi_d <= 45:
            macro_flow = "Dolar AS Menguat / Yield Obligasi Naik (Tekanan jual pada aset non-yield)"
            macro_bias = "BEARISH_MACRO"
        else:
            macro_flow = "Konsolidasi Makro Menjelang Rilis Data Ekonomi AS"
            macro_bias = "NEUTRAL_MACRO"
    else:
        asset_nature = "Forex Major Currency Pair"
        if change_pct > 0.15:
            macro_flow = "Arus modal masuk ke mata uang dasar vs Dolar AS"
            macro_bias = "BULLISH_MACRO"
        elif change_pct < -0.15:
            macro_flow = "Dolar AS menguat secara luas di pasar valuta asing"
            macro_bias = "BEARISH_MACRO"
        else:
            macro_flow = "Aliran dana seimbang di pasar mata uang"
            macro_bias = "NEUTRAL_MACRO"

    narrative = (
        f"Sesi Pasar: {session_name}. {killzone_desc} "
        f"Karakteristik Aset ({symbol}): {asset_nature}. "
        f"Dinamika Makro: {macro_flow}."
    )

    return {
        "agent": "Macro & Session Analyst",
        "session_name": session_name,
        "killzone_active": killzone_active,
        "killzone_desc": killzone_desc,
        "macro_bias": macro_bias,
        "macro_flow": macro_flow,
        "asset_nature": asset_nature,
        "utc_time": now_utc.strftime("%H:%M UTC"),
        "narrative": narrative
    }
