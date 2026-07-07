import asyncio
from typing import cast
from unittest.mock import MagicMock

import pytest
from strawberry.types import ExecutionContext

from selfprivacy_api.graphql import RequestMemoExtension
from selfprivacy_api.utils.request_memo import (
    _memo,
    begin_request_memo,
    end_request_memo,
    request_memoized,
)


class Counter:
    def __init__(self):
        self.calls = 0

    def bump(self):
        self.calls += 1


async def test_no_memo_passthrough():
    counter = Counter()

    async def factory():
        await asyncio.sleep(0)
        counter.bump()
        return "value"

    assert await request_memoized("k", factory) == "value"
    assert await request_memoized("k", factory) == "value"
    assert counter.calls == 2


async def test_memoizes_within_scope():
    counter = Counter()

    async def factory():
        await asyncio.sleep(0)
        counter.bump()
        return counter.calls

    token = begin_request_memo()
    try:
        first = await request_memoized("k", factory)
        second = await request_memoized("k", factory)
    finally:
        end_request_memo(token)

    assert first == 1
    assert second == 1
    assert counter.calls == 1


async def test_distinct_keys_are_independent():
    counter = Counter()

    async def factory():
        await asyncio.sleep(0)
        counter.bump()
        return counter.calls

    token = begin_request_memo()
    try:
        a = await request_memoized("a", factory)
        b = await request_memoized("b", factory)
    finally:
        end_request_memo(token)

    assert {a, b} == {1, 2}
    assert counter.calls == 2


async def test_scopes_are_isolated():
    counter = Counter()

    async def factory():
        await asyncio.sleep(0)
        counter.bump()
        return counter.calls

    token = begin_request_memo()
    try:
        await request_memoized("k", factory)
        await request_memoized("k", factory)
    finally:
        end_request_memo(token)

    token = begin_request_memo()
    try:
        second_scope = await request_memoized("k", factory)
    finally:
        end_request_memo(token)

    assert counter.calls == 2
    assert second_scope == 2


async def test_concurrent_callers_share_task():
    counter = Counter()
    gate = asyncio.Event()

    async def factory():
        counter.bump()
        await gate.wait()
        return "shared"

    token = begin_request_memo()
    try:
        task_a = asyncio.create_task(request_memoized("k", factory))
        task_b = asyncio.create_task(request_memoized("k", factory))
        # Let both callers reach the memo lookup before releasing the factory.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        gate.set()
        results = await asyncio.gather(task_a, task_b)
    finally:
        end_request_memo(token)

    assert results == ["shared", "shared"]
    assert counter.calls == 1


async def test_exception_is_cached_within_scope():
    counter = Counter()

    class Boom(Exception):
        pass

    async def factory():
        await asyncio.sleep(0)
        counter.bump()
        raise Boom("nope")

    token = begin_request_memo()
    try:
        with pytest.raises(Boom):
            await request_memoized("k", factory)
        with pytest.raises(Boom):
            await request_memoized("k", factory)
    finally:
        end_request_memo(token)

    assert counter.calls == 1


def test_end_request_memo_restores_previous_value():
    outer_token = begin_request_memo()
    try:
        outer_memo = _memo.get()
        inner_token = begin_request_memo()
        try:
            assert _memo.get() is not outer_memo
        finally:
            end_request_memo(inner_token)
        assert _memo.get() is outer_memo
    finally:
        end_request_memo(outer_token)

    assert _memo.get() is None


def _run_extension(operation_type):
    """Drive the on_execute generator once and record whether the memo was set."""
    ext = RequestMemoExtension(execution_context=None)
    ctx = MagicMock(spec=ExecutionContext)
    ctx.operation_type = operation_type
    ext.execution_context = cast(ExecutionContext, ctx)
    observed = {}
    gen = ext.on_execute()
    next(gen)
    observed["memo_during_yield"] = _memo.get()
    try:
        next(gen)
    except StopIteration:
        pass
    observed["memo_after_yield"] = _memo.get()
    return observed


def test_extension_installs_memo_for_query():
    from strawberry.types.graphql import OperationType

    observed = _run_extension(OperationType.QUERY)

    assert observed["memo_during_yield"] == {}
    assert observed["memo_after_yield"] is None


def test_extension_installs_memo_for_mutation():
    from strawberry.types.graphql import OperationType

    observed = _run_extension(OperationType.MUTATION)

    assert observed["memo_during_yield"] == {}
    assert observed["memo_after_yield"] is None


def test_extension_skips_memo_for_subscription():
    from strawberry.types.graphql import OperationType

    observed = _run_extension(OperationType.SUBSCRIPTION)

    assert observed["memo_during_yield"] is None
    assert observed["memo_after_yield"] is None
