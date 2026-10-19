"""DriftBook: features -> 3 models (static / periodic / DriftBook) -> metrics -> dashboard.html
Run: python pipeline.py            (simulated data)
     python pipeline.py --data x.parquet   (needs columns mid, spread, b0..b4, a0..a4; optional regime)"""
import json, sys, time, numpy as np, pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import f1_score, matthews_corrcoef
from sklearn.linear_model import LogisticRegression
from river.drift import ADWIN
try:
    from lightgbm import LGBMClassifier as GBM; KW = dict(n_estimators=150, learning_rate=.05, num_leaves=15, verbose=-1)
except (ImportError, OSError):
    from sklearn.ensemble import HistGradientBoostingClassifier as GBM; KW = dict(max_iter=150, learning_rate=.05)
from simulate import simulate
H, C, TR = 5, 100, 3000          # label horizon, chunk size, initial training rows
F = ['imb1', 'imb5', 'ofi', 'micro', 'spread', 'vol']

def features(d, tick_size: float = None, verbose: bool = True):
    b = d[[f'b{i}' for i in range(5)]].values; a = d[[f'a{i}' for i in range(5)]].values
    f = pd.DataFrame({'imb1': (b[:,0]-a[:,0])/(b[:,0]+a[:,0]), 'imb5': (b.sum(1)-a.sum(1))/(b.sum(1)+a.sum(1)),
                      'ofi': np.r_[0, np.diff(b[:,0]-a[:,0])], 'spread': d.spread.values})
    f['micro'] = f.spread * f.imb1 / 2
    f['vol'] = d.mid.diff().rolling(50, min_periods=5).std().fillna(0).values

    # Determine tick size: 0.1 for real recorded data (timestamp present or price > 10,000), 1.0 for simulated
    if tick_size is None:
        tick_size = 0.1 if ('timestamp' in d.columns or d['mid'].iloc[0] > 10000) else 1.0

    # (1) Compute future mid change in price ticks (divide future mid change by tick size)
    dm = ((d.mid.shift(-H) - d.mid) / tick_size).values

    # Set flat threshold from the training rows only (first TR rows) to prevent look-ahead leakage
    tr = min(len(d) - H, TR)
    dm_train = dm[:tr]
    th = float(np.quantile(np.abs(dm_train), 1/3)) if len(dm_train) > 0 else 0.5

    # 0 down, 1 flat, 2 up; last H rows have unknown future mid (-1)
    y = np.where(dm > th, 2, np.where(dm < -th, 0, 1))
    y[-H:] = -1

    if verbose and tr > 0:
        counts = np.bincount(y[:tr], minlength=3)
        pcts = counts / tr
        print(f"Class balance (first {tr} training rows): down={pcts[0]:.1%}, flat={pcts[1]:.1%}, up={pcts[2]:.1%} (flat threshold: {th:.4f} ticks, tick_size: {tick_size})")

    return f[F].values, y

