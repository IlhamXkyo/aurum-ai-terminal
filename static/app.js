// State
let currentSymbol = "XAUUSD";
let currentTimeframe = "15";
let autoTickRefresh = true;
let autoAiStream = true;
let tvWidget = null;
let lastPrice = 0;
let tickTimer = null;
let aiStreamTimer = null;
let isAnalyzing = false;

// Ticker Mapping for TradingView Widget
const TV_TICKER_MAP = {
    "XAUUSD": "OANDA:XAUUSD",
    "EURUSD": "FX:EURUSD",
    "GBPUSD": "FX:GBPUSD",
    "USDJPY": "FX:USDJPY",
    "BTCUSD": "BITSTAMP:BTCUSD"
};

// Timeframe mapping for TradingView Widget (1, 5, 15, 60, 240, D)
const TV_INTERVAL_MAP = {
    "1": "1",
    "5": "5",
    "15": "15",
    "60": "60",
    "240": "240",
    "1D": "D"
};

const TF_LABELS = {
    "1": "1 Menit",
    "5": "5 Menit",
    "15": "15 Menit",
    "60": "1 Jam (60m)",
    "240": "4 Jam (240m)",
    "1D": "Daily (1 Hari)"
};

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    initTradingViewChart();
    setupEventListeners();
    fetchMarketSnapshot();
    runParallelAnalysis();

    // Start auto polling loops
    startPollingLoops();
});

// 1. Initialize TradingView Advanced Chart Widget
function initTradingViewChart() {
    const container = document.getElementById("tradingview_widget");
    if (!container) return;
    container.innerHTML = "";

    const tvTicker = TV_TICKER_MAP[currentSymbol] || "OANDA:XAUUSD";
    const tvInterval = TV_INTERVAL_MAP[currentTimeframe] || "15";

    if (typeof TradingView !== "undefined") {
        tvWidget = new TradingView.widget({
            autosize: true,
            symbol: tvTicker,
            interval: tvInterval,
            timezone: "Asia/Jakarta",
            theme: "dark",
            style: "1", // Candlesticks
            locale: "id",
            toolbar_bg: "#131722",
            enable_publishing: false,
            allow_symbol_change: false,
            container_id: "tradingview_widget",
            studies: [
                "MASimple@tv-basicstudies",
                "RSI@tv-basicstudies"
            ],
            disabled_features: ["header_symbol_search"],
            enabled_features: ["side_toolbar_in_fullscreen_mode", "header_indicators", "header_chart_type"]
        });
    }

    document.getElementById("chartLabel").textContent = tvTicker;
    document.getElementById("timeframeLabel").textContent = TF_LABELS[currentTimeframe] || currentTimeframe;
}

// 2. Setup Event Listeners
function setupEventListeners() {
    // Pair selector
    const pairSelect = document.getElementById("pairSelect");
    pairSelect.addEventListener("change", (e) => {
        currentSymbol = e.target.value;
        document.getElementById("tickerSymbol").textContent = currentSymbol;
        initTradingViewChart();
        fetchMarketSnapshot();
        runParallelAnalysis();
    });

    // Timeframe buttons
    const tfButtons = document.querySelectorAll(".tf-btn");
    tfButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tfButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentTimeframe = btn.dataset.tf;
            initTradingViewChart();
            fetchMarketSnapshot();
            runParallelAnalysis();
        });
    });

    // Auto-AI Stream toggle (Continuous real-time AI)
    const autoAiToggle = document.getElementById("autoAiToggle");
    autoAiToggle.addEventListener("change", (e) => {
        autoAiStream = e.target.checked;
        const lbl = document.querySelector(".stream-active");
        if (lbl) {
            lbl.style.opacity = autoAiStream ? "1" : "0.5";
        }
        if (autoAiStream) {
            runParallelAnalysis();
            startPollingLoops();
        }
    });

    // Live Tick toggle
    const autoRefreshToggle = document.getElementById("autoRefreshToggle");
    autoRefreshToggle.addEventListener("change", (e) => {
        autoTickRefresh = e.target.checked;
    });

    // Manual Run Analysis button
    const btnRun = document.getElementById("btnRunAnalysis");
    btnRun.addEventListener("click", () => {
        runParallelAnalysis(true);
    });
}

