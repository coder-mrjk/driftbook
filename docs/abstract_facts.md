# DriftBook Abstract Facts & Verification Report

**Document Version:** 1.0.0  
**Verification Date:** 2026-10-23  
**Status:** All facts verified against repository code, test executions, simulation runs, and empirical Kraken data. Any unverified claim is marked strictly as "NOT VERIFIED".

---

## 1. Real Data Verification

Empirical high-frequency order-book data collected by `recorder.py` and stored in `data/*.parquet` / `combined.parquet`:

- **Exchange:** Kraken (via public WebSocket v2 API: `wss://ws.kraken.com/v2`)
- **Instrument:** `BTC/USD` (Order book subscribed at depth 25)
- **Total Recorded Rows:** 11,199 rows across 42 Parquet files
- **Date Range (UTC):**
  - **Start:** `2026-10-18T10:45:01.242517+00:00`
  - **End:** `2026-10-19T16:29:09.165254+00:00`
  - **Total Span:** 29 hours, 44 minutes, 7.9 seconds (discontinuous collection)
- **Sampling Frequency:** ~1.0 second per snapshot

### Contiguous Segments (Split where time gap > 5.0 seconds)
Splitting the 11,199 rows at every timestamp jump greater than 5 seconds yields **43 contiguous segments**:

