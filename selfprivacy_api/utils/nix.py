"""Nix helpers."""

import subprocess
import json


def evaluate_nix_file(file: str, apply: str = "f: f"):
    return json.loads(
        subprocess.run(
            ["nix", "eval", "--file", file, "--apply", apply, "--json"],
            capture_output=True,
        ).stdout
    )


def to_nix_expr(value):
    str_json = json.dumps(value)
    nix_expr = (
        subprocess.run(
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
        )
        .stdout.decode("utf-8")
        .strip()
    )

    assert len(nix_expr) != 0

    return nix_expr


def format_nix_expr(expr: str):
    return subprocess.run(
        ["nixfmt"], input=expr, encoding="utf-8", capture_output=True
    ).stdout.strip()
