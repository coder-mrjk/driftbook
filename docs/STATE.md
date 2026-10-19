# DriftBook Project State & Milestone Log

**Document Version:** 1.2.0  
**Date:** 2026-10-19  
**Status:** Research prototype validated on simulated data  
**Current Phase:** Milestone 3 Complete (Hyperparameter Tuning on 60% Split, River ADWIN Streaming Detector, Regime Router (Experimental), Held-Out 40% Evaluation, 17 Unit Tests, Tuning & Evaluation Report)

---

## 1. Executive Summary
DriftBook is a quantitative market microstructure forecasting framework built for the IIT Bombay & Optiver AI Innovation Lab Perceptron Hackathon (Theme 3: Markets & Trading Intelligence, Problem 4: Order Book Forecasting Under Regime Shifts). It detects statistical regime shifts in high-frequency limit order books and uses adaptive conformal prediction to abstain from trading during periods of high uncertainty.

---

## 2. Implemented Components

| Component | File Path | Status | Verification Evidence |
|---|---|---|---|
| Synthetic LOB Simulator | `simulate.py` | Complete & Tested | Planted regime shifts at steps 6000 and 11000; verified with `tests/test_simulate.py`. |
| Core Forecasting Pipeline | `pipeline.py` | Complete & Tested | Walk-forward evaluation of Static, Periodic, Tuned DriftBook, ADWIN, and Regime Router models. Supports `--heldout` mode. Tested via `tests/test_pipeline.py`. |
| Live Exchange Recorder | `recorder.py` | Complete & Tested | Evaluated Kraken, Coinbase, and OKX from India; selected Kraken v2 WS for BTC/USD depth 25. Hardened with depth truncation, aggressive cross-purge, and self-healing resync. Tested via `tests/test_recorder.py`. |
| Row Inspection Utility | `count_rows.py` | Complete & Tested | Fast header-based row counting across Parquet files with safe metadata and timestamp extraction. Tested via `tests/test_count_rows.py`. |
| Replay Dashboard | `dashboard.html` / `dashboard_template.html` | Complete & Tested | Zero-CDN, vanilla HTML5 Canvas interactive scrubber supporting all 5 models with rolling accuracy, mid-price, and confidence/abstain meters. |
| Presentation & Defense Guide | `docs/explanation.md` | Complete & Reviewed | File-by-file, function-by-function breakdown, plain English explanations, design rationales, and judge defense cheat sheet. |
| Tuning & Evaluation Report | `TUNING_AND_EVALUATION_REPORT.md` / `docs/TUNING_AND_EVALUATION_REPORT.md` | Complete & Verified | Grid search tuning on 60% split, held-out 40% split evaluation, ADWIN vs KS analysis, and Regime Router assessment. |
| Automated Test Suite | `tests/` + `pytest.ini` | Complete & Passing | 17 unit tests passing across all components with 0 warnings. |

---

## 3. Dependency & Environment State
- **Python Runtime:** Python 3.11.17 (`.venv`)
- **System Dependencies:** `libomp` (installed via Homebrew for LightGBM OpenMP support on macOS Apple Silicon)
- **Python Packages (`requirements.txt`):**
  - `numpy`
  - `pandas`
  - `scipy`
  - `scikit-learn`
  - `lightgbm`
  - `pyarrow`
  - `websockets`
  - `pytest`
  - `river` (v0.26.1 for streaming concept drift detection)

---

## 4. Benchmark Performance Metrics (Held-Out 40% Split: Steps 10,800–18,000)
- **Static Model:**
  - Accuracy: 48.5% | F1 Macro: 0.486 | MCC: 0.230
  - Per-sample Inference Latency: 0.009 ms
- **Periodic Retrain Model (every 2000 steps):**
  - Accuracy: 45.2% | F1 Macro: 0.446 | MCC: 0.177
  - Per-sample Inference Latency: 0.008 ms
- **Tuned DriftBook (KS Monitor + Adaptive Conformal Abstention):**
  - Accuracy: 44.5% | F1 Macro: 0.446 | MCC: 0.167
  - **Selective Accuracy:** 48.9%
  - **Abstain Rate:** 50.4% (reduced from 80.3% in baseline)
  - Detection Delay: 400 steps
  - False Alarms: **0** (reduced from 1 in baseline)
  - Per-sample Inference Latency: 0.010 ms
- **ADWIN Streaming Detector:**
  - Accuracy: 44.9% | F1 Macro: 0.446 | MCC: 0.171
  - Detection Delay: **82 steps** (fastest detector)
  - False Alarms: 2
  - Per-sample Inference Latency: 0.010 ms
- **Regime Router (Experimental - Learned from TR Training Rows):**
  - **Accuracy: 49.0%** | **F1 Macro: 0.492** | **MCC: 0.238** (Best Overall)
  - **Selective Accuracy: 51.4%**
  - **Abstain Rate: 40.1%** (Lowest Abstain Rate)
  - Detection Delay: **0 steps** (instantaneous routing)
  - False Alarms: **0**
  - Per-sample Inference Latency: 0.017 ms

---

## 5. Next Steps / Stretch Goals
1. Collect empirical multi-day order book captures from Kraken BTC/USD to validate regime router in real market conditions.
2. Explore hybrid ensemble detector combining ADWIN's fast loss tracking with KS distribution confidence.

