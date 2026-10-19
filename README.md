# DriftBook

Quantitative order-book direction forecasting under market regime shifts with adaptive conformal prediction, streaming drift detection, and multi-head regime routing.

Built for the **IIT Bombay & Optiver AI Innovation Lab Perceptron Hackathon** (Theme 3: Markets & Trading Intelligence, Problem 4: Order Book Forecasting Under Regime Shifts).

---

## What Does DriftBook Do?

In quantitative market making and algorithmic trading, machine learning models fail silently when market regimes change (e.g., sudden volatility spikes, liquidity dry-ups, or flow direction reversals).

DriftBook solves this problem through three layers of defense:
1. **Walk-Forward Microstructure Forecasting**: Predicts next short-term price movement (Down, Flat, Up) from Level-2 order book depth features (order book imbalance, microprice drift, spread, and short-term volatility).
2. **Concept & Covariate Drift Detection**:
   - **Distribution-Level (KS Detector)**: Monitors rolling Kolmogorov-Smirnov statistics across features against a baseline window to catch structural distribution shifts without false alarms.
   - **Loss-Level (River ADWIN)**: Tracks streaming prediction error rates $e_t = \mathbb{I}(\hat{y}_t \neq y_t)$ to react to performance decay in sub-100 ticks.
3. **Adaptive Conformal Abstention & Regime Routing**:
   - **Conformal Prediction Sets**: Constructs calibrated prediction sets $[S_t \subseteq \{\text{Down}, \text{Flat}, \text{Up}\}]$ at target coverage (e.g., $1-\alpha$). If the set is empty or contains multiple labels, the model **abstains from trading**, preventing adverse selection.
   - **Multi-Head Regime Router**: Automatically routes order-book states between specialized prediction heads (e.g. low-volatility normal regimes vs. high-volatility shock regimes) with zero adaptation delay.

---

## Quickstart: How to Run the App & See It Working

### 1. Environment Setup
```bash
# Clone and enter directory
cd /Users/karthi/driftbook

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies (river, scikit-learn, lightgbm, pyarrow, websockets, pytest)
pip install -r requirements.txt
```

### 2. Run Forecasting Pipeline on Benchmark Simulation
```bash
python pipeline.py
```
This runs walk-forward evaluation across all 5 models (Static, Periodic, Tuned DriftBook, River ADWIN, and Regime Router) over 18,000 steps with planted regime shifts at steps 6,000 and 11,000. It prints the class balance, metrics, detection times, and regenerates `results.json` and `dashboard.html`.

### 3. Run Pipeline on Held-Out Period Only (Final 40%)
```bash
python pipeline.py --heldout
```
Evaluates models out-of-sample on steps 10,800 to 18,000 with zero look-ahead bias.

### 4. Run Pipeline on Real Recorded Kraken BTC/USD Data
```bash
python pipeline.py --data combined.parquet
```

### 5. View the Interactive Replay Dashboard
```bash
# Open in your default browser on macOS
open dashboard.html
```
- Click **Play** (or press the Play button) to watch real-time order-book replay at 70ms tick intervals.
- Use the **Interactive Scrubber Slider** to jump to any tick (e.g., step 6,000 or 11,000) to observe how drift detectors fire, models adapt, and conformal meters switch to "ABSTAIN".
- Compare real-time rolling accuracy curves between Static, Periodic, DriftBook (KS), ADWIN, and Regime Router.

### 6. Record Live Real-Time Order Book Data from Kraken
```bash
# Stream live L2 order book updates (BTC/USD depth 25) via WebSocket
python recorder.py

# Check how many rows have been recorded so far
python count_rows.py
```

### 7. Run Automated Tests
```bash
pytest tests/ -v
```
Runs the 17 unit tests covering simulator integrity, pipeline execution, ADWIN detector, regime router, Kraken WebSocket recorder, order-book depth truncation, cross-purging, and row counting.

---

## Architecture & Project Structure

- `pipeline.py`: Feature engineering, walk-forward evaluation, KS drift detection, River ADWIN, conformal prediction sets, and multi-head regime routing.
- `simulate.py`: Realistic limit order book simulator with planted regime shifts (beta sign flips, volatility jumps).
- `recorder.py`: Industrial-grade Kraken v2 WebSocket recorder with depth truncation, aggressive cross-purge, and Parquet streaming flushes.
- `count_rows.py`: Zero-copy Parquet header reader to monitor live recording progress.
- `dashboard.html` / `dashboard_template.html`: Self-contained, offline HTML5 Canvas replay dashboard with zero external CDN dependencies.
- `combined.parquet`: Verified dataset of 10,029 recorded rows of real Kraken BTC/USD order book ticks.
- `TUNING_AND_EVALUATION_REPORT.md`: Grid search hyperparameter tuning table, held-out evaluation benchmarks, and comparative trade-off analysis.
- `docs/STATE.md`: Formal project state log and versioned milestones.
- `docs/FINAL_PRODUCTION_HANDOVER.md`: Production operations runbook and handover specification.
- `docs/explanation.md`: In-depth 60-second pitch, microstructure theory, function-by-function guide, and judge Q&A defense.
- `tests/`: 17 comprehensive unit tests with full CI/regression coverage.

---

## Benchmark Performance Highlights (Held-Out 40% Split)

| Model | Accuracy | Macro F1 | MCC | Abstain Rate | Selective Accuracy | Drift Alert Lag |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static** | 48.5% | 0.486 | 0.230 | 0.0% | 48.5% | None |
| **Periodic (2k)** | 45.2% | 0.446 | 0.177 | 0.0% | 45.2% | None |
| **Tuned DriftBook (KS)** | 44.5% | 0.446 | 0.167 | 50.4% | 48.9% | 400 steps (0 false alarms) |
| **ADWIN (River)** | 44.9% | 0.446 | 0.171 | 51.0% | 48.6% | **82 steps** (2 false alarms) |
| **Regime Router** | **49.0%** | **0.492** | **0.238** | **40.1%** | **51.4%** | **Instant (0 steps)** |
