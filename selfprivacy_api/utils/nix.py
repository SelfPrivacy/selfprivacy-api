"""Nix helpers."""

import asyncio
import json
import logging

from selfprivacy_api.exceptions.system import ShellException

logger = logging.getLogger(__name__)


async def evaluate_nix_file(file: str, apply: str = "f: f"):
    command = [
        "nix",
        "eval",
        "--file",
        file,
        "--apply",
        apply,
        "--json",
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode is None:
        raise Exception("Process was killed unexpectedly")
    if process.returncode != 0:
        raise ShellException(
            " ".join(command),
            stderr.decode("utf-8"),
            f"Failed to evaluate Nix expression in file {file}",
        )
    return json.loads(stdout.decode("utf-8"))


async def to_nix_expr(value):
    str_json = json.dumps(value)
    command = [
        "nix",
        "eval",
        "--expr",
        "{input}: {res = builtins.fromJSON input;}",
        "--argstr",
        "input",
        str_json,
        "res",
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise ShellException(
            " ".join(command),
            stderr.decode("utf-8"),
            "Failed to convert JSON object to Nix expression",
        )

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
        raise ShellException(
            "nixfmt",
            stderr.decode("utf-8"),
            "Failed to format Nix expression via nixfmt",
        )
    return stdout.decode("utf-8").strip()
