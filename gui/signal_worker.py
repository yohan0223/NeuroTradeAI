"""
Background worker for Part 9 signal generation.

Loads real candle data from MT5 or SQLite, calculates indicators,
then evaluates a decision with the selected engine.

No orders are sent.
"""

from datetime import datetime

import MetaTrader5 as mt5
from PyQt6.QtCore import QThread, pyqtSignal

from core.mt5_connector import MT5Connector
from core.data_store import CandleStore
from core.data_engine import DataEngine
from core.indicators import IndicatorEngine
from core.weight_store import WeightStore
from core.decision_engine import RuleBasedDecisionEngine
from core.adaptive_decision_engine import AdaptiveDecisionEngine
from core.rule_features import DEFAULT_WEIGHTS
from core.signal_history import SignalRecord


class SignalWorker(QThread):
    signal_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = dict(payload or {})

    def run(self):
        candle_store = CandleStore()
        weight_store = WeightStore()
        mt5_started = False

        try:
            if not candle_store.connect():
                self.error.emit("Could not open the SQLite candle store.")
                return

            if not weight_store.connect():
                self.error.emit("Could not open the SQLite weight/contract store.")
                return

            symbol = str(self.payload.get("symbol", "")).strip()
            timeframe = str(self.payload.get("timeframe", "")).strip()
            bars = int(self.payload.get("bars", 500))
            mode = str(self.payload.get("mode", "sync"))
            engine_name = str(self.payload.get("engine", "rule"))
            include_latest = bool(self.payload.get("include_latest", False))

            if not symbol or not timeframe:
                self.error.emit("Symbol and timeframe are required.")
                return

            if mode == "sync":
                if not MT5Connector.initialize():
                    self.error.emit(
                        "MT5 initialization failed. "
                        "Ensure MT5 is running and logged into a DEMO account."
                    )
                    return

                mt5_started = True

                symbol_info = MT5Connector.get_symbol_info(symbol)
                if not symbol_info:
                    self.error.emit(f"Could not resolve symbol {symbol}.")
                    return

                resolved_symbol = symbol_info.name
                point = float(symbol_info.point)
                digits = int(symbol_info.digits)

                if point <= 0.0:
                    self.error.emit(f"Invalid point value for {resolved_symbol}.")
                    return

                weight_store.save_contract(symbol, resolved_symbol, point, digits)
                weight_store.save_contract(
                    resolved_symbol, resolved_symbol, point, digits
                )

                engine = DataEngine(
                    symbol=resolved_symbol,
                    timeframe=timeframe,
                    store=candle_store,
                )
                raw = engine.sync_recent(limit=bars)

            else:
                contract = weight_store.load_contract(symbol)

                if not contract:
                    if not MT5Connector.initialize():
                        self.error.emit(
                            "No stored contract info for this symbol and MT5 "
                            "is unavailable. Run Sync & Evaluate once first."
                        )
                        return

                    mt5_started = True

                    symbol_info = MT5Connector.get_symbol_info(symbol)
                    if not symbol_info:
                        self.error.emit(f"Could not resolve symbol {symbol}.")
                        return

                    resolved_symbol = symbol_info.name
                    point = float(symbol_info.point)
                    digits = int(symbol_info.digits)

                    if point <= 0.0:
                        self.error.emit(
                            f"Invalid point value for {resolved_symbol}."
                        )
                        return

                    weight_store.save_contract(
                        symbol, resolved_symbol, point, digits
                    )
                    weight_store.save_contract(
                        resolved_symbol, resolved_symbol, point, digits
                    )

                else:
                    resolved_symbol = contract["resolved_symbol"]
                    point = float(contract["point"])
                    digits = int(contract["digits"])

                raw = candle_store.load_candles(resolved_symbol, timeframe, bars)

                if raw.empty:
                    self.error.emit(
                        f"No stored candles for {resolved_symbol} {timeframe}. "
                        "Run Sync & Evaluate first."
                    )
                    return

            enriched = IndicatorEngine.add_indicators(raw)

            meta = {
                "symbol": resolved_symbol,
                "timeframe": timeframe,
                "rows": int(len(enriched)),
                "point": float(point),
                "digits": int(digits),
            }

            if engine_name == "adaptive":
                weights = weight_store.load_weights()
                decision_engine = AdaptiveDecisionEngine(weights=weights)
                engine_label = "adaptive"
            else:
                weights = dict(DEFAULT_WEIGHTS)
                decision_engine = RuleBasedDecisionEngine()
                engine_label = "rule"

            result = decision_engine.evaluate(
                df=enriched,
                meta=meta,
                exclude_latest=not include_latest,
            )

            record = SignalRecord(
                record_id=0,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                engine=engine_label,
                engine_version=str(result.version),
                symbol=str(result.symbol),
                timeframe=str(result.timeframe),
                decision_time=str(result.decision_time),
                action=str(result.action),
                score=float(result.score),
                confidence=float(result.confidence),
                rows_used=int(result.rows_used),
                exclude_latest=bool(result.exclude_latest),
                inputs=dict(result.inputs),
                reasons=list(result.reasons),
                warnings=list(result.warnings),
                weights=dict(weights),
            )

            self.signal_ready.emit(record)

        except Exception as exc:
            self.error.emit(str(exc))

        finally:
            if mt5_started:
                MT5Connector.shutdown()

            candle_store.close()
            weight_store.close()