"""Nix helpers."""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class NixException(Exception):
    """Nix call errors"""

    @staticmethod
    def get_error_message() -> str:
        return "Internal nix call failed"


async def evaluate_nix_file(file: str, apply: str = "f: f"):
    process = await asyncio.create_subprocess_exec(
            "nix",
            "eval",
            "--file",
            file,
            "--apply",
            apply,
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode is None:
        raise Exception("Process was killed unexpectedly")
    if process.returncode != 0:
        msg = "evaluate_nix_file Nix call failed with non zero exit code."
        logger.error(f"{msg}\n" + stderr.decode("utf-8"))
        raise NixException(msg)
    return json.loads(stdout.decode("utf-8"))


async def to_nix_expr(value):
    str_json = json.dumps(value)
    process = await asyncio.create_subprocess_exec(
            "nix",
            "eval",
            "--expr",
            "{input}: {res = builtins.fromJSON input;}",
            "--argstr",
            "input",
            str_json,
            "res",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        msg = "to_nix_expr Nix call failed with non zero exit code."
        logger.error(f"{msg}\n" + stderr.decode("utf-8"))
        raise NixException(msg)
    nix_expr = stdout.decode("utf-8").strip()

    assert len(nix_expr) != 0

    return nix_expr


async def format_nix_expr(expr: str):
    process = await asyncio.create_subprocess_exec(
        "nixfmt",
        stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(expr.encode("utf-8"))
    if process.returncode != 0:
        msg = "format_nix_expr nixfmt-rfc-style call failed with non zero exit code."
        logger.error(f"{msg}\n" + stderr.decode("utf-8"))
        raise NixException(msg)
    return stdout.decode("utf-8").strip()
