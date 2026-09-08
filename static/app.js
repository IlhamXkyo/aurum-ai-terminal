// Global State
let currentSymbol = "XAUUSD";
let currentTimeframe = "15";
let autoTickRefresh = true;
let autoAiStream = true;
let audioAlertsEnabled = true;
let tvWidget = null;
let lastPrice = 0;
let tickTimer = null;
let aiStreamTimer = null;
let radarTimer = null;
let isAnalyzing = false;
let knownSetups = new Set(); // To avoid repeating notifications for the same setup

// Ticker Mapping for TradingView Widget
const TV_TICKER_MAP = {
    "XAUUSD": "OANDA:XAUUSD",
    "EURUSD": "FX:EURUSD",
    "GBPUSD": "FX:GBPUSD",
    "USDJPY": "FX:USDJPY",
    "BTCUSD": "BITSTAMP:BTCUSD"
};

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

// ================= 1. WEB AUDIO API CHIME SYNTHESIZER =================
let audioCtx = null;

function getAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioCtx = new AudioContextClass();
        }
    }
    if (audioCtx && audioCtx.state === "suspended") {
        audioCtx.resume();
    }
    return audioCtx;
}

function playTradingAlertSound(type = "BUY") {
    if (!audioAlertsEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;

        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gainNode = ctx.createGain();

        osc1.connect(gainNode);
        osc2.connect(gainNode);
        gainNode.connect(ctx.destination);

        const now = ctx.currentTime;

        if (type === "BUY") {
            // Ascending high-frequency harmonic chime (880Hz -> 1320Hz)
            osc1.frequency.setValueAtTime(880, now);
            osc1.frequency.exponentialRampToValueAtTime(1320, now + 0.15);
            osc2.frequency.setValueAtTime(1100, now);
            osc2.frequency.exponentialRampToValueAtTime(1760, now + 0.2);
        } else {
            // Descending firm chime (880Hz -> 587Hz)
            osc1.frequency.setValueAtTime(880, now);
            osc1.frequency.exponentialRampToValueAtTime(587, now + 0.15);
            osc2.frequency.setValueAtTime(659, now);
            osc2.frequency.exponentialRampToValueAtTime(440, now + 0.2);
        }

        gainNode.gain.setValueAtTime(0.3, now);
        gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.6);
        osc2.stop(now + 0.6);
    } catch (e) {
        console.warn("Audio playback failed:", e);
    }
}

// ================= 2. DESKTOP & TOAST NOTIFICATION ENGINE =================
function requestDesktopNotificationPermission() {
    if ("Notification" in window) {
        Notification.requestPermission().then(permission => {
            const btn = document.getElementById("btnRequestNotif");
            if (permission === "granted") {
                if (btn) btn.classList.add("active");
                showToast("NOTIFIKASI AKTIF", "Izin notifikasi desktop berhasil diaktifkan!", "neutral");
                playTradingAlertSound("BUY");
            } else {
                alert("Izin notifikasi belum diberikan di browser.");
            }
        });
    } else {
        alert("Browser ini tidak mendukung notifikasi desktop.");
    }
}

function triggerSetupNotification(tf, action, entry, sl, tp1, pips) {
    // 1. Play institutional sound chime
    playTradingAlertSound(action);

    // 2. Browser Desktop Push Notification (Works even when minimized)
    if ("Notification" in window && Notification.permission === "granted") {
        const title = `🚨 SETUP BARU: ${currentSymbol} (${tf.toUpperCase()}) - ${action}`;
        const body = `Entry: ${entry} | SL: ${sl} | TP: ${tp1} (+${pips} pips)`;
        try {
            new Notification(title, { body, icon: "/static/style.css" });
        } catch (e) {
            console.warn("Desktop notif error:", e);
        }
    }

    // 3. On-Screen Animated Toast
    showToast(
        `🚨 SETUP ${action}: ${currentSymbol} (${tf.toUpperCase()})`,
        `Entry: ${entry} | SL: ${sl} | TP1: ${tp1} (+${pips} pips)`,
        action.toLowerCase(),
        tf
    );
}

function showToast(title, message, type = "bullish", tf = null) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-card ${type}`;
    toast.innerHTML = `
        <div class="toast-top">
            <span class="toast-title">${title}</span>
            <span class="toast-time">Baru Saja</span>
        </div>
        <div class="toast-body">${message}</div>
        ${tf ? `<button class="toast-action-btn" onclick="switchTimeframe('${tf}')">⚡ Buka Chart ${tf}</button>` : ""}
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, 6000);
}

window.switchTimeframe = function(tf) {
    const cleanTf = tf.replace("m", "").replace("H", tf === "1H" ? "60" : "240").replace("D", "1D");
    const btn = document.querySelector(`.tf-btn[data-tf="${cleanTf}"]`);
    if (btn) btn.click();
};

