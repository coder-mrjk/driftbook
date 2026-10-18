import numpy as np
import pandas as pd
import pytest
from simulate import simulate
from pipeline import features, run, F


def test_features_computation():
    d = simulate(T=200, shifts=(100, 150), seed=1)
    X, y = features(d)

    assert X.shape == (200, len(F))
    assert y.shape == (200,)

    # Labels should be 0, 1, 2, with the last H=5 being -1
    valid_y = y[:-5]
    assert set(np.unique(valid_y)).issubset({0, 1, 2})
    assert (y[-5:] == -1).all()

    # Features must not contain NaNs or Infs
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()


def test_pipeline_run_modes():
    # Fast test with small T, shifts located after initial training TR=3000
    d = simulate(T=4500, shifts=(3400, 3900), seed=2)
    X, y = features(d)
    shifts = [3400, 3900]

    # Run static mode
    out_static, ends = run('static', X, y, shifts)
    assert 'acc' in out_static
    assert 'f1' in out_static
    assert 'mcc' in out_static
    assert len(ends) > 0

    # Run driftbook mode
    out_db, _ = run('driftbook', X, y, shifts)
    assert 'abstain_rate' in out_db
    assert 'selective_acc' in out_db
    assert 'coverage' in out_db
    assert 0.0 <= out_db['abstain_rate'] <= 1.0