| Segment | Start Timestamp (UTC) | End Timestamp (UTC) | Row Count | Duration (Hours) | Duration (Minutes) |
|---|---|---|---|---|---|
| **Seg 1** | 2026-10-18T10:45:01.242517+00:00 | 2026-10-18T10:45:10.260254+00:00 | 10 | 0.0025 h | 0.15 min |
| **Seg 2** | 2026-10-18T10:54:04.104434+00:00 | 2026-10-18T10:54:08.109916+00:00 | 5 | 0.0011 h | 0.07 min |
| **Seg 3** | 2026-10-18T11:02:41.182862+00:00 | 2026-10-18T11:02:50.196846+00:00 | 10 | 0.0025 h | 0.15 min |
| **Seg 4** | 2026-10-19T05:43:19.035670+00:00 | 2026-10-19T05:43:28.044293+00:00 | 10 | 0.0025 h | 0.15 min |
| **Seg 5 (Longest)** | 2026-10-19T05:44:04.884815+00:00 | 2026-10-19T08:30:53.784512+00:00 | **9,994** | **2.7802 h** | **166.81 min** |
| **Seg 6** | 2026-10-19T10:33:49.413799+00:00 | 2026-10-19T10:48:44.303524+00:00 | 895 | 0.2486 h | 14.91 min |
| **Seg 7** | 2026-10-19T10:57:35.588237+00:00 | 2026-10-19T10:57:42.604271+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 8** | 2026-10-19T11:06:37.628839+00:00 | 2026-10-19T11:06:46.647049+00:00 | 9 | 0.0025 h | 0.15 min |
| **Seg 9** | 2026-10-19T11:15:39.557025+00:00 | 2026-10-19T11:15:46.569035+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 10** | 2026-10-19T11:24:40.986364+00:00 | 2026-10-19T11:24:46.997994+00:00 | 7 | 0.0017 h | 0.10 min |
| **Seg 11** | 2026-10-19T11:33:42.263413+00:00 | 2026-10-19T11:33:49.277287+00:00 | 5 | 0.0019 h | 0.12 min |
| **Seg 12** | 2026-10-19T11:42:43.583889+00:00 | 2026-10-19T11:42:50.594327+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 13** | 2026-10-19T11:51:44.840070+00:00 | 2026-10-19T11:51:51.853683+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 14** | 2026-10-19T12:00:45.092297+00:00 | 2026-10-19T12:00:52.103607+00:00 | 6 | 0.0019 h | 0.12 min |
| **Seg 15** | 2026-10-19T12:09:47.250470+00:00 | 2026-10-19T12:09:55.262224+00:00 | 9 | 0.0022 h | 0.13 min |
| **Seg 16** | 2026-10-19T12:18:49.494831+00:00 | 2026-10-19T12:18:56.506919+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 17** | 2026-10-19T12:27:56.214640+00:00 | 2026-10-19T12:27:59.218140+00:00 | 4 | 0.0008 h | 0.05 min |
| **Seg 18** | 2026-10-19T12:36:54.615915+00:00 | 2026-10-19T12:37:00.627887+00:00 | 7 | 0.0017 h | 0.10 min |
| **Seg 19** | 2026-10-19T12:45:55.993209+00:00 | 2026-10-19T12:46:03.006748+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 20** | 2026-10-19T12:49:39.325362+00:00 | 2026-10-19T12:49:46.337315+00:00 | 6 | 0.0019 h | 0.12 min |
| **Seg 21** | 2026-10-19T12:55:21.717677+00:00 | 2026-10-19T12:55:27.724654+00:00 | 7 | 0.0017 h | 0.10 min |
| **Seg 22** | 2026-10-19T13:04:22.819066+00:00 | 2026-10-19T13:04:29.834189+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 23** | 2026-10-19T13:13:25.071630+00:00 | 2026-10-19T13:13:32.081261+00:00 | 6 | 0.0019 h | 0.12 min |
| **Seg 24** | 2026-10-19T13:22:27.217994+00:00 | 2026-10-19T13:22:38.238874+00:00 | 12 | 0.0031 h | 0.18 min |
| **Seg 25** | 2026-10-19T13:31:29.424222+00:00 | 2026-10-19T13:31:35.433257+00:00 | 5 | 0.0017 h | 0.10 min |
| **Seg 26** | 2026-10-19T13:40:30.703688+00:00 | 2026-10-19T13:40:42.722703+00:00 | 13 | 0.0033 h | 0.20 min |
| **Seg 27** | 2026-10-19T13:49:34.003337+00:00 | 2026-10-19T13:49:40.011714+00:00 | 7 | 0.0017 h | 0.10 min |
| **Seg 28** | 2026-10-19T14:07:40.619939+00:00 | 2026-10-19T14:07:44.623746+00:00 | 5 | 0.0011 h | 0.07 min |
| **Seg 29** | 2026-10-19T14:16:39.909832+00:00 | 2026-10-19T14:16:46.923114+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 30** | 2026-10-19T14:25:42.109122+00:00 | 2026-10-19T14:25:49.120197+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 31** | 2026-10-19T14:50:47.178154+00:00 | 2026-10-19T14:50:47.178154+00:00 | 1 | 0.0000 h | 0.00 min |
| **Seg 32** | 2026-10-19T14:59:42.158914+00:00 | 2026-10-19T14:59:52.177057+00:00 | 11 | 0.0028 h | 0.17 min |
| **Seg 33** | 2026-10-19T15:08:43.420837+00:00 | 2026-10-19T15:08:50.433604+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 34** | 2026-10-19T15:17:47.793370+00:00 | 2026-10-19T15:17:54.803848+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 35** | 2026-10-19T15:26:47.683982+00:00 | 2026-10-19T15:26:58.706971+00:00 | 12 | 0.0031 h | 0.18 min |
| **Seg 36** | 2026-10-19T15:35:49.602882+00:00 | 2026-10-19T15:35:56.619433+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 37** | 2026-10-19T15:44:51.925882+00:00 | 2026-10-19T15:44:57.934737+00:00 | 4 | 0.0017 h | 0.10 min |
| **Seg 38** | 2026-10-19T15:51:39.333465+00:00 | 2026-10-19T15:51:46.352724+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 39** | 2026-10-19T16:00:41.679195+00:00 | 2026-10-19T16:00:52.697528+00:00 | 12 | 0.0031 h | 0.18 min |
| **Seg 40** | 2026-10-19T16:09:43.888612+00:00 | 2026-10-19T16:09:49.899371+00:00 | 7 | 0.0017 h | 0.10 min |
| **Seg 41** | 2026-10-19T16:18:45.208236+00:00 | 2026-10-19T16:18:53.222835+00:00 | 7 | 0.0022 h | 0.13 min |
| **Seg 42** | 2026-10-19T16:27:47.193035+00:00 | 2026-10-19T16:27:54.206712+00:00 | 8 | 0.0019 h | 0.12 min |
| **Seg 43** | 2026-10-19T16:29:09.165254+00:00 | 2026-10-19T16:29:09.165254+00:00 | 1 | 0.0000 h | 0.00 min |

- **Longest Segment Details (Segment 5, saved in `longest_segment.parquet`):**
  - **Start:** `2026-10-19T05:44:04.884815+00:00`
  - **End:** `2026-10-19T08:30:53.784512+00:00`
  - **Rows:** 9,994
  - **Length in Hours:** **2.7802 hours** (10,008.9 seconds = 166.81 minutes)

