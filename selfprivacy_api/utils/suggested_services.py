import logging
import httpx
import asyncio
import json

from os.path import join, exists
from opentelemetry import trace

from selfprivacy_api.services.templated_service import (
    SP_MODULES_DEFINITIONS_PATH,
    TemplatedService,
)
from selfprivacy_api.utils.redis_pool import RedisPool
from selfprivacy_api.services import get_remote_service

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class SuggestedServices:
    @tracer.start_as_current_span("SuggestedServices.sync")
    @staticmethod
    async def sync():
        # TODO(nhnn): Is 3 too much or too little? I really don't want to overload git.selfprivacy.org with concurrent requests.
        module_fetch_semaphore = asyncio.Semaphore(3)

        redis = await RedisPool().get_connection_async()

        async def fetch_remote_module(name, rev):
            async with module_fetch_semaphore:
                logger.info(f"Caching metadata for suggested remote module {name}")
                remote_module = await get_remote_service(
                    name,
                    f"git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&rev={rev}&dir=sp-modules/{name}",
                )
                await redis.set(f"suggestedservices:{name}:HEAD", rev)
                await redis.set(f"suggestedservices:{name}:data", json.dumps(remote_module.definition_data))
                logger.info(f"Metadata for suggested remote module {name} has been updated to revision {rev}")
        
        async with redis.lock("suggestedservices:sync"):
            async with httpx.AsyncClient() as client:
                forgejo_response = await client.get(
                    "https://git.selfprivacy.org/api/v1/repos/SelfPrivacy/selfprivacy-nixos-config/contents/sp-modules",
                    headers={
                        "Accept": "application/json"
                    },
                    timeout=10
                )
                modules_list = forgejo_response.json()
                assert isinstance(modules_list, list)

            async with asyncio.TaskGroup() as tg:
                for module in modules_list:
                    name = module["name"]
                    last_revision = module["last_commit_sha"]
                    cached_revision = await redis.get(f"suggestedservices:{name}:HEAD")
                    if cached_revision is None or cached_revision != last_revision:
                        tg.create_task(
                            fetch_remote_module(name, last_revision)
                        )

    @staticmethod
    async def get() -> list[TemplatedService]:
        redis = await RedisPool().get_connection_async()
        services = []

        async for key in redis.scan_iter("suggestedservices:*:data"):
            service_id = key.split("suggestedservices:")[1].split(":data")[0]

            # If service is already installed - no reason to return newer cached version as it may not represent reality.
            if exists(join(SP_MODULES_DEFINITIONS_PATH, service_id)):
                continue
            
            service_data = await redis.get(key)

            assert service_data is not None

            services.append(TemplatedService(service_id, service_data))

        return services        