// ================= 3. INITIALIZATION & LISTENERS =================
document.addEventListener("DOMContentLoaded", () => {
    initTradingViewChart();
    setupEventListeners();
    fetchMarketSnapshot();
    runParallelAnalysis();
    scanMultiTimeframeRadar();

    // Start background loops
    startPollingLoops();
});

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
            style: "1",
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

function setupEventListeners() {
    // Pair selector
    const pairSelect = document.getElementById("pairSelect");
    pairSelect.addEventListener("change", (e) => {
        currentSymbol = e.target.value;
        document.getElementById("tickerSymbol").textContent = currentSymbol;
        initTradingViewChart();
        fetchMarketSnapshot();
        runParallelAnalysis();
        scanMultiTimeframeRadar();
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
            updateRadarActiveCard(currentTimeframe);
        });
    });

    // Audio Alert Toggle Button
    const btnAudio = document.getElementById("btnAudioToggle");
    btnAudio.addEventListener("click", () => {
        getAudioContext(); // Resume on user gesture
        audioAlertsEnabled = !audioAlertsEnabled;
        btnAudio.classList.toggle("active", audioAlertsEnabled);
        document.getElementById("audioIcon").textContent = audioAlertsEnabled ? "🔔" : "🔕";
        if (audioAlertsEnabled) {
            playTradingAlertSound("BUY");
        }
    });

    // Desktop Notification Request Button
    const btnNotif = document.getElementById("btnRequestNotif");
    btnNotif.addEventListener("click", () => {
        requestDesktopNotificationPermission();
    });

    // Auto-AI Stream toggle
    const autoAiToggle = document.getElementById("autoAiToggle");
    autoAiToggle.addEventListener("change", (e) => {
        autoAiStream = e.target.checked;
        const lbl = document.querySelector(".stream-active");
        if (lbl) lbl.style.opacity = autoAiStream ? "1" : "0.5";
        if (autoAiStream) {
            runParallelAnalysis();
            scanMultiTimeframeRadar();
        }
    });

    // Manual Run Analysis button
    const btnRun = document.getElementById("btnRunAnalysis");
    btnRun.addEventListener("click", () => {
        getAudioContext();
        runParallelAnalysis(true);
        scanMultiTimeframeRadar();
    });

    // Radar cards click delegation
    const radarCards = document.querySelectorAll(".radar-card");
    radarCards.forEach(rc => {
        rc.addEventListener("click", () => {
            const tf = rc.dataset.tf;
            switchTimeframe(tf);
        });
    });

    // Tab buttons in Right Panel
    const tabAnalysis = document.getElementById("tabBtnAnalysis");
    const tabJournal = document.getElementById("tabBtnJournal");
    const viewAnalysis = document.getElementById("viewAnalysis");
    const viewJournal = document.getElementById("viewJournal");

    tabAnalysis.addEventListener("click", () => {
        tabAnalysis.classList.add("active");
        tabJournal.classList.remove("active");
        viewAnalysis.classList.add("active");
        viewJournal.classList.remove("active");
    });

    tabJournal.addEventListener("click", () => {
        tabJournal.classList.add("active");
        tabAnalysis.classList.remove("active");
        viewJournal.classList.add("active");
        viewAnalysis.classList.remove("active");
        fetchJournalData();
    });
}

function updateRadarActiveCard(activeTf) {
    document.querySelectorAll(".radar-card").forEach(rc => {
        rc.classList.toggle("active", rc.dataset.tf === activeTf);
    });
}

function startPollingLoops() {
    // 1. Live Tick polling (Every 3.5s)
    if (tickTimer) clearInterval(tickTimer);
    tickTimer = setInterval(() => {
        if (autoTickRefresh) {
            fetchMarketSnapshot();
        }
    }, 3500);

    // 2. Auto-AI Single TF Analysis (Every 8s)
    if (aiStreamTimer) clearInterval(aiStreamTimer);
    aiStreamTimer = setInterval(() => {
        if (autoAiStream && !isAnalyzing) {
            runParallelAnalysis(false);
        }
    }, 8000);

    // 3. Multi-Timeframe Radar Scan (Every 12s across all timeframes)
    if (radarTimer) clearInterval(radarTimer);
    radarTimer = setInterval(() => {
        if (autoAiStream) {
            scanMultiTimeframeRadar();
        }
    }, 12000);
}

