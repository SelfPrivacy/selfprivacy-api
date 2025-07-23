"""Nix helpers."""

import subprocess
import json


def evaluate_nix_file(file: str, apply: str = "f: f") -> dict:
    return json.loads(
        subprocess.run(
            ["nix", "eval", "--file", file, "--apply", apply, "--json"],
            capture_output=True,
        ).stdout
    )


def to_nix_expr(
    dict_to_convert: dict,
    format = True
):
    str_json = json.dumps(dict_to_convert)
    nix_expr = (
        subprocess.run(
            [
                "nix",
                "eval",
                "--expr",
                "{input}: {res =  builtins.fromJSON input;}",
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

    if format:
        nix_expr = subprocess.run(
            ["nixfmt"],
            input=nix_expr,
            encoding='utf-8',
            capture_output=True
        ).stdout.strip()

    # TODO: Run nixfmt-rfc-style on nix_expr to make it look pretty?

    return nix_expr
