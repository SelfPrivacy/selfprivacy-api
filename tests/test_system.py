import pytest
from selfprivacy_api.actions.system import run_blocking, ShellException

# uname is just an arbitrary command expected to be everywhere we care


def test_uname():
    output = run_blocking(["uname"])
    assert output is not None


def test_uname_new_session():
    output = run_blocking(["uname"], new_session=True)
    assert output is not None


def test_uname_nonexistent_args():
    with pytest.raises(ShellException) as exception_info:
        # uname: extra operand ‘sldfkjsljf’
        # Try 'uname --help' for more information
        run_blocking(["uname", "isdyfhishfaisljhkeysmash"], new_session=True)
    assert "extra operand" in exception_info.value.args[0]
