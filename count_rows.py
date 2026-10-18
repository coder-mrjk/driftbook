"""
count_rows.py - Inspects and reports the number of order-book rows collected.

Scans the Parquet storage directory (default: data/), extracts row counts
and metadata from each file, and prints summary totals.
"""

import argparse
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd


def count_collected_rows(directory: str = "data") -> int:
    path = Path(directory)
    if not path.exists():
        print(f"Directory '{directory}' does not exist.")
        return 0

    files = sorted(list(path.glob("*.parquet")))
    if not files:
        print(f"No Parquet files found in '{directory}'.")
        return 0

    print("=" * 70)
    print(f"DRIFTBOOK DATA RECORDINGS - '{directory}'")
    print("=" * 70)
    print(f"{'Filename':<38} | {'Rows':>8} | {'Size':>9} | {'Time Range (UTC)'}")
    print("-" * 70)

    total_rows = 0
    total_bytes = 0

    for f in files:
        file_size = f.stat().st_size
        total_bytes += file_size
        size_str = (
            f"{file_size / 1024:.1f} KB"
            if file_size < 1024 * 1024
            else f"{file_size / (1024 * 1024):.2f} MB"
        )

        try:
            pfile = pq.ParquetFile(f)
            num_rows = pfile.metadata.num_rows
            total_rows += num_rows

            time_range = ""
            if num_rows > 0:
                # Read only timestamp column to determine exact interval
                df_ts = pd.read_parquet(f, columns=["timestamp"])
                t_start = df_ts["timestamp"].iloc[0][:19].replace("T", " ")
                t_end = df_ts["timestamp"].iloc[-1][:19].replace("T", " ")
                time_range = f"{t_start} -> {t_end}"

            print(f"{f.name:<38} | {num_rows:>8d} | {size_str:>9} | {time_range}")
        except Exception as e:
            print(f"{f.name:<38} | ERROR: {e}")

    total_size_str = (
        f"{total_bytes / 1024:.1f} KB"
        if total_bytes < 1024 * 1024
        else f"{total_bytes / (1024 * 1024):.2f} MB"
    )
    print("-" * 70)
    print(
        f"TOTAL: {len(files)} file(s), {total_rows:,} rows collected ({total_size_str})"
    )
    print("=" * 70)
    return total_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print number of order-book rows collected in Parquet files."
    )
    parser.add_argument(
        "--dir", default="data", help="Directory containing Parquet files (default: data)"
    )
    args = parser.parse_args()
    count_collected_rows(args.dir)
