import asyncio
import json
import logging
from os.path import exists, join

import httpx
from opentelemetry import trace

from selfprivacy_api.services.remote import get_remote_service
from selfprivacy_api.services.templated_service import (
    SP_MODULES_DEFINITIONS_PATH,
    TemplatedService,
)
from selfprivacy_api.utils.redis_pool import RedisPool

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

SUGGESTED_SERVICES_REDIS_KEY = "suggestedservices:services"
_suggested_service_cache: dict[str, tuple[str, TemplatedService]] = {}


class SuggestedServices:
    @tracer.start_as_current_span("SuggestedServices.sync")
    @staticmethod
    async def sync():
        # TODO(nhnn): Is 3 too much or too little? I really don't want to overload git.selfprivacy.org with concurrent requests.
        module_fetch_semaphore = asyncio.Semaphore(3)
        redis = await RedisPool().get_connection_async()

        async with redis.lock("suggestedservices:sync"):
            async with httpx.AsyncClient() as client:
                forgejo_response = await client.get(
                    "https://git.selfprivacy.org/api/v1/repos/SelfPrivacy/selfprivacy-nixos-config/contents/sp-modules",
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                modules_list = forgejo_response.json()
                assert isinstance(modules_list, list)

            cached_payloads = await redis.hgetall(SUGGESTED_SERVICES_REDIS_KEY)
            cached_revisions = {
                name: json.loads(payload).get("revision")
                for name, payload in cached_payloads.items()
            }

            async def fetch_remote_module(name: str, rev: str):
                async with module_fetch_semaphore:
                    logger.info("Caching metadata for suggested remote module %s", name)
                    try:
                        remote_module = await get_remote_service(
                            name,
                            "git+https://git.selfprivacy.org/SelfPrivacy/"
                            + "selfprivacy-nixos-config.git?ref=flakes"
                            + f"&rev={rev}&dir=sp-modules/{name}",
                        )
                    except Exception:
                        logger.exception(
                            "Failed to cache metadata for suggested remote module %s",
                            name,
                        )
                        return None
                    logger.info(
                        "Metadata for suggested remote module %s has been updated to revision %s",
                        name,
                        rev,
                    )
                    return name, rev, remote_module.definition_data

            tasks = []
            module_names = set()
            async with asyncio.TaskGroup() as tg:
                for module in modules_list:
                    name = module["name"]
                    rev = module["last_commit_sha"]
                    module_names.add(name)
                    if cached_revisions.get(name) != rev:
                        tasks.append(tg.create_task(fetch_remote_module(name, rev)))

            removed_modules = set(cached_payloads) - module_names
            if tasks or removed_modules:
                async with redis.pipeline(transaction=True) as pipe:
                    for task in tasks:
                        result = task.result()
                        if result is None:
                            continue
                        name, rev, definition_data = result
                        pipe.hset(
                            SUGGESTED_SERVICES_REDIS_KEY,
                            name,
                            json.dumps(
                                {
                                    "revision": rev,
                                    "definition": json.dumps(definition_data),
                                }
                            ),
                        )
                    if removed_modules:
                        pipe.hdel(SUGGESTED_SERVICES_REDIS_KEY, *removed_modules)
                    await pipe.execute()

    @staticmethod
    async def get() -> list[TemplatedService]:
        with tracer.start_as_current_span("SuggestedServices.get") as span:
            redis = await RedisPool().get_connection_async()
            payloads = await redis.hgetall(SUGGESTED_SERVICES_REDIS_KEY)
            services = []

            for service_id, serialized_payload in payloads.items():
                # If service is already installed - no reason to return newer cached version as it may not represent reality.
                if exists(join(SP_MODULES_DEFINITIONS_PATH, service_id)):
                    span.add_event(
                        "Skipped suggested service as it is already installed",
                        attributes={"service_id": service_id},
                    )
                    continue

                payload = json.loads(serialized_payload)
                revision = payload.get("revision")
                cached = _suggested_service_cache.get(service_id)
                if (
                    cached is not None
                    and revision is not None
                    and cached[0] == revision
                ):
                    services.append(cached[1])
                    continue

                service = TemplatedService(service_id, payload["definition"])
                if revision is not None:
                    _suggested_service_cache[service_id] = (revision, service)
                services.append(service)

            span.set_attribute("suggested_service_count", len(services))
            return services
