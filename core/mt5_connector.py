import MetaTrader5 as mt5
import logging
from config import DEFAULT_SYMBOL, MT5_PATH


class MT5Connector:
    """Handles connection and interactions with the MetaTrader 5 terminal."""

    @staticmethod
    def _get_account_mode_name(mode: int) -> str:
        """Return human-readable account trade mode name."""
        mapping = {
            getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0): "DEMO",
            getattr(mt5, "ACCOUNT_TRADE_MODE_REAL", 1): "REAL",
            getattr(mt5, "ACCOUNT_TRADE_MODE_CONTEST", 2): "CONTEST",
        }
        return mapping.get(mode, f"UNKNOWN({mode})")

    @staticmethod
    def initialize() -> bool:
        """Initialize the MT5 terminal."""
        try:
            if MT5_PATH:
                initialized = mt5.initialize(MT5_PATH)
            else:
                initialized = mt5.initialize()
        except Exception as exc:
            logging.error(f"MT5 initialization exception: {exc}")
            return False

        if not initialized:
            logging.error(f"MT5 initialization failed. Error code: {mt5.last_error()}")
            return False

        account_info = mt5.account_info()
        if not account_info:
            logging.error("Failed to get account info. Ensure MT5 terminal is logged in.")
            mt5.shutdown()
            return False

        mode = int(account_info.trade_mode)

        demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
        real_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_REAL", 1)

        mode_name = MT5Connector._get_account_mode_name(mode)

        logging.info(
            f"Connected to MT5. Account: {account_info.login}, "
            f"Server: {account_info.server}, Mode: {mode_name} (trade_mode={mode})"
        )

        if mode == real_mode:
            logging.critical("Connected to REAL account. ABORTING! (DEMO ONLY rule enforced)")
            mt5.shutdown()
            return False

        if mode != demo_mode:
            logging.critical(
                f"Account mode is {mode_name}, not DEMO. ABORTING! (DEMO ONLY rule enforced)"
            )
            mt5.shutdown()
            return False

        logging.info("DEMO account confirmed.")
        return True

    @staticmethod
    def resolve_symbol(symbol_name: str) -> str:
        """Resolve the exact symbol name from the broker."""
        symbols = mt5.symbols_get()
        if not symbols:
            logging.error("Failed to get symbols.")
            return None

        # Exact match first
        for s in symbols:
            if s.name == symbol_name:
                return s.name

        # Partial match, for example:
        # XAUUSD, XAUUSD.a, GOLD, XAUUSDm, etc.
        for s in symbols:
            if symbol_name.lower() in s.name.lower() or s.name.lower() in symbol_name.lower():
                logging.info(f"Resolved {symbol_name} to broker symbol: {s.name}")
                return s.name

        logging.error(f"Symbol {symbol_name} not found in broker list.")
        return None

    @staticmethod
    def get_symbol_info(symbol_name: str):
        """Get symbol information and ensure it is selected in Market Watch."""
        resolved_name = MT5Connector.resolve_symbol(symbol_name)
        if not resolved_name:
            return None

        symbol_info = mt5.symbol_info(resolved_name)
        if not symbol_info:
            # Try selecting it if it was not available initially
            if not mt5.symbol_select(resolved_name, True):
                logging.error(f"Failed to select symbol {resolved_name}")
                return None
            symbol_info = mt5.symbol_info(resolved_name)

        if not symbol_info.visible:
            logging.info(f"Symbol {resolved_name} not visible, attempting to select.")
            if not mt5.symbol_select(resolved_name, True):
                logging.error(f"Failed to select symbol {resolved_name}")
                return None

        return mt5.symbol_info(resolved_name)

    @staticmethod
    def shutdown():
        """Shutdown the MT5 terminal connection."""
        mt5.shutdown()
        logging.info("MT5 connection closed.")