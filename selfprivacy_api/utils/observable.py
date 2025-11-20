import asyncio

from typing import AsyncGenerator, Generic, TypeVar

T = TypeVar("T")


class Observable(Generic[T]):
    val: T
    listeners: list[asyncio.Queue[T]]

    def __init__(self, initial_value: T):
        self.val = initial_value
        self.listeners = []

    async def put(self, val):
        self.val = val
        for listener in self.listeners:
            await listener.put(val)

    def get(self):
        return self.val

    async def subscribe(self) -> AsyncGenerator[T, None]:
        queue = asyncio.Queue[T]()
        self.listeners.append(queue)

        yield self.val

        while True:
            try:
                yield await queue.get()
            finally:
                self.listeners.remove(queue)
                return