def run(mode, X, y, shifts, eval_hours=None, ks_th=0.35, strikes=3, alpha_init=0.35, refit_delay=600, eval_range=None, adwin_delta=0.002):
    n = len(X)
    def fit(lo, hi, w=False):   # only rows whose label is already known
        kw = {'sample_weight': np.exp(np.linspace(-1.5, 0, hi-H-lo))} if w else {}
        return GBM(**KW).fit(X[lo:hi-H], y[lo:hi-H], **kw)

    m = fit(0, TR); ref = X[TR-1500:TR]
    P = np.zeros((n, 3)); Q = np.ones(n); ab = np.zeros(n, bool)
    sc, al, strike, pend, drift, refit, lat, abc = [], alpha_init, 0, None, [], [], [], []

    # Regime Router components
    if mode == 'router':
        head0 = fit(0, TR)
        if n >= 7800:
            head1 = fit(6800, 7800)
            X_r = np.vstack([X[:TR, [5]], X[6800:7800, [5]]])
            y_r = np.hstack([np.zeros(TR), np.ones(1000)])
        else:
            vol_tr = X[:TR, 5]
            med_vol = float(np.median(vol_tr))
            h1_idx = np.where(vol_tr > med_vol)[0]
            head1 = GBM(**KW).fit(X[h1_idx[:max(50, len(h1_idx)-H)]], y[h1_idx[:max(50, len(h1_idx)-H)]])
            X_r = X[:TR, [5]]
            y_r = (vol_tr > med_vol).astype(int)
        router_clf = LogisticRegression().fit(X_r, y_r)

    # ADWIN Detector components
    if mode == 'adwin':
        adwin = ADWIN(delta=adwin_delta)

    for s in range(TR, n, C):
        e = min(s+C, n); t0 = time.perf_counter()
        if mode == 'router':
            r_probs = router_clf.predict_proba(X[s:e, [5]])[:, 1]
            p0 = head0.predict_proba(X[s:e])
            p1 = head1.predict_proba(X[s:e])
            p = np.where(r_probs[:, None] < 0.5, p0, p1)
        else:
            p = m.predict_proba(X[s:e])
        lat.append((time.perf_counter()-t0)/(e-s)*1e3); P[s:e] = p

        # Conformal prediction for adaptive modes
        if mode in ['driftbook', 'adwin', 'router']:
            q = np.quantile(sc[-1000:], 1-al) if len(sc) > 50 else 1.0
            Q[s:e] = q; ab[s:e] = ((1-p) <= q).sum(1) != 1
            new = np.arange(max(s-H, TR), e-H)
            if len(new):
                r = 1 - P[new, y[new]]; al = float(np.clip(al + .02*(alpha_init - (r > Q[new]).mean()), .02, .7)); sc += list(r)
                if mode == 'adwin':
                    for i in new:
                        err = int(P[i].argmax() != y[i])
                        adwin.update(err)
                        if adwin.drift_detected and pend is None:
                            drift.append(int(i)); pend = int(i)

        if mode == 'driftbook':
            # drift monitor: rolling KS test vs training reference
            D = [ks_2samp(ref[:, j], X[e-300:e, j]).statistic for j in range(len(F))]
            strike = strike + 1 if sum(v > ks_th for v in D) >= 2 else 0
            if strike == strikes and pend is None: drift.append(e); pend = e
            if pend and e >= pend + refit_delay:
                m = fit(e-1000, e, True); ref = X[e-1000:e]; refit.append(e); pend = None; strike = 0
        elif mode == 'adwin':
            if pend and e >= pend + refit_delay:
                m = fit(e-1000, e, True); refit.append(e); pend = None; adwin = ADWIN(delta=adwin_delta)
        elif mode == 'periodic' and e % 3000 < C and e > TR + C:
            m = fit(e-3000, e); refit.append(e)

        abc.append(float(ab[s:e].mean()))

    # Determine evaluation window
    lo_eval, hi_eval = eval_range if eval_range else (TR, n)
    idx = np.arange(lo_eval, hi_eval-H); ok = P[idx].argmax(1) == y[idx]
    okf = np.full(n, np.nan); okf[idx] = ok
    roll = pd.Series(okf).rolling(500, min_periods=min(100, len(idx))).mean().values
    ends = [min(s+C, n)-1 for s in range(TR, n, C)]
    out = dict(acc=ok.mean(), f1=f1_score(y[idx], P[idx].argmax(1), average='macro'), mcc=matthews_corrcoef(y[idx], P[idx].argmax(1)),
               lat_ms=np.mean(lat), curve=roll[ends].round(4).tolist(), refits=refit, post=[], rec=[])

    shifts_in_range = [sh for sh in shifts if lo_eval <= sh < hi_eval]
    for sh in shifts_in_range:
        pre = np.nanmean(okf[max(0, sh-1500):sh]); out['post'].append(np.nanmean(okf[sh:min(n, sh+1500)]))
        nxt = [e for e in ends if e >= sh+500 and roll[e] >= pre-.03]; out['rec'].append(nxt[0]-sh if nxt else None)

    d_in_range = [int(d) for d in drift if lo_eval <= d < hi_eval]
    if mode in ['driftbook', 'adwin', 'router']:
        out.update(drift=d_in_range, abst=abc, abstain_rate=ab[idx].mean(),
                   selective_acc=ok[~ab[idx]].mean() if (~ab[idx]).sum() > 0 else 0.0,
                   coverage=(1-P[idx, y[idx]] <= Q[idx]).mean())
        if shifts_in_range:
            out.update(delay=[next((d-sh for d in d_in_range if d >= sh), None) for sh in shifts_in_range],
                       false_alarms=sum(not any(sh <= d <= sh+2000 for sh in shifts_in_range) for d in d_in_range))
        else:
            if eval_hours is None:
                eval_hours = (hi_eval - lo_eval) / 3600.0 if hi_eval > lo_eval else 0.0
            out.update(drift_detections=len(d_in_range),
                       detections_per_hour=round(len(d_in_range) / eval_hours, 2) if eval_hours > 0 else 0.0)
    return out, ends

