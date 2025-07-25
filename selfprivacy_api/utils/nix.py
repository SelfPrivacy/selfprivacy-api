"""Nix helpers."""

import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class NixException(Exception):
    """Nix call errors"""

    @staticmethod
    def get_error_message() -> str:
        return "Internal nix call failed"

def evaluate_nix_file(file: str, apply: str = "f: f"):
    process = subprocess.run(
        ["nix", "eval", "--file", file, "--apply", apply, "--json"],
        capture_output=True,
        encoding="utf-8",
    )
    if process.returncode != 0:
        msg = "evaluate_nix_file Nix call failed with non zero exit code."
        logger.error(f"{msg}\n" + process.stderr)
        raise NixException(msg)
    return json.loads(process.stdout)


def to_nix_expr(value):
    str_json = json.dumps(value)
    process = subprocess.run(
        [
            "nix",
            "eval",
            "--expr",
            "{input}: {res = builtins.fromJSON input;}",
            "--argstr",
            "input",
            str_json,
            "res",
        ],
        capture_output=True,
        encoding="utf-8",
    )
    if process.returncode != 0:
        msg = "to_nix_expr Nix call failed with non zero exit code."
        logger.error(f"{msg}\n" + process.stderr)
        raise NixException(msg)
    nix_expr = process.stdout.strip()

    assert len(nix_expr) != 0

    return nix_expr


def format_nix_expr(expr: str):
    process = subprocess.run(
        ["nixfmt"], input=expr, encoding="utf-8", capture_output=True
    )
    if process.returncode != 0:
        msg = "format_nix_expr nixfmt-rfc-style call failed with non zero exit code."
        logger.error(f"{msg}\n" + process.stderr)
        raise NixException(msg)
    return process.stdout.strip()