function startPollingLoops() {
    // 1. Live Tick polling (Every 3.5 seconds)
    if (tickTimer) clearInterval(tickTimer);
    tickTimer = setInterval(() => {
        if (autoTickRefresh) {
            fetchMarketSnapshot();
        }
    }, 3500);

    // 2. Auto-AI Stream Analysis loop (Every 8 seconds continuously in real-time)
    if (aiStreamTimer) clearInterval(aiStreamTimer);
    aiStreamTimer = setInterval(() => {
        if (autoAiStream && !isAnalyzing) {
            runParallelAnalysis(false);
        }
    }, 8000);
}

// 3. Fetch Market Snapshot & Update Indicators Ribbon
async function fetchMarketSnapshot() {
    try {
        const res = await fetch(`/api/market-data?symbol=${currentSymbol}&timeframe=${currentTimeframe}`);
        const data = await res.json();
        if (data.success && data.data) {
            updateMarketUI(data.data);
        }
    } catch (err) {
        console.warn("Market fetch error:", err);
    }
}

function updateMarketUI(snap) {
    const digits = snap.digits || 2;
    const price = snap.price;
    const priceEl = document.getElementById("tickerPrice");
    const changeEl = document.getElementById("tickerChange");

    // Flash animation on tick change
    if (lastPrice > 0 && price !== lastPrice) {
        priceEl.style.color = price > lastPrice ? "var(--color-bullish)" : "var(--color-bearish)";
        setTimeout(() => { priceEl.style.color = "var(--text-bright)"; }, 500);
    }
    lastPrice = price;

    priceEl.textContent = Number(price).toFixed(digits);

    const change = Number(snap.change_pct || 0);
    changeEl.textContent = (change >= 0 ? "+" : "") + change.toFixed(2) + "%";
    changeEl.className = "ticker-change " + (change >= 0 ? "bullish" : "bearish");

    // Header stats
    document.getElementById("statHigh").textContent = Number(snap.high || 0).toFixed(digits);
    document.getElementById("statLow").textContent = Number(snap.low || 0).toFixed(digits);
    const atr = snap.indicators_current_tf ? snap.indicators_current_tf.atr : 0;
    document.getElementById("statAtr").textContent = Number(atr || 0).toFixed(digits);

    // Ribbon values
    const ind = snap.indicators_current_tf || {};
    const rsiVal = Number(ind.rsi || 50).toFixed(1);
    document.getElementById("ribbonRsi").textContent = rsiVal;
    
    const rsiFill = document.getElementById("rsiBarFill");
    rsiFill.style.width = Math.min(Math.max(rsiVal, 0), 100) + "%";
    if (rsiVal >= 70) {
        rsiFill.style.background = "var(--color-bearish)";
    } else if (rsiVal <= 30) {
        rsiFill.style.background = "var(--color-bullish)";
    } else {
        rsiFill.style.background = "var(--color-cyan)";
    }

    const macd = Number(ind.macd || 0).toFixed(digits);
    const macdSig = Number(ind.macd_signal || 0).toFixed(digits);
    document.getElementById("ribbonMacd").textContent = `${macd} / ${macdSig}`;
    document.getElementById("ribbonMacdState").textContent = Number(macd) >= Number(macdSig) ? "▲ Bullish Cross" : "▼ Bearish Cross";

    document.getElementById("valEma20").textContent = Number(ind.ema20 || 0).toFixed(digits);
    document.getElementById("valEma50").textContent = Number(ind.ema50 || 0).toFixed(digits);
    document.getElementById("valEma200").textContent = Number(ind.ema200 || 0).toFixed(digits);

    const piv = snap.pivots || {};
    document.getElementById("ribbonPivot").textContent = `Pivot: ${Number(piv.middle || 0).toFixed(digits)}`;
    document.getElementById("ribbonPivotRange").textContent = `S1: ${Number(piv.s1 || 0).toFixed(digits)} | R1: ${Number(piv.r1 || 0).toFixed(digits)}`;
}

