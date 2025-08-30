import logging
import os

def setup_logger(name: str, level=logging.INFO):
    """Setup a logger with file + stream handler"""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}.log")
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Prevent adding multiple handlers in debug mode reload
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

        # Stream handler (console)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s: %(name)s - %(message)s"))

        logger.addHandler(fh)
        logger.addHandler(sh)

    return logger