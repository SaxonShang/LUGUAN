import logging
import os

def setup_logging(log_file="logs/app.log"):
    """
    Sets up logging configuration.
    
    Logs messages to both the console and a log file.
    
    Args:
        log_file (str): Path to the log file (default: logs/app.log)
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))  # ✅ Create logs directory if missing

    logger = logging.getLogger("AppLogger")
    logger.setLevel(logging.DEBUG)  # ✅ Capture all log levels

    # ✅ Console Logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # ✅ Console shows INFO+ logs

    # ✅ File Logger
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)  # ✅ File stores all logs (DEBUG+)

    # ✅ Log Format
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # ✅ Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# ✅ Example Usage
if __name__ == "__main__":
    log = setup_logging()
    log.debug("Debugging mode active.")
    log.info("System is running.")
    log.warning("This is a warning!")
    log.error("An error occurred!")
