"""Nix helpers."""

import subprocess
import json


def evaluate_nix_file(file: str, apply: str = "f: f"):
    process = subprocess.run(
        ["nix", "eval", "--file", file, "--apply", apply, "--json"],
        capture_output=True,
        encoding="utf-8",
    )
    process.check_returncode()
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
    process.check_returncode()
    nix_expr = process.stdout.strip()

    assert len(nix_expr) != 0

    return nix_expr


def format_nix_expr(expr: str):
    process = subprocess.run(
        ["nixfmt"], input=expr, encoding="utf-8", capture_output=True
    )
    process.check_returncode()
    return process.stdout.strip()
