"""Per-request async memoization used by GraphQL resolvers.

A `ContextVar` holds a dict keyed by hashable identifiers; `request_memoized`
coalesces concurrent callers on the same key onto a single asyncio.Task so
the expensive factory runs once per request.

The scope is installed by `RequestMemoExtension` in
`selfprivacy_api.graphql`. Outside a request the memo is None and every
call passes straight through to the factory.
"""

import asyncio
from contextvars import ContextVar, Token
from typing import Any, Callable, Coroutine, Hashable, Optional

_memo: ContextVar[Optional[dict]] = ContextVar("sp_request_memo", default=None)


def begin_request_memo() -> Token[Optional[dict]]:
    return _memo.set({})


def end_request_memo(token: Token[Optional[dict]]) -> None:
    _memo.reset(token)


async def request_memoized[T](
    key: Hashable, factory: Callable[[], Coroutine[Any, Any, T]]
) -> T:
    """Run factory once per request per key; concurrent callers share the task."""
    memo = _memo.get()
    if memo is None:
        return await factory()
    task = memo.get(key)
    if task is None:
        task = asyncio.create_task(factory())
        memo[key] = task
    return await task