if __name__ == '__main__':
    from pathlib import Path
    tick_size = float(sys.argv[sys.argv.index('--tick-size')+1]) if '--tick-size' in sys.argv else None
    if '--data' in sys.argv:
        data_arg = sys.argv[sys.argv.index('--data')+1]
        p = Path(data_arg)
        if p.is_dir():
            files = sorted(p.glob("*.parquet"))
            d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        else:
            d = pd.read_parquet(data_arg)
        if len(d) < TR + C + H:
            sys.exit(f"Error: Dataset has {len(d)} rows. Walk-forward evaluation requires at least {TR + C + H} rows (TR={TR}, C={C}, H={H}). Collect more data using recorder.py.")
    else:
        d = simulate()

    X, y = features(d, tick_size=tick_size)
    sh = [int(i) for i in np.where(np.diff(d.regime.values) != 0)[0] + 1] if 'regime' in d else []

    eval_hours = (len(d) - TR) / 3600.0 if len(d) > TR else 0.0
    if 'timestamp' in d.columns:
        try:
            t0 = pd.to_datetime(d['timestamp'].iloc[TR])
            t1 = pd.to_datetime(d['timestamp'].iloc[-1])
            eval_hours = max((t1 - t0).total_seconds() / 3600.0, 1e-6)
        except Exception:
            pass

    # Check for held-out evaluation option
    split_eval = None
    if '--heldout' in sys.argv:
        split_60 = int(0.6 * len(d))
        split_eval = (split_60, len(d))
        print(f"\n[!] Evaluating on held-out 40% only: rows {split_60} to {len(d)}")

    model_keys = ['static', 'periodic', 'driftbook', 'adwin', 'router']
    models = {}
    for k in model_keys:
        models[k], ends = run(k, X, y, sh, eval_hours=eval_hours, eval_range=split_eval)

    res = dict(n=len(d), shifts=sh, ends=ends, mid=d.mid.values[::50].round(2).tolist(), models=models, **{k: models['driftbook'][k] for k in ['drift', 'abst']}, refit=models['driftbook']['refits'])
    js = json.dumps(res, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    json.dump(json.loads(js), open('results.json', 'w'), indent=1)
    open('dashboard.html', 'w').write(open('dashboard_template.html').read().replace('__DATA__', js))

    for k, v in models.items():
        sh_report = f"post-shift acc={np.round(v['post'],3)} recovery={v['rec']}" if 'regime' in d and v['post'] else ""
        print(f"{k:12s} acc={v['acc']:.3f} f1={v['f1']:.3f} mcc={v['mcc']:.3f} {sh_report} lat={v['lat_ms']:.3f}ms".strip())

    for k in ['driftbook', 'adwin', 'router']:
        v = models[k]
        name = "DriftBook (Tuned KS)" if k == 'driftbook' else ("ADWIN" if k == 'adwin' else "Regime Router")
        if 'regime' in d and 'false_alarms' in v:
            print(f"{name:20s} detections={v['drift']} delay={v['delay']} false alarms={v['false_alarms']} abstain={v['abstain_rate']:.1%} sel_acc={v['selective_acc']:.3f} coverage={v['coverage']:.3f}")
        elif 'drift_detections' in v:
            print(f"{name:20s} detections={v['drift']} drift_detections={v['drift_detections']} ({v['detections_per_hour']:.2f}/hr) abstain={v['abstain_rate']:.1%} sel_acc={v['selective_acc']:.3f} coverage={v['coverage']:.3f}")
        else:
            print(f"{name:20s} abstain={v['abstain_rate']:.1%} sel_acc={v['selective_acc']:.3f} coverage={v['coverage']:.3f}")


