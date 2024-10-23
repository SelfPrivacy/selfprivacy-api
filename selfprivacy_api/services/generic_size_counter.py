"""Generic size counter using pathlib"""

import pathlib
import logging

logger = logging.getLogger(__name__)


def get_storage_usage(path: str) -> int:
    """
    Calculate the real storage usage of path and all subdirectories.
    Calculate using pathlib.
    Do not follow symlinks.
    """
    storage_usage = 0
    for iter_path in pathlib.Path(path).rglob("**/*"):
        if iter_path.is_dir():
            continue
        try:
            storage_usage += iter_path.stat().st_size
        except FileNotFoundError:
            pass
        except Exception as error:
            logging.error(error)
    return storage_usage
