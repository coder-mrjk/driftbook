# Final Production Handover — DriftBook

**Title:** DriftBook: Production Handover & Operations Runbook  
**Version:** 1.0.0  
**Date:** 2026-10-18  
**Owner:** DriftBook Engineering Team  
**Status:** Approved & Production Verified  
**Verified against commit:** Working Tree Clean  

---

## 1. System Overview
DriftBook is a quantitative order-book forecasting and drift-detection framework designed for high-frequency trading (HFT) and market making. It forecasts short-term price direction (5-second horizon) from Level-2 order book depth, monitors rolling multi-feature Kolmogorov-Smirnov statistics to detect market regime shifts, and deploys adaptive conformal prediction sets to abstain from trading during periods of high uncertainty or adverse selection.

---

## 2. Architecture & File Inventory

| File | Purpose | Key Interface |
|---|---|---|
| [`simulate.py`](file:///Users/karthi/driftbook/simulate.py) | Synthetic order-book generator with planted regime shifts ($\beta$ flips sign, spread widens, volatility increases). | `simulate(T=18000, shifts=(6000, 11000), seed=7)` |
| [`pipeline.py`](file:///Users/karthi/driftbook/pipeline.py) | Feature engineering, walk-forward evaluation of Static, Periodic, and DriftBook models, adaptive conformal abstention, and metrics reporting. | `features(d)`, `run(mode, X, y, shifts)` |
| [`recorder.py`](file:///Users/karthi/driftbook/recorder.py) | Live Kraken v2 WebSocket L2 book recorder for BTC/USD at 1 Hz with depth truncation, cross-purging, and 10-minute Snappy Parquet flushes. | `OrderBook`, `OrderBookRecorder`, `main()` |
| [`count_rows.py`](file:///Users/karthi/driftbook/count_rows.py) | Diagnostic utility reading Parquet metadata headers to inspect row counts, disk size, and UTC time spans. | `count_collected_rows(directory="data")` |
| [`dashboard_template.html`](file:///Users/karthi/driftbook/dashboard_template.html) | High-performance HTML5 Canvas replay dashboard (100% offline, zero external CDN dependencies). | `plot()`, `upd()` |
| [`dashboard.html`](file:///Users/karthi/driftbook/dashboard.html) | Standalone dashboard populated with benchmark dataset and model predictions. | Open in browser (`open dashboard.html`) |
| [`docs/explanation.md`](file:///Users/karthi/driftbook/docs/explanation.md) | Comprehensive presentation guide for judges (IIT Bombay & Optiver): 60s pitch, function breakdown, design rationales, and Q&A grill defense. | Technical Documentation |
| [`docs/STATE.md`](file:///Users/karthi/driftbook/docs/STATE.md) | Milestone tracking log and benchmark performance records. | Project State Tracking |

---

## 3. Quickstart & Operational Commands

### 3.1 Environment Activation
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.2 Running the Pipeline (Synthetic Benchmark)
```bash
python pipeline.py
```
Output:
- Generates `results.json` containing accuracy, F1, MCC, recovery delay, detection timestamps, and conformal metrics.
- Updates `dashboard.html` for instant visual replay.

### 3.3 Opening the Replay Dashboard
```bash
open dashboard.html
```
Features:
- **Play/Pause Replay:** 70ms tick automatic playback.
- **Interactive Scrubber:** Scrub directly to Regime 1 (step 6000) or Regime 2 (step 11000) to observe real-time drift detection and conformal abstention.
- **Status Band:** Visual color alerts (Green = Market stable, Yellow = Market changed: adapting).
- **Abstain Meter:** Dynamic confidence bar displaying answer rate vs. abstention rate.

### 3.4 Live Exchange Order Book Recording
```bash
# Record live BTC/USD from Kraken v2 WebSocket (1 row/sec, saves to data/ every 10 min)
python recorder.py

# Optional: Run quick dry-run test collecting 10 rows
python recorder.py --max-rows 10
```

### 3.5 Checking Recorded Row Counts
```bash
python count_rows.py
```

### 3.6 Executing Unit Tests
```bash
pytest -v
```

---

## 4. Key Quantitative Results

| Metric | Static Model | Periodic Retrain | DriftBook (Ours) |
|---|---|---|---|
| **Overall Accuracy** | 39.6% | 43.2% | **45.8%** |
| **Selective Accuracy** (when trading) | 39.6% | 43.2% | **55.8% (+16.2% edge)** |
| **Macro F1 Score** | 0.396 | 0.435 | **0.458** |
| **Matthews Correlation (MCC)** | 0.095 | 0.148 | **0.188 (+98% vs static)** |
| **Abstain Rate** | 0.0% | 0.0% | **77.3%** |
| **Conformal Coverage** | N/A | N/A | **80.1% (target: 80.0%)** |
| **Inference Latency** | 0.008 ms | 0.008 ms | **0.010 ms (~10 $\mu$s)** |
| **Shock Recovery Speed** | 5,499 steps | 3,399 steps | **1,299 steps (76% faster)** |

---

## 5. Security & Safety Checklist
- [x] Zero Secrets: No hardcoded credentials or API keys (Kraken v2 public order-book endpoint requires no authentication).
- [x] Clean Git State: Master branch clean with descriptive Conventional Commits.
- [x] No Look-ahead Bias: Prediction horizon strictly masked ($hi - H$), ensuring models never train on unmaterialized future returns.
- [x] Zero External CDN Dependencies: `dashboard.html` executes completely offline without external network calls.
