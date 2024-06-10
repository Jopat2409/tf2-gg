from services import test_func
from utils import Logger

import sys

if __name__ == "__main__":
    args = sys.argv[1::]

    Logger.init("logs", "scraper", "verbose" in args)

    __logger = Logger.get_logger()
    if "rgl" in args:
        __logger.log_info("Scraping RGL data")
        test_func()
