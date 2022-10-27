"""
Singleton is a creational design pattern, which ensures that only
one object of its kind exists and provides a single point of access
to it for any other code.
"""
from threading import Lock


class SingletonMetaclass(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(SingletonMetaclass, cls).__call__(
                    *args, **kwargs
                )
        return cls._instances[cls]