---

## 2. Real-Data Run on Longest Contiguous Segment

Execution of `python pipeline.py --data longest_segment.parquet`:
- **Tick Size Detected:** 0.1 USD
- **Flat Threshold:** **0.0000 ticks**
- **Class Balance (First 3,000 training rows):**
  - **Down (0):** 15.5% (466 / 3000)
  - **Flat (1):** **59.9%** (1,798 / 3000)
  - **Up (2):** 24.5% (736 / 3000)
- **Evaluation Window:** Steps 3,000 to 9,994 (6,989 evaluation rows, 1.944 hours evaluated out-of-sample)

### Quantitative Performance Metrics

| Model | Accuracy | Macro F1 | MCC | Drift Detections | Detections / Hour | Abstain Rate | Selective Accuracy | Empirical Coverage | Latency (ms/pred) | Refit Ticks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static** | **57.2%** (0.5718) | 0.470 (0.4695) | 0.205 (0.2054) | 0 | 0.00 / hr | 0.0%* | 57.2%* | 100.0%* | **0.008 ms** | None |
| **Periodic (3k)** | 55.7% (0.5572) | 0.456 (0.4558) | 0.191 (0.1906) | 0 | 0.00 / hr | 0.0%* | 55.7%* | 100.0%* | **0.008 ms** | [6000, 9000] |
| **DriftBook (Tuned KS)** | **57.2%** (0.5718) | 0.470 (0.4695) | 0.205 (0.2054) | 0 | **0.00 / hr** | **20.6%** | **60.0%** | **65.4%** | 0.009 ms | None |
| **ADWIN (River)** | 55.0% (0.5499) | **0.485** (0.4854) | **0.208** (0.2080) | **2** (`[5367, 6666]`) | **1.03 / hr** | 25.3% | 57.7% | 65.2% | 0.008 ms | [6000, 7300] |
| **Regime Router (Exp)** | 55.4% (0.5539) | 0.463 (0.4627) | 0.191 (0.1912) | 0 | 0.00 / hr | 23.8% | 59.0% | 65.4% | 0.018 ms | None |

*\*Note on Static and Periodic:* In `pipeline.py`, conformal prediction and drift detection are disabled for `static` and `periodic` modes; their abstain rate is effectively 0.0% (coverage 100%).

---

## 3. Simulated Benchmark Results Over 20 Seeds

Empirically executed across 20 distinct random seeds (seeds 1 to 20, $T=18,000$ steps with planted regime shifts at $t=6,000$ [$\beta: +0.25 \to -0.40, \sigma: 0.35 \to 0.56$] and $t=11,000$ [$\beta: -0.40 \to +0.25, \sigma: 0.56 \to 0.35$]):

| Metric | Static Model | Periodic (every 3,000) | Tuned DriftBook (KS) | ADWIN (River) | Regime Router (Exp) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Overall Accuracy** | 0.4112 ± 0.0119 | 0.4441 ± 0.0070 | 0.4822 ± 0.0107 | **0.4882 ± 0.0128** | 0.3975 ± 0.0142 |
| **Macro F1 Score** | 0.4027 ± 0.0103 | 0.4309 ± 0.0061 | 0.4649 ± 0.0093 | **0.4711 ± 0.0087** | 0.3917 ± 0.0116 |
| **MCC (Matthews Corr)** | 0.1131 ± 0.0175 | 0.1603 ± 0.0094 | 0.2173 ± 0.0137 | **0.2265 ± 0.0166** | 0.0948 ± 0.0190 |
| **Post-Shift 1 Acc ($t=6,000$)** | 0.1893 ± 0.0228 | 0.1962 ± 0.0306 | 0.3274 ± 0.0518 | **0.3663 ± 0.0335** | 0.1977 ± 0.0260 |
| **Post-Shift 2 Acc ($t=11,000$)** | **0.5204 ± 0.0321** | 0.2843 ± 0.0268 | 0.3004 ± 0.0291 | 0.3452 ± 0.0472 | 0.4966 ± 0.0334 |
| **Post-Shift Mean Acc** | 0.3548 ± 0.0183 | 0.2403 ± 0.0221 | 0.3139 ± 0.0324 | **0.3557 ± 0.0259** | 0.3472 ± 0.0213 |
| **Shift 1 Delay (ticks)** | N/A | N/A | 395.0 ± 49.7 (20/20) | **195.1 ± 221.9** (20/20) | N/A |
| **Shift 2 Delay (ticks)** | N/A | N/A | **390.0 ± 30.0** (20/20) | 455.8 ± 668.3 (20/20) | N/A |
| **False Alarms (count)** | N/A | N/A | **0.55 ± 0.67** | 2.90 ± 1.18 | **0.00 ± 0.00** |
| **Abstain Rate** | 0.0% | 0.0% | 42.71% ± 2.08% | **41.89% ± 2.14%** | 56.87% ± 2.18% |
| **Selective Accuracy** | 41.12% ± 1.19% | 44.41% ± 0.70% | 53.54% ± 1.22% | **53.64% ± 1.51%** | 50.98% ± 2.72% |
| **Empirical Coverage** | 100.0% | 100.0% | 64.94% ± 0.13% | 65.02% ± 0.17% | 65.11% ± 0.14% |
| **Latency (ms/pred)** | 0.020 ± 0.006 ms | **0.016 ± 0.003 ms** | 0.022 ± 0.006 ms | **0.016 ± 0.001 ms** | 0.039 ± 0.012 ms |