// 4. Trigger Parallel Multi-Agent Analysis (Continuous or Manual)
async function runParallelAnalysis(isManual = false) {
    if (isAnalyzing) return;
    isAnalyzing = true;

    const btnRun = document.getElementById("btnRunAnalysis");
    if (isManual) {
        btnRun.classList.add("loading");
        btnRun.innerHTML = `<span>⏳ Menganalisis...</span>`;
    }

    try {
        const res = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: currentSymbol, timeframe: currentTimeframe })
        });

        const data = await res.json();
        if (data.success) {
            renderAnalysisResults(data);
        }
    } catch (err) {
        console.error("Analysis error:", err);
    } finally {
        isAnalyzing = false;
        if (isManual) {
            btnRun.classList.remove("loading");
            btnRun.innerHTML = `<span class="bolt-icon">⚡</span><span>Analisis Ulang</span>`;
        }
    }
}

// 5. Render Agent Results, On-Chart HUD & Master Trade Setup
function renderAnalysisResults(data) {
    const meta = data.meta;
    const agents = data.agents;
    const strat = agents.trade_strategist;
    const struct = agents.market_structure;
    const pa = agents.price_action;
    const smc = agents.smc_liquidity;
    const macro = agents.macro_session;
    const levels = strat.chart_levels || {};

    // Execution benchmark
    document.getElementById("benchTime").textContent = `${meta.parallel_execution_time_ms} ms (Total: ${meta.total_processing_time_ms} ms)`;

    // ================= A. ON-CHART AI SIGNAL & HUD =================
    const chartBadge = document.getElementById("chartSignalBadge");
    const chartAction = document.getElementById("chartSignalAction");
    const chartBias = document.getElementById("chartSignalBias");

    if (strat.action === "BUY") {
        chartAction.textContent = "▲ BUY SIGNAL ACTIVE";
        chartBias.textContent = strat.bias.replace(/_/g, " ");
        chartBadge.className = "chart-signal-badge bullish";
    } else if (strat.action === "SELL") {
        chartAction.textContent = "▼ SELL SIGNAL ACTIVE";
        chartBias.textContent = strat.bias.replace(/_/g, " ");
        chartBadge.className = "chart-signal-badge bearish";
    } else {
        chartAction.textContent = "■ WAIT / NO SETUP";
        chartBias.textContent = "EQUILIBRIUM";
        chartBadge.className = "chart-signal-badge neutral";
    }

    // Session Pill on Chart
    document.getElementById("chartSessionName").textContent = `${macro.session_name} (${macro.utc_time})`;

    // On-Chart Level Ribbon
    document.getElementById("hudEntry").textContent = `${levels.entry_low} - ${levels.entry_high}`;
    document.getElementById("hudSl").textContent = levels.stop_loss;
    document.getElementById("hudSlPips").textContent = `-${levels.sl_pips} pips`;
    document.getElementById("hudTp1").textContent = levels.take_profit_1;
    document.getElementById("hudTp1Pips").textContent = `+${levels.tp1_pips} pips`;
    document.getElementById("hudTp2").textContent = levels.take_profit_2;
    document.getElementById("hudTp2Pips").textContent = `+${levels.tp2_pips} pips`;
    document.getElementById("hudRr").textContent = levels.rr_ratio;

    // ================= B. MASTER TRADE CARD =================
    const actionBadge = document.getElementById("actionBadge");
    const actionMain = actionBadge.querySelector(".action-main");
    const biasBadge = document.getElementById("biasBadge");

    actionMain.textContent = strat.action;
    biasBadge.textContent = strat.bias.replace(/_/g, " ");

    actionBadge.className = "action-callout " + (
        strat.action === "BUY" ? "bullish" : (strat.action === "SELL" ? "bearish" : "neutral")
    );

    document.getElementById("confValue").textContent = `${strat.confidence}%`;
    document.getElementById("confFill").style.width = `${strat.confidence}%`;

    document.getElementById("tradeEntry").textContent = strat.entry_range;
    document.getElementById("tradeSl").textContent = strat.stop_loss;
    document.getElementById("tradeSlPips").textContent = `-${strat.sl_pips} pips`;
    document.getElementById("tradeTp1").textContent = strat.take_profit_1;
    document.getElementById("tradeTp1Pips").textContent = `+${strat.tp1_pips} pips`;
    document.getElementById("tradeTp2").textContent = strat.take_profit_2;
    document.getElementById("tradeTp2Pips").textContent = `+${strat.tp2_pips} pips`;
    document.getElementById("tradeRr").textContent = strat.risk_reward;
    document.getElementById("tradeNarrative").textContent = strat.narrative;

    // Trade Management Rules
    document.getElementById("ruleBreakeven").textContent = strat.breakeven_trigger;
    document.getElementById("rulePartial").textContent = strat.partial_tp_rule;

    // ================= C. PARALLEL AGENT CARDS =================
    // Agent 1: Market Structure & Fractal Trend
    document.getElementById("ag1Trend").textContent = struct.trend.replace(/_/g, " ");
    document.getElementById("ag1Wyckoff").textContent = struct.wyckoff_phase;
    document.getElementById("textAgent1").textContent = struct.narrative;
    const tag1 = document.getElementById("tagAgent1");
    tag1.textContent = struct.htf_alignment;
    tag1.className = "agent-tag " + (struct.trend.includes("BULLISH") ? "bullish" : (struct.trend.includes("BEARISH") ? "bearish" : "neutral"));

    // Agent 2: Price Action & Momentum Pro
    document.getElementById("ag2Pattern").textContent = pa.pattern;
    document.getElementById("ag2Div").textContent = `${pa.momentum_rating} (${pa.divergence})`;
    document.getElementById("textAgent2").textContent = pa.narrative;
    const tag2 = document.getElementById("tagAgent2");
    tag2.textContent = pa.momentum_rating;
    tag2.className = "agent-tag " + (pa.momentum_rating === "BULLISH" ? "bullish" : (pa.momentum_rating === "BEARISH" ? "bearish" : "neutral"));

    // Agent 3: ICT / SMC & Liquidity Hunt
    document.getElementById("ag3Zone").textContent = `${smc.range_percentage}% (${smc.pricing_bias.replace(/_/g, " ")})`;
    document.getElementById("ag3Target").textContent = `BSL: ${smc.bsl_target} | SSL: ${smc.ssl_target}`;
    document.getElementById("textAgent3").textContent = smc.narrative;
    const tag3 = document.getElementById("tagAgent3");
    tag3.textContent = smc.pricing_bias.replace(/_/g, " ");
    tag3.className = "agent-tag " + (smc.pricing_bias.includes("BULLISH") ? "bullish" : (smc.pricing_bias.includes("BEARISH") ? "bearish" : "neutral"));

    // Agent 4: Macro & Session Analyst (NEW)
    document.getElementById("ag4Session").textContent = macro.session_name;
    document.getElementById("ag4MacroBias").textContent = macro.macro_flow;
    document.getElementById("textAgent4").textContent = macro.narrative;
    const tag4 = document.getElementById("tagAgent4");
    tag4.textContent = macro.killzone_active ? "KILLZONE AKTIF" : "OFF-PEAK";
    tag4.className = "agent-tag " + (macro.killzone_active ? "bullish" : "neutral");

    // Checklist update
    const checklistUl = document.getElementById("checklistItems");
    if (strat.checklist && strat.checklist.length > 0) {
        checklistUl.innerHTML = strat.checklist.map(item => `<li>${item}</li>`).join("");
    }
}