// ================= 4. FETCH MARKET SNAPSHOT & INDICATORS =================
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

    if (lastPrice > 0 && price !== lastPrice) {
        priceEl.style.color = price > lastPrice ? "var(--color-bullish)" : "var(--color-bearish)";
        setTimeout(() => { priceEl.style.color = "var(--text-bright)"; }, 500);
    }
    lastPrice = price;

    priceEl.textContent = Number(price).toFixed(digits);

    const change = Number(snap.change_pct || 0);
    changeEl.textContent = (change >= 0 ? "+" : "") + change.toFixed(2) + "%";
    changeEl.className = "ticker-change " + (change >= 0 ? "bullish" : "bearish");

    document.getElementById("statHigh").textContent = Number(snap.high || 0).toFixed(digits);
    document.getElementById("statLow").textContent = Number(snap.low || 0).toFixed(digits);
    const atr = snap.indicators_current_tf ? snap.indicators_current_tf.atr : 0;
    document.getElementById("statAtr").textContent = Number(atr || 0).toFixed(digits);

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

// ================= 5. SINGLE-TIMEFRAME ANALYSIS & POSITION BOX =================
async function runParallelAnalysis(isManual = false) {
    if (isAnalyzing) return;
    isAnalyzing = true;

    const btnRun = document.getElementById("btnRunAnalysis");
    if (isManual) {
        btnRun.classList.add("loading");
        btnRun.innerHTML = `<span>⏳ Memindai...</span>`;
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
            btnRun.innerHTML = `<span class="bolt-icon">⚡</span><span>Scan Ulang</span>`;
        }
    }
}

function renderAnalysisResults(data) {
    const agents = data.agents;
    const strat = agents.trade_strategist;
    const struct = agents.market_structure;
    const pa = agents.price_action;
    const smc = agents.smc_liquidity;
    const macro = agents.macro_session;
    const levels = strat.chart_levels || {};

    // 1. Clean Chart Sub-Header Status
    const chartBadge = document.getElementById("chartSignalBadge");
    const chartAction = document.getElementById("chartSignalAction");
    chartAction.textContent = strat.action === "BUY" ? "▲ BUY SIGNAL ACTIVE" : (strat.action === "SELL" ? "▼ SELL SIGNAL ACTIVE" : "■ WAIT / EQUILIBRIUM");
    chartBadge.className = "signal-pill " + (strat.action === "BUY" ? "bullish" : (strat.action === "SELL" ? "bearish" : "neutral"));

    document.getElementById("chartSessionName").textContent = `${macro.session_name} (${macro.utc_time})`;

    // 2. Authentic TradingView Position Box Visualizer
    renderTvPositionBox(strat);

    // 3. Master Trade Card
    const actionBadge = document.getElementById("actionBadge");
    const actionMain = actionBadge.querySelector(".action-main");
    const biasBadge = document.getElementById("biasBadge");

    actionMain.textContent = strat.action;
    biasBadge.textContent = strat.bias.replace(/_/g, " ");
    actionBadge.className = "action-callout " + (strat.action === "BUY" ? "bullish" : (strat.action === "SELL" ? "bearish" : "neutral"));

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

    document.getElementById("ruleBreakeven").textContent = strat.breakeven_trigger;
    document.getElementById("rulePartial").textContent = strat.partial_tp_rule;

    // 4. Agent Cards
    document.getElementById("ag1Trend").textContent = struct.trend.replace(/_/g, " ");
    document.getElementById("ag1Wyckoff").textContent = struct.wyckoff_phase;
    document.getElementById("textAgent1").textContent = struct.narrative;
    const tag1 = document.getElementById("tagAgent1");
    tag1.textContent = struct.htf_alignment;
    tag1.className = "agent-tag " + (struct.trend.includes("BULLISH") ? "bullish" : (struct.trend.includes("BEARISH") ? "bearish" : "neutral"));

    document.getElementById("ag2Pattern").textContent = pa.pattern;
    document.getElementById("ag2Div").textContent = `${pa.momentum_rating} (${pa.divergence})`;
    document.getElementById("textAgent2").textContent = pa.narrative;
    const tag2 = document.getElementById("tagAgent2");
    tag2.textContent = pa.momentum_rating;
    tag2.className = "agent-tag " + (pa.momentum_rating === "BULLISH" ? "bullish" : (pa.momentum_rating === "BEARISH" ? "bearish" : "neutral"));

    document.getElementById("ag3Zone").textContent = `${smc.range_percentage}% (${smc.pricing_bias.replace(/_/g, " ")})`;
    document.getElementById("ag3Target").textContent = `BSL: ${smc.bsl_target} | SSL: ${smc.ssl_target}`;
    document.getElementById("textAgent3").textContent = smc.narrative;
    const tag3 = document.getElementById("tagAgent3");
    tag3.textContent = smc.pricing_bias.replace(/_/g, " ");
    tag3.className = "agent-tag " + (smc.pricing_bias.includes("BULLISH") ? "bullish" : (smc.pricing_bias.includes("BEARISH") ? "bearish" : "neutral"));

    document.getElementById("ag4Session").textContent = macro.session_name;
    document.getElementById("ag4MacroBias").textContent = macro.macro_flow;
    document.getElementById("textAgent4").textContent = macro.narrative;
    const tag4 = document.getElementById("tagAgent4");
    tag4.textContent = macro.killzone_active ? "KILLZONE AKTIF" : "OFF-PEAK";
    tag4.className = "agent-tag " + (macro.killzone_active ? "bullish" : "neutral");
}