---

## 4. Exact Method Settings

Every setting verified directly in `pipeline.py`:

1. **Feature List (`F`):**
   - 6 features total:
     1. `imb1`: Top-of-book depth imbalance: $(b_0 - a_0) / (b_0 + a_0)$
     2. `imb5`: 5-level total depth imbalance: $(\sum_{i=0}^4 b_i - \sum_{i=0}^4 a_i) / (\sum_{i=0}^4 b_i + \sum_{i=0}^4 a_i)$
     3. `ofi`: Order Flow Imbalance proxy: $[0, \text{diff}(b_0 - a_0)]$
     4. `micro`: Microprice drift proxy: $\text{spread} \times \text{imb1} / 2$
     5. `spread`: Bid-ask spread in price ticks
     6. `vol`: Mid-price rolling volatility: rolling 50-tick standard deviation of $\Delta mid$, min periods 5, fillna 0.

2. **Label Horizon and Rule:**
   - **Horizon:** $H = 5$ ticks forward.
   - **Future Mid Change in Ticks:** $dm = (\text{mid}_{t+H} - \text{mid}_t) / \text{tick\_size}$.
   - **Tick Size Scaling:** $0.1$ for real Kraken data (`'timestamp'` in columns or $\text{mid}[0] > 10,000$); $1.0$ for simulated data.
   - **Flat Threshold Rule:** $th = \text{quantile}(|dm_{\text{train}}|, 1/3)$ computed strictly from the first $TR = 3,000$ training rows. (Guarantees zero look-ahead bias).
   - **Label Encoding:**
     - $y_t = 2$ (Up) if $dm_t > th$
     - $y_t = 0$ (Down) if $dm_t < -th$
     - $y_t = 1$ (Flat) if $-th \le dm_t \le th$
     - Last $H=5$ rows assigned $y=-1$ (unobserved future).

3. **Model & Hyperparameters:**
   - Primary: LightGBM `LGBMClassifier` (with automatic fallback to `HistGradientBoostingClassifier`).
   - Hyperparameters: `n_estimators=150`, `learning_rate=0.05`, `num_leaves=15`, `verbose=-1`.
   - Initial Training Size: $TR = 3,000$ rows.
   - Walk-forward Chunk Size: $C = 100$ rows.

4. **Kolmogorov-Smirnov (KS) Drift Detector Settings:**
   - Reference baseline window: First $TR=3,000$ rows use $X[1,500:3,000]$ (1,500 rows). Post-drift refits use $X[e-1,000:e]$ (1,000 rows).
   - Test streaming window: $X[e-300:e]$ (rolling 300 rows).
   - Two-sample KS test: `scipy.stats.ks_2samp(ref[:, j], test[:, j]).statistic` evaluated for each feature $j \in \{0, \dots, 5\}$.
   - Feature KS threshold: `ks_th = 0.35`.
   - Hit Criterion: At least 2 features must simultaneously have KS statistic $> 0.35$.
   - Consecutive Hits (Strikes): `strikes = 3` consecutive chunks of $C=100$ ticks.
   - Strike Reset: Reset to 0 if fewer than 2 features exceed 0.35 in any chunk.

