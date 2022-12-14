"""
Redis pool module for selfprivacy_api
"""
import redis
from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass
from os import environ

REDIS_SOCKET = "/run/redis-sp-api/redis.sock"


class RedisPool(metaclass=SingletonMetaclass):
    """
    Redis connection pool singleton.
    """

    def __init__(self):
        if "USE_REDIS_PORT" in environ.keys():
            self._pool = redis.ConnectionPool(
                host="127.0.0.1",
                port=int(environ["USE_REDIS_PORT"]),
                decode_responses=True,
            )

        else:
            self._pool = redis.ConnectionPool.from_url(
                f"unix://{REDIS_SOCKET}",
                decode_responses=True,
            )
        self._pubsub_connection = self.get_connection()

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
