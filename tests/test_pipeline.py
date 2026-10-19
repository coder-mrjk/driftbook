import numpy as np
import pandas as pd
import pytest
from simulate import simulate
from pipeline import features, run, F, TR, H


def test_features_computation():
    d = simulate(T=200, shifts=(100, 150), seed=1)
    X, y = features(d, verbose=False)

    assert X.shape == (200, len(F))
    assert y.shape == (200,)

    # Labels should be 0, 1, 2, with the last H=5 being -1
    valid_y = y[:-5]
    assert set(np.unique(valid_y)).issubset({0, 1, 2})
    assert (y[-5:] == -1).all()

    # Features must not contain NaNs or Infs
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()


def test_class_balance_and_threshold():
    # Test that labels in price ticks produce roughly balanced classes in training rows
    d = simulate(T=5000, shifts=(3400, 4200), seed=42)
    X, y = features(d, tick_size=1.0, verbose=False)

    # First TR rows
    train_y = y[:TR]
    counts = np.bincount(train_y, minlength=3)
    pcts = counts / TR

    # All three classes must be well represented and roughly balanced (~20% to ~45%)
    for i, name in enumerate(['down', 'flat', 'up']):
        assert 0.20 <= pcts[i] <= 0.45, f"Class {name} percentage {pcts[i]:.2%} out of expected ~33%"


def test_no_lookahead_leakage_in_threshold():
    # Modifying future prices after TR should NOT change the training labels
    d1 = simulate(T=4000, shifts=(3200, 3600), seed=7)
    d2 = d1.copy()
    # Inject massive price surge strictly in the test period (after TR)
    d2.loc[TR + 100:, 'mid'] += 10000.0

    _, y1 = features(d1, tick_size=1.0, verbose=False)
    _, y2 = features(d2, tick_size=1.0, verbose=False)

    # Training labels up to TR must be 100% identical (no look-ahead leakage)
    assert np.array_equal(y1[:TR], y2[:TR])


def test_tick_size_scaling():
    d = simulate(T=200, shifts=(100, 150), seed=10)
    # Testing with custom tick_size
    X1, y1 = features(d, tick_size=0.1, verbose=False)
    X2, y2 = features(d, tick_size=10.0, verbose=False)
    assert X1.shape == X2.shape
    assert (y1[-5:] == -1).all()
    assert (y2[-5:] == -1).all()


def test_pipeline_run_modes_with_regime():
    # Fast test with small T, shifts located after initial training TR=3000
    d = simulate(T=4500, shifts=(3400, 3900), seed=2)
    X, y = features(d, verbose=False)
    shifts = [3400, 3900]

    # Run static mode
    out_static, ends = run('static', X, y, shifts)
    assert 'acc' in out_static
    assert 'f1' in out_static
    assert 'mcc' in out_static
    assert len(ends) > 0

    # Run driftbook mode with regime shifts
    out_db, _ = run('driftbook', X, y, shifts)
    assert 'abstain_rate' in out_db
    assert 'selective_acc' in out_db
    assert 'coverage' in out_db
    assert 'false_alarms' in out_db
    assert 'delay' in out_db
    assert 0.0 <= out_db['abstain_rate'] <= 1.0


def test_pipeline_no_regime_reporting():
    # Dataset without regime column: must report drift_detections and detections_per_hour instead of false_alarms
    d = simulate(T=4500, shifts=(3400, 3900), seed=3)
    d = d.drop(columns=['regime'])
    X, y = features(d, verbose=False)

    # Empty shifts simulates no regime column
    shifts = []
    out_db, ends = run('driftbook', X, y, shifts, eval_hours=1.0)

    # Must contain drift_detections and detections_per_hour
    assert 'drift_detections' in out_db
    assert 'detections_per_hour' in out_db
    assert out_db['drift_detections'] == len(out_db['drift'])
    assert out_db['detections_per_hour'] == len(out_db['drift']) / 1.0

    # Must NOT report false_alarms or delay
    assert 'false_alarms' not in out_db
    assert 'delay' not in out_db


def test_adwin_detector():
    d = simulate(T=4500, shifts=(3400, 3900), seed=4)
    X, y = features(d, verbose=False)
    shifts = [3400, 3900]
    out_adwin, _ = run('adwin', X, y, shifts)
    assert 'acc' in out_adwin
    assert 'f1' in out_adwin
    assert 'abstain_rate' in out_adwin
    assert 'drift' in out_adwin
    assert isinstance(out_adwin['drift'], list)


def test_regime_router():
    d = simulate(T=4500, shifts=(3400, 3900), seed=5)
    X, y = features(d, verbose=False)
    shifts = [3400, 3900]
    out_router, _ = run('router', X, y, shifts)
    assert 'acc' in out_router
    assert 'f1' in out_router
    assert 'abstain_rate' in out_router
    assert 0.0 <= out_router['abstain_rate'] <= 1.0


def test_heldout_split_evaluation():
    d = simulate(T=5000, shifts=(3200, 4200), seed=6)
    X, y = features(d, verbose=False)
    split_60 = int(0.6 * len(d))
    out_heldout, _ = run('driftbook', X, y, [3200, 4200], eval_range=(split_60, len(d)))
    assert 'acc' in out_heldout
    assert 'f1' in out_heldout