function renderTvPositionBox(strat) {
    const isLong = strat.action === "BUY";
    const modeBadge = document.getElementById("toolModeBadge");
    const targetZone = document.getElementById("posTargetZone");
    const stopZone = document.getElementById("posStopZone");
    const posBox = document.getElementById("tvPositionBox");

    if (strat.action === "BUY") {
        modeBadge.textContent = "🟢 LONG POSITION TOOL";
        posBox.style.flexDirection = "column"; // Target on top, Stop at bottom
    } else if (strat.action === "SELL") {
        modeBadge.textContent = "🔴 SHORT POSITION TOOL";
        posBox.style.flexDirection = "column-reverse"; // Target at bottom, Stop on top
    } else {
        modeBadge.textContent = "🟡 EQUILIBRIUM BRACKET";
        posBox.style.flexDirection = "column";
    }

    document.getElementById("tvTpPrice").textContent = strat.take_profit_1;
    document.getElementById("tvTpPips").textContent = `+${strat.tp1_pips} pips`;
    document.getElementById("tvEntryPrice").textContent = strat.entry_range;
    document.getElementById("tvSlPrice").textContent = strat.stop_loss;
    document.getElementById("tvSlPips").textContent = `-${strat.sl_pips} pips`;
    document.getElementById("tvRrBadge").textContent = `R:R ${strat.risk_reward}`;

    document.getElementById("psAction").textContent = strat.action;
    document.getElementById("psConf").textContent = `${strat.confidence}%`;
    document.getElementById("psTp2").textContent = strat.take_profit_2;
}

// ================= 6. MULTI-TIMEFRAME RADAR SCANNER =================
async function scanMultiTimeframeRadar() {
    try {
        const res = await fetch(`/api/scan-radar?symbol=${currentSymbol}`);
        const data = await res.json();
        if (data.success && data.radar) {
            updateRadarUI(data.radar);
            if (data.journal) {
                renderJournalTable(data.journal);
            }
        }
    } catch (err) {
        console.warn("Radar scan error:", err);
    }
}

function updateRadarUI(radar) {
    for (const [tf, item] of Object.entries(radar)) {
        const card = document.querySelector(`.radar-card[data-tf="${tf}"]`);
        if (!card) continue;

        const badge = card.querySelector(".rc-badge");
        const val = card.querySelector(".rc-val");

        badge.textContent = item.action;
        badge.className = "rc-badge " + (item.action === "BUY" ? "bullish" : (item.action === "SELL" ? "bearish" : "neutral"));

        if (item.action !== "WAIT") {
            val.textContent = `${item.action} @ ${item.entry}`;
            
            // Check if this setup is new to trigger alerts
            const setupKey = `${currentSymbol}-${tf}-${item.action}-${item.entry}`;
            if (!knownSetups.has(setupKey)) {
                knownSetups.add(setupKey);
                triggerSetupNotification(
                    tf === "60" ? "1H" : (tf === "240" ? "4H" : `${tf}m`),
                    item.action,
                    item.entry,
                    item.stop_loss,
                    item.take_profit_1,
                    item.tp1_pips
                );
            }
        } else {
            val.textContent = `Wait (${item.bias.split('_')[0]})`;
        }
    }
}

// ================= 7. SETUP JOURNAL (PAST & ACTIVE) =================
async function fetchJournalData() {
    try {
        const res = await fetch(`/api/setup-journal?symbol=${currentSymbol}`);
        const data = await res.json();
        if (data.success && data.journal) {
            renderJournalTable(data.journal);
        }
    } catch (err) {
        console.warn("Journal fetch error:", err);
    }
}

function renderJournalTable(journal) {
    const tbody = document.getElementById("journalTableBody");
    if (!tbody) return;

    if (!journal || journal.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="loading-td">Belum ada setup tersimpan.</td></tr>`;
        return;
    }

    tbody.innerHTML = journal.map(row => `
        <tr>
            <td>${row.time_str}</td>
            <td><b>${row.timeframe}</b></td>
            <td><span class="journal-badge ${row.action.toLowerCase()}">${row.action}</span></td>
            <td>${row.entry}</td>
            <td>${row.stop_loss}</td>
            <td>${row.take_profit_1}</td>
            <td><span class="${row.status.includes('HIT') ? 'status-hit' : 'status-active'}">${row.status}</span></td>
        </tr>
    `).join("");
}
