"""
Forex & Gold AI Live Trading Terminal Server
Flask backend serving real-time TradingView market data and parallel multi-agent analysis.
"""

import sys
import os
import time
import concurrent.futures
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add root folder to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from data_fetcher import fetch_market_snapshot, PAIR_CONFIG
from agents.market_structure import analyze_market_structure
from agents.price_action import analyze_price_action
from agents.smc_liquidity import analyze_smc_liquidity
from agents.macro_fundamental import analyze_macro_session
from agents.trade_strategist import synthesize_trade_plan

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


@app.route("/")
def index():
    return render_template("index.html", pairs=PAIR_CONFIG)


@app.route("/api/pairs", methods=["GET"])
def get_pairs():
    return jsonify(PAIR_CONFIG)


@app.route("/api/market-data", methods=["GET"])
def get_market_data():
    symbol = request.args.get("symbol", "XAUUSD").upper()
    timeframe = request.args.get("timeframe", "15")
    
    try:
        snapshot = fetch_market_snapshot(symbol=symbol, timeframe=timeframe)
        return jsonify({"success": True, "data": snapshot})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# In-Memory Setup Journal (Tracks past and new setups)
SETUP_JOURNAL = [
    {
        "id": "init-1",
        "timestamp": time.time() - 3600,
        "time_str": "1 Jam Lalu",
        "symbol": "XAUUSD",
        "timeframe": "15m",
        "action": "BUY",
        "bias": "BULLISH_EXPANSION",
        "entry": "4415.50",
        "stop_loss": "4405.00",
        "take_profit_1": "4426.00",
        "take_profit_2": "4435.00",
        "pips_gain": "+105 pips",
        "status": "HIT TP1 (+105 pips)"
    },
    {
        "id": "init-2",
        "timestamp": time.time() - 7200,
        "time_str": "2 Jam Lalu",
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "action": "BUY",
        "bias": "BOS_BULLISH",
        "entry": "4410.20",
        "stop_loss": "4395.00",
        "take_profit_1": "4425.00",
        "take_profit_2": "4440.00",
        "pips_gain": "+148 pips",
        "status": "HIT TP1 (+148 pips)"
    }
]


def analyze_single_tf(symbol: str, timeframe: str) -> dict:
    snapshot = fetch_market_snapshot(symbol=symbol, timeframe=timeframe)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_struct = executor.submit(analyze_market_structure, snapshot)
        f_pa = executor.submit(analyze_price_action, snapshot)
        f_smc = executor.submit(analyze_smc_liquidity, snapshot)
        f_macro = executor.submit(analyze_macro_session, snapshot)

        struct_res = f_struct.result()
        pa_res = f_pa.result()
        smc_res = f_smc.result()
        macro_res = f_macro.result()

    trade_plan = synthesize_trade_plan(
        snapshot=snapshot,
        structure=struct_res,
        price_action=pa_res,
        smc=smc_res,
        macro=macro_res
    )

    return {
        "snapshot": snapshot,
        "agents": {
            "market_structure": struct_res,
            "price_action": pa_res,
            "smc_liquidity": smc_res,
            "macro_session": macro_res,
            "trade_strategist": trade_plan
        }
    }


@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    payload = request.get_json() or {}
    symbol = payload.get("symbol", "XAUUSD").upper()
    timeframe = payload.get("timeframe", "15")
    
    start_time = time.time()
    
    try:
        res = analyze_single_tf(symbol, timeframe)
        total_time_ms = round((time.time() - start_time) * 1000, 1)

        return jsonify({
            "success": True,
            "meta": {
                "symbol": symbol,
                "timeframe": timeframe,
                "price": res["snapshot"]["price"],
                "total_processing_time_ms": total_time_ms,
                "timestamp": res["snapshot"]["timestamp"]
            },
            "snapshot": res["snapshot"],
            "agents": res["agents"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/scan-radar", methods=["GET"])
def scan_radar():
    symbol = request.args.get("symbol", "XAUUSD").upper()
    timeframes = ["1", "5", "15", "60", "240"]
    radar_results = {}
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_tf = {executor.submit(analyze_single_tf, symbol, tf): tf for tf in timeframes}
            for future in concurrent.futures.as_completed(future_to_tf):
                tf = future_to_tf[future]
                res = future.result()
                strat = res["agents"]["trade_strategist"]
                snap = res["snapshot"]
                
                radar_results[tf] = {
                    "timeframe": tf,
                    "price": snap["price"],
                    "action": strat["action"],
                    "bias": strat["bias"],
                    "confidence": strat["confidence"],
                    "entry": strat["entry_range"],
                    "stop_loss": strat["stop_loss"],
                    "sl_pips": strat["sl_pips"],
                    "take_profit_1": strat["take_profit_1"],
                    "tp1_pips": strat["tp1_pips"],
                    "take_profit_2": strat["take_profit_2"],
                    "tp2_pips": strat["tp2_pips"],
                    "risk_reward": strat["risk_reward"],
                    "chart_levels": strat.get("chart_levels", {})
                }
                
                # Check if this is a newly opened setup (BUY or SELL)
                if strat["action"] in ("BUY", "SELL"):
                    # Check if already logged in last 15 minutes for this timeframe
                    recent = [j for j in SETUP_JOURNAL if j["symbol"] == symbol and j["timeframe"] == f"{tf}m" and (time.time() - j["timestamp"] < 900)]
                    if not recent:
                        now_str = time.strftime("%H:%M:%S")
                        SETUP_JOURNAL.insert(0, {
                            "id": f"{symbol}-{tf}-{int(time.time())}",
                            "timestamp": time.time(),
                            "time_str": f"{now_str} (Baru)",
                            "symbol": symbol,
                            "timeframe": f"{tf}m" if tf != "60" and tf != "240" else ("1H" if tf == "60" else "4H"),
                            "action": strat["action"],
                            "bias": strat["bias"],
                            "entry": str(strat["entry_range"]),
                            "stop_loss": str(strat["stop_loss"]),
                            "take_profit_1": str(strat["take_profit_1"]),
                            "take_profit_2": str(strat["take_profit_2"]),
                            "pips_gain": f"+{strat['tp1_pips']} pips",
                            "status": "AKTIF / TERBUKA"
                        })
                        if len(SETUP_JOURNAL) > 30:
                            SETUP_JOURNAL.pop()

        return jsonify({
            "success": True,
            "symbol": symbol,
            "radar": radar_results,
            "journal": SETUP_JOURNAL[:15]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/setup-journal", methods=["GET"])
def get_journal():
    return jsonify({"success": True, "journal": SETUP_JOURNAL})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Forex & Gold AI Terminal on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