5. **Conformal Prediction Settings:**
   - Method: Online Adaptive Split Conformal Prediction.
   - Calibration score: Non-conformity score $r_i = 1 - P(y_i)$ (probability of true label).
   - Calibration Buffer: Rolling last 1,000 non-conformity scores (`sc[-1000:]`).
   - Error Budget / Initial Alpha: $\alpha_{\text{init}} = 0.35$ (target coverage $1 - \alpha = 65.0\%$).
   - Cutoff Quantile: $q_t = \text{quantile}(sc[-1000:], 1 - \alpha_t)$ if `len(sc) > 50` else $1.0$.
   - Prediction Set: $S_t = \{ c \in \{0, 1, 2\} : 1 - P_t(c) \le q_t \}$.
   - Abstention Criterion: Abstain if $|S_t| \neq 1$ (empty set or multi-label set).
   - Online Adaptive Alpha Update: After each chunk, $\alpha \leftarrow \text{clip}(\alpha + 0.02 \times (\alpha_{\text{init}} - \text{empirical\_error}), 0.02, 0.70)$.

6. **Model Refit Rule:**
   - Post-drift refit delay: `refit_delay = 600` ticks.
   - Retraining buffer: Once drift is flagged at step $d$, retrain when $e \ge d + 600$.
   - Retraining window: Most recent 1,000 rows ($X[e-1000:e]$).
   - Sample weighting: Exponential recency weighting:
     $$w_i = \exp\left(\text{linspace}(-1.5, 0, 1000 - H)\right)$$
   - Periodic Baseline Refit Rule: Retrains every 3,000 ticks on $X[e-3000:e]$ without sample weights.

7. **ADWIN Streaming Detector Settings:**
   - Package: `river.drift.ADWIN`.
   - Confidence Delta: `adwin_delta = 0.002` ($\delta = 2 \times 10^{-3}$).
   - Monitored Loss Stream: Streaming instantaneous binary 0-1 error: $e_t = \mathbb{I}(\arg\max P_t \neq y_t)$.
   - Reset Rule: On drift detection, wait `refit_delay = 600` ticks, refit on last 1,000 samples with exponential recency weighting, and instantiate a fresh `ADWIN(delta=0.002)`.

---

## 5. Current Status of Each Component

| Component | Status | Verification Evidence |
|---|---|---|
| **Live Recorder (`recorder.py`)** | **Complete & Operational** | Implements Kraken v2 WS feed, depth truncation to 25 levels, aggressive cross-purge, Snappy Parquet streaming. 6 unit tests passing in `tests/test_recorder.py`. |
| **Pipeline (`pipeline.py`)** | **Complete & Operational** | Implements walk-forward evaluation, features, Static, Periodic, DriftBook, ADWIN, Regime Router, `--heldout`, `--data`, `--tick-size`. 8 unit tests passing in `tests/test_pipeline.py`. |
| **Replay Dashboard (`dashboard.html`)** | **Complete & Operational** | Self-contained HTML5 Canvas, zero-CDN, offline replay with play/pause, scrub slider, rolling accuracy, mid-price, and conformal meters. Template replacement tested and verified. |
| **ADWIN Detector** | **Complete & Integrated** | Implemented via `river.drift.ADWIN(delta=0.002)` inside `pipeline.py`. Unit test passing in `tests/test_pipeline.py::test_adwin_detector`. |
| **Regime Router** | **Experimental (Present in Code)** | Implemented in `pipeline.py` (lines 58-73, 80-84). Routes between Head 0 and Head 1 via logistic regression on `vol`. Unit test passing in `tests/test_pipeline.py::test_regime_router`. |
| **Neural Network** | **NOT BUILT (Absent)** | No neural network, deep learning model (e.g. MLP, LSTM, DeepLOB, CNN) exists in the repository. The project uses LightGBM tree ensembles. |
| **Unit Test Suite (`tests/`)** | **17 Passing / 0 Failing** | Verified by running `pytest tests/ -v`: 17 passed in 13.40 seconds with 0 warnings or errors. |

---

## 6. Known Limitations, Failures & Surprising Results

### Verified Failures & Limitations

