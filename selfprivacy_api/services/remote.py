import asyncio
import subprocess

from opentelemetry import trace
from selfprivacy_api.services.templated_service import (
    TemplatedService,
)

tracer = trace.get_tracer(__name__)


async def get_remote_service(id: str, url: str) -> TemplatedService:
    with tracer.start_as_current_span(
        "fetch_remote_service", attributes={"service_id": id, "url": url}
    ) as span:
        process = await asyncio.create_subprocess_exec(
            "sp-fetch-remote-module",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        span.add_event("started sp-fetch-remote-module process")
        stdout, stderr = await process.communicate()
        span.add_event("sp-fetch-remote-module process finished")

        if process.returncode is None:
            raise Exception("Process was killed unexpectedly")

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                ["sp-fetch-remote-module", url],
                stdout,
                stderr,
            )

    return TemplatedService(id, stdout.decode("utf-8"))
