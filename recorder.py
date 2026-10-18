"""
recorder.py - Live Order Book Recorder for DriftBook.

Connects to the public WebSocket order-book feed (Kraken v2), maintains a real-time
L2 order book for BTC/USD with depth truncation and crossed-book purging, records
top 5 bid and ask levels as one row per second, saves compressed Parquet files every
10 minutes, and automatically reconnects on drop.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import websockets

# Expected columns matching DriftBook pipeline requirements:
# timestamp, mid, spread (in price ticks), b0..b4, a0..a4
COLUMNS = [
    "timestamp",
    "mid",
    "spread",
    "b0",
    "b1",
    "b2",
    "b3",
    "b4",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
]


class OrderBook:
    """Thread-safe representation of an L2 Limit Order Book with depth truncation."""

    def __init__(self, tick_size: float = 0.1, depth: int = 25):
        self.tick_size = tick_size
        self.depth = depth
        self.bids: Dict[float, float] = {}  # price -> qty
        self.asks: Dict[float, float] = {}  # price -> qty
        self.last_update_ts: float = 0.0
        self.has_snapshot: bool = False
        self.crossed_count: int = 0

    def clear(self):
        """Wipes internal book state and reset snapshot flag."""
        self.bids.clear()
        self.asks.clear()
        self.has_snapshot = False
        self.crossed_count = 0

    def _truncate(self):
        """Truncate bids to top depth (highest) and asks to top depth (lowest)."""
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)[:self.depth]
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])[:self.depth]
        self.bids = dict(sorted_bids)
        self.asks = dict(sorted_asks)

    def apply_snapshot(self, bids: List[dict], asks: List[dict]):
        """Populate initial book from exchange snapshot."""
        self.bids = {float(x["price"]): float(x["qty"]) for x in bids if float(x.get("qty", 0)) > 0}
        self.asks = {float(x["price"]): float(x["qty"]) for x in asks if float(x.get("qty", 0)) > 0}
        self._truncate()
        self.has_snapshot = True
        self.last_update_ts = time.time()
        self.crossed_count = 0

    def apply_update(self, bids: List[dict], asks: List[dict]):
        """
        Apply incremental updates.
        Purges stale orders crossed by price shifts before truncating to subscribed depth.
        """
        # 1. Market microstructure invariant: incoming aggressive bids purge executed asks
        valid_bids = [b for b in bids if float(b.get("qty", 0)) > 0]
        if valid_bids:
            highest_new_bid = max(float(b["price"]) for b in valid_bids)
            self.asks = {p: q for p, q in self.asks.items() if p > highest_new_bid}

        # 2. Market microstructure invariant: incoming aggressive asks purge executed bids
        valid_asks = [a for a in asks if float(a.get("qty", 0)) > 0]
        if valid_asks:
            lowest_new_ask = min(float(a["price"]) for a in valid_asks)
            self.bids = {p: q for p, q in self.bids.items() if p < lowest_new_ask}

        # 3. Apply bid additions / modifications / cancellations
        for b in bids:
            price = float(b["price"])
            qty = float(b["qty"])
            if qty <= 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty

        # 4. Apply ask additions / modifications / cancellations
        for a in asks:
            price = float(a["price"])
            qty = float(a["qty"])
            if qty <= 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty

        # 5. Enforce depth constraint (drops levels that fell out of depth window)
        self._truncate()
        self.last_update_ts = time.time()

    def get_top5_row(self) -> Optional[dict]:
        """Extract top 5 bids and asks formatted into standard DriftBook row."""
        if not self.has_snapshot or len(self.bids) < 5 or len(self.asks) < 5:
            return None

        # Sort bids descending (highest price first), asks ascending (lowest price first)
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)[:5]
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])[:5]

        best_bid = sorted_bids[0][0]
        best_ask = sorted_asks[0][0]

        if best_bid >= best_ask:
            self.crossed_count += 1
            return None

        self.crossed_count = 0
        mid = round((best_bid + best_ask) / 2.0, 4)
        # Spread expressed in price ticks (e.g., $0.10 / $0.10 = 1 tick)
        spread_ticks = round((best_ask - best_bid) / self.tick_size, 4)

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mid": float(mid),
            "spread": float(spread_ticks),
        }
        for i in range(5):
            row[f"b{i}"] = float(sorted_bids[i][1])
            row[f"a{i}"] = float(sorted_asks[i][1])

        return row

    def needs_resync(self) -> bool:
        """Returns True if book has been persistently crossed (> 10 consecutive ticks)."""
        return self.crossed_count >= 10


class OrderBookRecorder:
    """Manages WebSocket connection, sampling, Parquet persistence, and reconnects."""

    def __init__(
        self,
        symbol: str = "BTC/USD",
        interval: float = 1.0,
        save_interval: int = 600,
        tick_size: float = 0.1,
        depth: int = 25,
        out_dir: str = "data",
        log_file: str = "recorder.log",
        max_rows: Optional[int] = None,
    ):
        self.symbol = symbol
        self.interval = interval
        self.save_interval = save_interval
        self.tick_size = tick_size
        self.depth = depth
        self.out_dir = Path(out_dir)
        self.log_file = log_file
        self.max_rows = max_rows

        self.ws_url = "wss://ws.kraken.com/v2"
        self.book = OrderBook(tick_size=tick_size, depth=depth)
        self.buffer: List[dict] = []
        self.total_rows_saved: int = 0
        self.running: bool = True
        self.last_save_time: float = time.time()
        self._ws_task: Optional[asyncio.Task] = None
        self._sample_task: Optional[asyncio.Task] = None

        self._setup_logging()
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        self.logger = logging.getLogger("recorder")
        self.logger.setLevel(logging.INFO)
        # Avoid duplicate handlers if re-initialized
        self.logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        fh = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def flush_to_parquet(self) -> Optional[Path]:
        """Saves current buffer to a compressed Parquet file."""
        if not self.buffer:
            return None

        df = pd.DataFrame(self.buffer, columns=COLUMNS)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        clean_symbol = self.symbol.replace("/", "_")
        filename = self.out_dir / f"book_{clean_symbol}_{now_str}.parquet"
        if filename.exists():
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            filename = self.out_dir / f"book_{clean_symbol}_{now_str}.parquet"

        df.to_parquet(filename, index=False, compression="snappy", engine="pyarrow")
        rows_saved = len(df)
        self.total_rows_saved += rows_saved
        self.buffer.clear()
        self.last_save_time = time.time()

        self.logger.info(
            f"Saved {rows_saved} rows to {filename} (Total saved: {self.total_rows_saved})"
        )
        return filename

    async def _sample_loop(self):
        """Samples the order book once per second."""
        self.logger.info(
            f"Starting sampling loop (every {self.interval}s, save every {self.save_interval}s)"
        )
        while self.running:
            start_t = time.time()
            row = self.book.get_top5_row()
            if row is not None:
                self.buffer.append(row)
                if len(self.buffer) % 60 == 0:
                    self.logger.info(
                        f"Buffer size: {len(self.buffer)} | Last mid: {row['mid']:.2f} | Spread: {row['spread']:.1f} ticks"
                    )

                if self.max_rows and (self.total_rows_saved + len(self.buffer)) >= self.max_rows:
                    self.logger.info(f"Target max_rows ({self.max_rows}) reached.")
                    self.flush_to_parquet()
                    self.running = False
                    break

            # Check if save interval has elapsed
            if time.time() - self.last_save_time >= self.save_interval and self.buffer:
                self.flush_to_parquet()

            # Sleep remaining time until next interval
            elapsed = time.time() - start_t
            sleep_time = max(0.05, self.interval - elapsed)
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break

    async def _ws_listen(self):
        """Maintains WebSocket connection and updates the local order book."""
        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        sub_msg = {
            "method": "subscribe",
            "params": {
                "channel": "book",
                "symbol": [self.symbol],
                "depth": self.depth,
            },
        }

        while self.running:
            self.logger.info(f"Connecting to {self.ws_url} for {self.symbol} (depth={self.depth})...")
            try:
                self.book.clear()
                async with websockets.connect(
                    self.ws_url,
                    open_timeout=10,
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    self.logger.info("Connected to WebSocket. Subscribing to book channel...")
                    await ws.send(json.dumps(sub_msg))
                    reconnect_delay = 1.0  # Reset delay on successful connection

                    async for message in ws:
                        if not self.running:
                            break

                        if self.book.needs_resync():
                            self.logger.warning("OrderBook crossed persistently. Re-subscribing for fresh snapshot...")
                            break

                        data = json.loads(message)

                        # Handle subscription response or error
                        if "success" in data and not data.get("success"):
                            self.logger.error(f"Subscription error: {data}")
                            break

                        channel = data.get("channel")
                        msg_type = data.get("type")

                        if channel == "book" and "data" in data:
                            for entry in data["data"]:
                                bids = entry.get("bids", [])
                                asks = entry.get("asks", [])
                                if msg_type == "snapshot":
                                    self.book.apply_snapshot(bids, asks)
                                    self.logger.info(
                                        f"Received initial order-book snapshot for {self.symbol} "
                                        f"({len(self.book.bids)} bids, {len(self.book.asks)} asks)"
                                    )
                                elif msg_type == "update":
                                    self.book.apply_update(bids, asks)

            except (websockets.ConnectionClosed, asyncio.TimeoutError, OSError) as e:
                self.logger.warning(f"WebSocket disconnected ({e}). Reconnecting in {reconnect_delay:.1f}s...")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in WebSocket loop: {e}", exc_info=True)

            if self.running:
                try:
                    await asyncio.sleep(reconnect_delay)
                except asyncio.CancelledError:
                    break
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

    async def run(self):
        """Runs the listener and sampler concurrently until stopped."""
        self._ws_task = asyncio.create_task(self._ws_listen())
        self._sample_task = asyncio.create_task(self._sample_loop())

        try:
            await asyncio.gather(self._ws_task, self._sample_task)
        except asyncio.CancelledError:
            self.logger.info("Recorder tasks cancelled.")
        finally:
            self.flush_to_parquet()
            self.logger.info(f"Recorder stopped. Total rows saved: {self.total_rows_saved}")

    def stop(self):
        """Signal recorder to shut down and flush remaining data promptly."""
        self.logger.info("Stop signal received. Shutting down...")
        self.running = False
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
        if self._sample_task and not self._sample_task.done():
            self._sample_task.cancel()


def main():
    parser = argparse.ArgumentParser(description="Live order-book recorder for DriftBook.")
    parser.add_argument("--symbol", default="BTC/USD", help="Order book symbol (default: BTC/USD)")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds (default: 1.0)")
    parser.add_argument("--save-interval", type=int, default=600, help="Parquet flush interval in seconds (default: 600, 10 min)")
    parser.add_argument("--tick-size", type=float, default=0.1, help="Price tick size (default: 0.1 for BTC/USD on Kraken)")
    parser.add_argument("--depth", type=int, default=25, help="Subscribed order book depth (default: 25)")
    parser.add_argument("--out-dir", default="data", help="Output directory for parquet files (default: data)")
    parser.add_argument("--log-file", default="recorder.log", help="Log file path (default: recorder.log)")
    parser.add_argument("--max-rows", type=int, default=None, help="Stop after recording max rows (optional)")
    args = parser.parse_args()

    recorder = OrderBookRecorder(
        symbol=args.symbol,
        interval=args.interval,
        save_interval=args.save_interval,
        tick_size=args.tick_size,
        depth=args.depth,
        out_dir=args.out_dir,
        log_file=args.log_file,
        max_rows=args.max_rows,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _sig_handler():
        recorder.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _sig_handler)
        except NotImplementedError:
            # Windows fallback
            pass

    try:
        loop.run_until_complete(recorder.run())
    except KeyboardInterrupt:
        recorder.stop()
        recorder.flush_to_parquet()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
