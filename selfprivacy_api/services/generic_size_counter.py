"""Generic size counter using pathlib"""

import asyncio
import os
import pathlib
import logging

from selfprivacy_api.utils.redis_pool import RedisPool

logger = logging.getLogger(__name__)


def get_storage_usage_blocking(path: str) -> int:
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


async def get_storage_usage(path: str) -> int:
    path = os.path.abspath(path)

    redis_conn = await RedisPool().get_connection_async()

    if redis_conn is not None:
        value = await redis_conn.get(f"sizecounter:path:{path}")

        if value is not None:
            return int(value)

        async with redis_conn.lock(f"sizecounter:calculatelock:{path}"):
            usage = await asyncio.get_running_loop().run_in_executor(
                None, get_storage_usage_blocking, path
            )

            await redis_conn.set(f"sizecounter:path:{path}", usage, ex=15 * 60)

        return usage

    return await asyncio.get_running_loop().run_in_executor(
        None, get_storage_usage_blocking, path
    )
