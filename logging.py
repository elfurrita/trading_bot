# logging.py

import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler("trading_bot.log"),
                                  logging.StreamHandler()])
