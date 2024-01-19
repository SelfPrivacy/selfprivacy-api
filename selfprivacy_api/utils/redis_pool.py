"""
Redis pool module for selfprivacy_api
"""
from os import environ
import redis
from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass

REDIS_SOCKET = "/run/redis-sp-api/redis.sock"


class RedisPool(metaclass=SingletonMetaclass):
    """
    Redis connection pool singleton.
    """

    def __init__(self):
        self._pool = redis.ConnectionPool.from_url(
            RedisPool.connection_url(dbnumber=0),
            decode_responses=True,
        )
        self._pubsub_connection = self.get_connection()

    @staticmethod
    def connection_url(dbnumber: int) -> str:
        """
        redis://[[username]:[password]]@localhost:6379/0
        unix://[username@]/path/to/socket.sock?db=0[&password=password]
        """

        if "USE_REDIS_PORT" in environ:
            port = int(environ["USE_REDIS_PORT"])
            return f"redis://@127.0.0.1:{port}/{dbnumber}"
        else:
            return f"unix://{REDIS_SOCKET}?db={dbnumber}"

    def get_connection(self):
        """
        Get a connection from the pool.
        """
        return redis.Redis(connection_pool=self._pool)

    def get_pubsub(self):
        """
        Get a pubsub connection from the pool.
        """
        return self._pubsub_connection.pubsub()
