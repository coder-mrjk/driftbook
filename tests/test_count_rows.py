import os
import shutil
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from count_rows import count_collected_rows


def test_count_rows_empty_and_populated():
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Empty directory
        assert count_collected_rows(temp_dir) == 0

        # 2. Non-existent directory
        assert count_collected_rows(os.path.join(temp_dir, "nonexistent")) == 0

        # 3. Create sample parquet file
        df1 = pd.DataFrame({
            "timestamp": ["2026-10-18T10:00:00Z", "2026-10-18T10:00:01Z", "2026-10-18T10:00:02Z"],
            "mid": [100.0, 100.1, 100.2],
            "spread": [1.0, 1.0, 1.0],
            "b0": [1.0, 1.0, 1.0], "b1": [1.0, 1.0, 1.0], "b2": [1.0, 1.0, 1.0], "b3": [1.0, 1.0, 1.0], "b4": [1.0, 1.0, 1.0],
            "a0": [2.0, 2.0, 2.0], "a1": [2.0, 2.0, 2.0], "a2": [2.0, 2.0, 2.0], "a3": [2.0, 2.0, 2.0], "a4": [2.0, 2.0, 2.0],
        })
        df1.to_parquet(Path(temp_dir) / "f1.parquet", compression="snappy")

        df2 = pd.DataFrame({
            "timestamp": ["2026-10-18T10:05:00Z", "2026-10-18T10:05:01Z"],
            "mid": [101.0, 101.1],
            "spread": [1.0, 1.0],
            "b0": [1.0, 1.0], "b1": [1.0, 1.0], "b2": [1.0, 1.0], "b3": [1.0, 1.0], "b4": [1.0, 1.0],
            "a0": [2.0, 2.0], "a1": [2.0, 2.0], "a2": [2.0, 2.0], "a3": [2.0, 2.0], "a4": [2.0, 2.0],
        })
        df2.to_parquet(Path(temp_dir) / "f2.parquet", compression="snappy")

        # 4. File without timestamp column
        df3 = pd.DataFrame({"mid": [102.0, 102.1]})
        df3.to_parquet(Path(temp_dir) / "f3.parquet", compression="snappy")

        assert count_collected_rows(temp_dir) == 7
    finally:
        shutil.rmtree(temp_dir)
