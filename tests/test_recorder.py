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


def test_order_book_depth_truncation():
    book = OrderBook(tick_size=0.1, depth=10)
    bids = [{"price": 100.0 - i * 0.1, "qty": 1.0} for i in range(25)]
    asks = [{"price": 100.1 + i * 0.1, "qty": 1.0} for i in range(25)]
    book.apply_snapshot(bids, asks)

    # OrderBook must strictly truncate to depth 10
    assert len(book.bids) == 10
    assert len(book.asks) == 10
    assert min(book.bids.keys()) >= 99.1 - 1e-6
    assert max(book.asks.keys()) <= 101.0 + 1e-6


def test_order_book_price_rally_and_drop_resilience():
    book = OrderBook(tick_size=0.1, depth=10)
    # Initial snapshot at 100
    book.apply_snapshot(
        bids=[{"price": 100.0 - i * 0.1, "qty": 1.0} for i in range(10)],
        asks=[{"price": 100.1 + i * 0.1, "qty": 1.0} for i in range(10)],
    )
    row1 = book.get_top5_row()
    assert row1 is not None
    assert abs(row1["mid"] - 100.05) < 1e-6

    # Market rallies to 110: new bids at 110, new asks at 110.1
    book.apply_update(
        bids=[{"price": 110.0 - i * 0.1, "qty": 1.0} for i in range(10)],
        asks=[{"price": 110.1 + i * 0.1, "qty": 1.0} for i in range(10)],
    )
    row2 = book.get_top5_row()
    assert row2 is not None, "Book should not be permanently crossed after price rally"
    assert abs(row2["mid"] - 110.05) < 1e-6

    # Market drops to 95: new bids at 95, new asks at 95.1
    book.apply_update(
        bids=[{"price": 95.0 - i * 0.1, "qty": 1.0} for i in range(10)],
        asks=[{"price": 95.1 + i * 0.1, "qty": 1.0} for i in range(10)],
    )
    row3 = book.get_top5_row()
    assert row3 is not None, "Book should not be permanently crossed after price drop"
    assert abs(row3["mid"] - 95.05) < 1e-6


def test_order_book_needs_resync():
    book = OrderBook(tick_size=0.1, depth=10)
    book.has_snapshot = True
    book.bids = {105.0: 1.0, 104.9: 1.0, 104.8: 1.0, 104.7: 1.0, 104.6: 1.0}
    book.asks = {100.0: 1.0, 100.1: 1.0, 100.2: 1.0, 100.3: 1.0, 100.4: 1.0}

    assert not book.needs_resync()
    for _ in range(10):
        book.get_top5_row()
    assert book.needs_resync()


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