1. **Regime Router Generalization Failure in Simulation:**
   - Across 20 simulation seeds, the Regime Router achieved only **39.75% ± 1.42% accuracy** and **0.0948 ± 0.0190 MCC** — substantially worse than the simple Static baseline (41.12%) and Periodic baseline (44.41%).
   - **Root Cause Identified:** The router's two heads are fitted solely on the initial $TR = 3,000$ training rows. In `simulate.py`, the first 3,000 rows are strictly in Regime 0 ($\beta = +0.25$). Consequently, *both Head 0 and Head 1 are trained exclusively on positive-beta dynamics*. When Regime 1 begins at $t=6,000$ ($\beta = -0.40$), neither head has ever observed negative beta. The router routes to Head 1 based on higher volatility, but Head 1's predictions are completely inverted, causing post-shift 1 accuracy to plummet to **19.77% ± 2.60%**.
   - The earlier report (`TUNING_AND_EVALUATION_REPORT.md`) showed 49.0% accuracy because it evaluated exclusively on the held-out split (steps 10,800 to 18,000), where the market had reverted back to positive-beta Regime 2! Across the entire simulation, the router suffers catastrophic failure during Regime 1.

2. **Real-Data Flat Threshold Collapse to 0.0000 Ticks:**
   - In `pipeline.py`, the flat threshold is defined as $th = \text{quantile}(|dm_{\text{train}}|, 1/3)$.
   - In real Kraken BTC/USD data sampled at 1-second intervals with a 5-second horizon ($H=5$), the mid-price does not change at all over 5 seconds in **59.9%** of the training samples ($dm = 0.0$).
   - Because the zero-change proportion exceeds 33.3%, the 1/3 quantile collapses to **$th = 0.0000$ ticks**.
   - As a result, the "Flat" class absorbs 59.9% of all samples, while "Down" is 15.5% and "Up" is 24.5%.

3. **High Fragmentation in Real Data Collection:**
   - Of the 11,199 rows collected across 42 files, only one segment (Segment 5, 9,994 rows, ~2.78 hours) is continuous. The remaining 42 segments consist mostly of brief test recordings (1 to 13 rows), meaning the dataset cannot support multi-day walk-forward evaluation across diverse real market regimes.

4. **ADWIN Noise Sensitivity vs. KS Inactivity on Real Data:**
   - On the 2.78-hour Kraken segment, the tuned KS detector generated **0 detections** (0.00/hr) because order book feature distributions remained within normal variance bounds ($ks\_th=0.35$ was never exceeded by 2 features for 3 consecutive chunks).
   - Conversely, ADWIN fired **2 drift detections** (`[5367, 6666]`), achieving a higher Macro F1 (0.485 vs 0.470) and MCC (0.208 vs 0.205), but triggering refits that reduced raw accuracy from 57.2% to 55.0% due to fitting on short noisy windows.

5. **Absence of Real Execution Simulation:**
   - The pipeline predicts mid-price direction without modeling order queue dynamics, bid-ask crossing fees, fill probabilities, or market impact.

### Surprising Real-Data Results (Good & Bad)

- **Surprising (Bad) — Static Baseline Outperformed Adaptive Retraining in Raw Accuracy:**
  On real data, the Static baseline achieved **57.2% accuracy**, while Periodic retrain dropped to **55.7%** and ADWIN dropped to **55.0%**. Why? Because of the 59.9% Flat class imbalance. The static model, trained on calm initial rows, heavily predicted the dominant Flat class. Periodic and ADWIN retraining adapted to short bursts of volatility, making more aggressive Up/Down predictions that lowered raw accuracy on subsequent calm ticks.
- **Surprising (Good) — Selective Accuracy Under Conformal Abstention Worked on Real Data:**
  Even though the real data had zero KS drift detections, DriftBook's conformal prediction filter abstained on **20.6%** of predictions and elevated selective accuracy from **57.2% up to 60.0%** (a +2.8% absolute gain) while maintaining empirical coverage at **65.4%** (matching the theoretical $1 - \alpha = 65.0\%$ target with remarkable precision).
- **Surprising (Good) — Sub-10 Microsecond Inference Latency:**
  Inference latency on real Kraken data was **0.008 ms (8 microseconds) per prediction** for Static, Periodic, and ADWIN, and **0.009 ms (9 microseconds)** for DriftBook, fully satisfying ultra-low-latency high-frequency trading requirements.
