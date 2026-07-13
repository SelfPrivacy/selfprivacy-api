from pathlib import Path

import aiofiles
import pytest

from selfprivacy_api.exceptions.system import ShellException
from selfprivacy_api.utils.nix import evaluate_nix_file, format_nix_expr, to_nix_expr


@pytest.mark.asyncio
async def test_evaluate_nix_file_applies_expression():
    async with aiofiles.tempfile.NamedTemporaryFile() as nix_file:
        await nix_file.write(b"{ value = 42; nested.enabled = true; }")
        await nix_file.flush()

        # just in case, previous code had problems with passing PathLike objects
        nix_path = Path(nix_file.name)

        assert await evaluate_nix_file(nix_path, "f: f.value") == 42
        assert await evaluate_nix_file(nix_path) == {
            "nested": {"enabled": True},
            "value": 42,
        }


@pytest.mark.asyncio
async def test_evaluate_nix_file_raises_for_invalid_nix():
    async with aiofiles.tempfile.NamedTemporaryFile() as nix_file:
        await nix_file.write(b"{ value = ; }")
        await nix_file.flush()

        with pytest.raises(ShellException):
            await evaluate_nix_file(nix_file.name)


@pytest.mark.asyncio
async def test_nix_expr_round_trip_works():
    value = {
        "enabled": True,
        "message": "something",
        "services": ["nextcloud", "vikunja"],
    }
    async with aiofiles.tempfile.NamedTemporaryFile() as nix_file:
        await nix_file.write((await to_nix_expr(value)).encode())
        await nix_file.flush()

        assert await evaluate_nix_file(nix_file.name) == value


@pytest.mark.asyncio
async def test_to_nix_expr_raises_for_non_json_value():
    with pytest.raises(ShellException):
        await to_nix_expr(float("nan"))


@pytest.mark.asyncio
async def test_format_nix_expr_formats_works():
    assert await format_nix_expr('{value="hello";}') == '{ value = "hello"; }'


@pytest.mark.asyncio
async def test_format_nix_expr_raises_for_invalid_expression():
    with pytest.raises(ShellException):
        await format_nix_expr("{ value = ; }")
