import sys
import logging
from PyQt6.QtWidgets import QApplication
from core.mt5_connector import MT5Connector
from core.database import DatabaseManager
from config import DEFAULT_SYMBOL

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main entry point for NeuroTrade AI."""
    setup_logging()
    logging.info("Starting NeuroTrade AI - Part 1 Verification")
    
    # 1. Database Setup
    db = DatabaseManager()
    if not db.connect():
        logging.critical("Failed to connect to database. Exiting.")
        sys.exit(1)
        
    # 2. MT5 Connection
    if not MT5Connector.initialize():
        logging.critical("Failed to initialize MT5. Ensure terminal is running and logged into a DEMO account. Exiting.")
        db.close()
        sys.exit(1)
        
    # 3. Symbol Resolution
    symbol_info = MT5Connector.get_symbol_info(DEFAULT_SYMBOL)
    if symbol_info:
        logging.info(f"Successfully loaded symbol: {symbol_info.name}")
        logging.info(f"Digits: {symbol_info.digits}, Volume Min: {symbol_info.volume_min}, Max: {symbol_info.volume_max}")
    else:
        logging.warning(f"Could not load default symbol {DEFAULT_SYMBOL}.")
        
    # Clean up
    MT5Connector.shutdown()
    db.close()
    
    logging.info("Part 1 verification completed successfully.")

if __name__ == "__main__":
    # Initialize QApplication as PyQt6 will be used in future parts
    app = QApplication(sys.argv)
    main()
    # app.exec() will be used when GUI is built in Part 2