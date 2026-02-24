import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_env():
    """
    Load environment variables from a .env file into os.environ.
    This ensures that environment configurations are explicitly managed and loaded.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}, relying on existing system environment variables.")
