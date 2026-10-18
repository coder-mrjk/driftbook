import numpy as np
import pandas as pd
import pytest
from simulate import simulate


def test_simulate_structure():
    T = 500
    shifts = (200, 350)
    d = simulate(T=T, shifts=shifts, seed=42)

    assert isinstance(d, pd.DataFrame)
    assert len(d) == T

    # Check required columns
    expected_cols = ["mid", "spread", "regime"] + [f"b{i}" for i in range(5)] + [f"a{i}" for i in range(5)]
    for col in expected_cols:
        assert col in d.columns, f"Missing column {col}"

    # Check regime shifts
    assert (d["regime"][:200] == 0).all()
    assert (d["regime"][200:350] == 1).all()
    assert (d["regime"][350:] == 2).all()

    # Check positive prices and book sizes
    assert (d["mid"] > 0).all()
    assert (d["spread"] > 0).all()
    for i in range(5):
        assert (d[f"b{i}"] > 0).all()
        assert (d[f"a{i}"] > 0).all()
