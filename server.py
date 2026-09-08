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


@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    payload = request.get_json() or {}
    symbol = payload.get("symbol", "XAUUSD").upper()
    timeframe = payload.get("timeframe", "15")
    
    start_time = time.time()
    
    try:
        # 1. Fetch live snapshot
        snapshot = fetch_market_snapshot(symbol=symbol, timeframe=timeframe)
        
        # 2. Run Agent 1, 2, and 3 in PARALLEL via ThreadPoolExecutor
        agent_start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_structure = executor.submit(analyze_market_structure, snapshot)
            future_price_action = executor.submit(analyze_price_action, snapshot)
            future_smc = executor.submit(analyze_smc_liquidity, snapshot)
            
            structure_res = future_structure.result()
            price_action_res = future_price_action.result()
            smc_res = future_smc.result()
        agent_time_ms = round((time.time() - agent_start) * 1000, 1)

        # 3. Agent 4: Chief Strategist synthesizes the 3 parallel agents
        trade_plan = synthesize_trade_plan(
            snapshot=snapshot,
            structure=structure_res,
            price_action=price_action_res,
            smc=smc_res
        )

        total_time_ms = round((time.time() - start_time) * 1000, 1)

        return jsonify({
            "success": True,
            "meta": {
                "symbol": symbol,
                "timeframe": timeframe,
                "price": snapshot["price"],
                "parallel_execution_time_ms": agent_time_ms,
                "total_processing_time_ms": total_time_ms,
                "timestamp": snapshot["timestamp"]
            },
            "snapshot": snapshot,
            "agents": {
                "market_structure": structure_res,
                "price_action": price_action_res,
                "smc_liquidity": smc_res,
                "trade_strategist": trade_plan
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Forex & Gold AI Terminal on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
