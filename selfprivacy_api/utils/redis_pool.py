"""
Redis pool module for selfprivacy_api
"""
import redis
import redis.asyncio as redis_async

from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass

REDIS_SOCKET = "/run/redis-sp-api/redis.sock"


# class RedisPool(metaclass=SingletonMetaclass):
class RedisPool:
    """
    Redis connection pool singleton.
    """

    def __init__(self):
        self._dbnumber = 0
        url = RedisPool.connection_url(dbnumber=self._dbnumber)
        # We need a normal sync pool because otherwise
        # our whole API will need to be async
        self._pool = redis.ConnectionPool.from_url(
            url,
            decode_responses=True,
        )
        # We need an async pool for pubsub
        self._async_pool = redis_async.ConnectionPool.from_url(
            url,
            decode_responses=True,
        )
        # TODO: inefficient, this is probably done each time we connect
        self.get_connection().config_set("notify-keyspace-events", "KEA")

    @staticmethod
    def connection_url(dbnumber: int) -> str:
        """
        redis://[[username]:[password]]@localhost:6379/0
        unix://[username@]/path/to/socket.sock?db=0[&password=password]
        """
        return f"unix://{REDIS_SOCKET}?db={dbnumber}"

    def get_connection(self):
        """
        Get a connection from the pool.
        """
        return redis.Redis(connection_pool=self._pool)

    def get_connection_async(self) -> redis_async.Redis:
        """
        Get an async connection from the pool.
        Async connections allow pubsub.
        """
        return redis_async.Redis(connection_pool=self._async_pool)

    async def subscribe_to_keys(self, pattern: str) -> redis_async.client.PubSub:
        async_redis = self.get_connection_async()
        pubsub = async_redis.pubsub()
        await pubsub.psubscribe(f"__keyspace@{self._dbnumber}__:" + pattern)
        return pubsub
