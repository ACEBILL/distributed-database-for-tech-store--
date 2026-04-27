from db import get_redis_connection


def get_cache(key):
    return get_redis_connection().get(key)


def set_cache(key, value, ttl=300):
    get_redis_connection().setex(key, ttl, value)
