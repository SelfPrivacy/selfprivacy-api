import asyncio
from contextvars import ContextVar, Token
from typing import Any, Awaitable, Callable, Hashable, Optional

_memo: ContextVar[Optional[dict]] = ContextVar("sp_request_memo", default=None)


def begin_request_memo() -> Token:
    return _memo.set({})


def end_request_memo(token: Token) -> None:
    _memo.reset(token)


async def request_memoized(key: Hashable, factory: Callable[[], Awaitable]) -> Any:
    """Runs a factory once per request, concurrent callers share single task"""
    memo = _memo.get()
    if memo is None:
        return await factory()
    task = memo.get(key)
    if task is None:
        task = asyncio.ensure_future(factory())
        memo[key] = task
    return await task
