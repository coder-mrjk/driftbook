# DriftBook
Order-book direction forecasting that detects distribution shift, adapts, and abstains when unsure.

## Run
    pip install -r requirements.txt
    python pipeline.py                  # simulated data with planted regime shifts
    python pipeline.py --data my.parquet   # real recorded data (cols: mid, spread, b0..b4, a0..a4)
Then open `dashboard.html` (works offline; press Play). Metrics are also saved in `results.json`.

## Files
- simulate.py: synthetic order book; imbalance predicts price, but the relationship flips at steps 6000 and 11000
- pipeline.py: features (imbalance, microprice, spread, volatility), labels (down/flat/up over 5 steps), three models, metrics
  - static: trained once, never updated
  - periodic: retrained every 3000 steps
  - driftbook: rolling KS test detects shift, then refits on recent weighted data; adaptive conformal prediction abstains when unsure
- dashboard_template.html: replay dashboard (no internet or extra libraries needed)

## Not yet built
Live exchange recorder, regime-router heads, ADWIN, neural-network model, tests. Evaluation is walk-forward with no look-ahead.
