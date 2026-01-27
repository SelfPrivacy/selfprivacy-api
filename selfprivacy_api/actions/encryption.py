import asyncio
import logging
import subprocess

from opentelemetry import trace
from typing import Optional
from pydantic import BaseModel
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.utils.block_devices import BlockDevices

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class VolumeEncryptionStatus(BaseModel):
    """fscrypt encryption status for a volume."""

    is_enrolled: bool = False
    is_unlocked: bool = False
    key_id: Optional[str] = None


async def get_encryption_status_for_volume(
    volume_name: str,
) -> Optional[VolumeEncryptionStatus]:
    with tracer.start_as_current_span(
        "get_encryption_status_for_volume", attributes={"volume_name": volume_name}
    ):
        redis = RedisPool().get_connection_async()

        key_id = await redis.get(f"encryption:{volume_name}:key_id")

        if key_id is None:
            return VolumeEncryptionStatus(
                is_enrolled=False, is_unlocked=False, key_id=None
            )

        blockdev = BlockDevices().get_block_device_by_canonical_name(volume_name)

        if blockdev is None:
            return None

        process = await asyncio.create_subprocess_exec(
            "fscryptctl",
            "key_status",
            key_id,
            blockdev.mountpoints[0],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode is None:
            raise Exception("Process was killed unexpectedly")

        if process.returncode != 0:
            # TODO: proper error handling
            raise Exception("Process exited with an error")

        stdout_text = stdout.decode("utf-8")

        return VolumeEncryptionStatus(
            is_enrolled=True, is_unlocked="Present" in stdout_text, key_id=key_id
        )


async def enroll_volume_encryption(
    volume_name: str, key: bytes
) -> Optional[VolumeEncryptionStatus]:
    redis = RedisPool().get_connection_async()
    blockdev = BlockDevices().get_block_device_by_canonical_name(volume_name)

    if blockdev is None:
        return None

    if await redis.get(f"encryption:{volume_name}:key_id") is not None:
        # Already enrolled.
        return None

    process = await asyncio.create_subprocess_exec(
        "fscryptctl",
        "add_key",
        blockdev.mountpoints[0],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=key)

    if process.returncode is None:
        raise Exception("Process was killed unexpectedly")

    if process.returncode != 0:
        print("fscrypt add_key failed:", stdout, stderr)
        raise subprocess.CalledProcessError(
            process.returncode,
            [
                "fscryptctl",
                "add_key",
                blockdev.mountpoints[0],
            ],
            stdout,
            stderr,
        )

    key_id = stdout.decode("utf-8").strip()

    await redis.set(f"encryption:{volume_name}:key_id", key_id)

    return await get_encryption_status_for_volume(volume_name)
