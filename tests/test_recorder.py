import os
import shutil
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from recorder import OrderBook, OrderBookRecorder, COLUMNS


def test_order_book_snapshot_and_update():
    book = OrderBook(tick_size=0.1)
    assert not book.has_snapshot
    assert book.get_top5_row() is None

    # Apply snapshot
    bids = [{"price": 100.0 - i * 0.1, "qty": 1.0 + i} for i in range(10)]
    asks = [{"price": 100.1 + i * 0.1, "qty": 2.0 + i} for i in range(10)]
    book.apply_snapshot(bids, asks)

    assert book.has_snapshot
    row = book.get_top5_row()
    assert row is not None

    # Check columns
    for col in COLUMNS:
        assert col in row

    # Best bid: 100.0, Best ask: 100.1 -> mid = 100.05
    assert abs(row["mid"] - 100.05) < 1e-6
    # Spread: (100.1 - 100.0) / 0.1 = 1.0 tick
    assert abs(row["spread"] - 1.0) < 1e-6

    # b0 should be 1.0, a0 should be 2.0
    assert abs(row["b0"] - 1.0) < 1e-6
    assert abs(row["a0"] - 2.0) < 1e-6

    # Apply update: cancel best bid (qty = 0) and add tighter ask
    book.apply_update(
        bids=[{"price": 100.0, "qty": 0.0}],
        asks=[{"price": 100.05, "qty": 0.5}],
    )

    new_row = book.get_top5_row()
    assert new_row is not None
    # Now best bid is 99.9, best ask is 100.05
    assert abs(new_row["b0"] - 2.0) < 1e-6  # Was index 1 with qty 2.0
    assert abs(new_row["a0"] - 0.5) < 1e-6
    assert abs(new_row["mid"] - ((99.9 + 100.05) / 2.0)) < 1e-6


def test_order_book_crossed_safety():
    book = OrderBook(tick_size=0.1)
    # Best bid higher than best ask
    bids = [{"price": 101.0 - i * 0.1, "qty": 1.0} for i in range(6)]
    asks = [{"price": 100.0 + i * 0.1, "qty": 1.0} for i in range(6)]
    book.apply_snapshot(bids, asks)

    assert book.get_top5_row() is None


def test_recorder_flush_to_parquet():
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test.log")
    try:
        recorder = OrderBookRecorder(
            symbol="BTC/USD",
            interval=0.1,
            save_interval=10,
            tick_size=0.1,
            out_dir=temp_dir,
            log_file=log_file,
        )

        # Populate buffer manually
        for t in range(5):
            recorder.buffer.append({
                "timestamp": f"2026-10-18T10:00:0{t}Z",
                "mid": 1000.0 + t,
                "spread": 1.0,
                "b0": 1.0, "b1": 1.1, "b2": 1.2, "b3": 1.3, "b4": 1.4,
                "a0": 2.0, "a1": 2.1, "a2": 2.2, "a3": 2.3, "a4": 2.4,
            })

        filepath = recorder.flush_to_parquet()
        assert filepath is not None
        assert filepath.exists()

        # Read back with pandas
        df = pd.read_parquet(filepath)
        assert len(df) == 5
        assert list(df.columns) == COLUMNS
        assert df["mid"].iloc[0] == 1000.0
        assert df["mid"].iloc[-1] == 1004.0
    finally:
        shutil.rmtree(temp_dir)
