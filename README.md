# Aurum AI Trading Terminal

Aplikasi terminal trading untuk analisis teknikal pasar Forex dan Emas (XAUUSD) berbasis Flask dan widget grafik TradingView.

Aplikasi ini menjalankan pipeline analisis teknikal terstruktur yang mengkombinasikan evaluasi tren jangka panjang, pola price action, dan pemetaan likuiditas Smart Money Concepts (SMC) untuk menghasilkan rencana trading ringkas.

## Fitur

- **Grafik Interaktif TradingView**: Streaming data tick real-time dengan pemilihan timeframe fleksibel (1m, 5m, 15m, 1H, 4H, 1D).
- **Pipeline Analisis Bertingkat**:
  - *Market Structure*: Evaluasi tren kerangka waktu tinggi (HTF), Break of Structure (BOS), dan pivot point.
  - *Price Action & Momentum*: Pembacaan pola candlestick, level RSI (14), dan konvergensi histogram MACD.
  - *Liquidity Mapping*: Penandaan area order block, discount vs premium zone, serta buy-side/sell-side liquidity.
  - *Trade Synthesis*: Rangkuman sinyal entry, batas risiko stop loss, target take profit, dan rasio risk-to-reward.
- **Pita Metrik Pasar**: Pemantauan langsung status persilangan EMA 20/50/200 dan rentang volatilitas harian.
- **Dukungan Pasangan Mata Uang**: XAUUSD, EURUSD, GBPUSD, USDJPY, dan BTCUSD.

## Instalasi

### Prasyarat

- Python 3.10 atau lebih baru
- pip

### Langkah Menjalankan

1. Clone repositori:
   ```bash
   git clone https://github.com/IlhamXkyo/aurum-ai-terminal.git
   cd aurum-ai-terminal
   ```

2. Buat virtual environment:
   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   # Di Linux/macOS:
   source venv/bin/activate
   ```

3. Pasang paket yang diperlukan:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan aplikasi:
   ```bash
   python app.py
   ```
   Buka `http://localhost:5000` di peramban.

## Catatan dan Batasan

Aplikasi ini ditujukan semata-mata untuk riset dan edukasi analisis teknikal mandiri, bukan rekomendasi finansial atau jaminan keuntungan. Selalu terapkan manajemen risiko disiplin pada setiap aktivitas trading.

## Lisensi

MIT License.
