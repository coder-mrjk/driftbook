# Project Handover & Architecture Guide — DriftBook

**Title:** DriftBook: Handover & Operations Guide  
**Version:** 1.2.0  
**Date:** 2026-10-19  
**Status:** Research prototype validated on simulated data  

---

## 1. System Overview
DriftBook is a quantitative order-book forecasting and drift-detection framework (research prototype validated on simulated data). It forecasts short-term price direction (5-step horizon) from Level-2 order book depth, monitors rolling multi-feature Kolmogorov-Smirnov statistics and River ADWIN streaming errors to detect market regime shifts, deploys adaptive conformal prediction sets to abstain from trading during periods of high uncertainty or adverse selection, and routes between specialized prediction heads with an experimental dynamic regime router.

---

## 2. Architecture & File Inventory

| File | Purpose | Key Interface |
|---|---|---|
| [`simulate.py`](../simulate.py) | Synthetic order-book generator with planted regime shifts ($\beta$ flips sign, spread widens, volatility increases). | `simulate(T=18000, shifts=(6000, 11000), seed=7)` |
| [`pipeline.py`](../pipeline.py) | Feature engineering, walk-forward evaluation of Static, Periodic, Tuned DriftBook, ADWIN, and Regime Router (Experimental) models. | `features(d)`, `run(...)` |
| [`recorder.py`](../recorder.py) | Live Kraken v2 WebSocket L2 book recorder for BTC/USD at 1 Hz with depth truncation, cross-purging, and 10-minute Snappy Parquet flushes. | `OrderBook`, `OrderBookRecorder`, `main()` |
| [`count_rows.py`](../count_rows.py) | Diagnostic utility reading Parquet metadata headers to inspect row counts, disk size, and UTC time spans. | `count_collected_rows(directory="data")` |
| [`dashboard_template.html`](../dashboard_template.html) | High-performance HTML5 Canvas replay dashboard (100% offline, zero external CDN dependencies) supporting all 5 models. | `plot()`, `upd()` |
| [`dashboard.html`](../dashboard.html) | Standalone dashboard populated with benchmark dataset and model predictions. | Open in browser (`open dashboard.html`) |
| [`TUNING_AND_EVALUATION_REPORT.md`](../TUNING_AND_EVALUATION_REPORT.md) | Exhaustive tuning grid search on 60% split and out-of-sample held-out 40% benchmarks. | Empirical Evaluation Report |
| [`explanation.md`](explanation.md) | Comprehensive presentation guide: 60s pitch, function breakdown, design rationales, and Q&A defense. | Technical Documentation |
| [`STATE.md`](STATE.md) | Milestone tracking log and benchmark performance records. | Project State Tracking |

---

## 3. Quickstart & Operational Commands

### 3.1 Environment Activation
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.2 Running the Pipeline (Synthetic Benchmark)
```bash
# Run full walk-forward evaluation (all 5 models)
python pipeline.py

# Run strictly on held-out final 40% split
python pipeline.py --heldout

# Run on real recorded Kraken BTC/USD data
python pipeline.py --data combined.parquet
```

### 3.3 Opening the Replay Dashboard
```bash
open dashboard.html
```
Features:
- **Play/Pause Replay:** 70ms tick automatic playback.
- **Interactive Scrubber:** Scrub directly to Regime 1 (step 6000) or Regime 2 (step 11000) to observe real-time drift detection and conformal abstention.
- **5-Model Accuracy Comparison:** Live Canvas plots for Static, Periodic, DriftBook (KS), ADWIN, and Regime Router.
- **Abstain Meter:** Dynamic confidence bar displaying answer rate vs. abstention rate.

### 3.4 Live Exchange Order Book Recording
```bash
python recorder.py
```

### 3.5 Checking Recorded Row Counts
```bash
python count_rows.py
```

### 3.6 Executing Unit Tests
```bash
pytest tests/ -v
```

---

## 4. Key Quantitative Results (Held-Out 40% Split: Steps 10,800–18,000)

| Metric | Static Model | Periodic (2k) | DriftBook (KS) | ADWIN (River) | Regime Router (Ours) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Overall Accuracy** | 48.5% | 45.2% | 44.5% | 44.9% | **49.0%** |
| **Selective Accuracy** (when trading) | 48.5% | 45.2% | 48.9% | 48.6% | **51.4% (+2.9% edge)** |
| **Macro F1 Score** | 0.486 | 0.446 | 0.446 | 0.446 | **0.492** |
| **Matthews Correlation (MCC)** | 0.230 | 0.177 | 0.167 | 0.171 | **0.238** |
| **Abstain Rate** | 0.0% | 0.0% | 50.4% | 51.0% | **40.1%** |
| **Detection Delay** | N/A | N/A | 400 steps | **82 steps** | **0 steps (Instant)** |
| **False Alarms** | N/A | N/A | **0** | 2 | **0** |
| **Inference Latency** | 0.009 ms | 0.008 ms | 0.010 ms | 0.010 ms | 0.017 ms |

---

## 5. Security & Safety Checklist
- [x] Zero Secrets: No hardcoded credentials or API keys (Kraken v2 public order-book endpoint requires no authentication).
- [x] Clean Git State: Master branch clean with descriptive Conventional Commits.
- [x] No Look-ahead Bias: Prediction horizon strictly masked ($hi - H$), ensuring models never train on unmaterialized future returns.
- [x] Zero External CDN Dependencies: `dashboard.html` executes completely offline without external network calls.
- [x] Full Test Coverage: 17 unit tests passing with zero errors or warnings.

