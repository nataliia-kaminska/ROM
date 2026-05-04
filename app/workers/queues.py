from rq import Queue

from app.core.redis import get_redis_connection


DEFAULT_QUEUE = "default"
INGESTION_QUEUE = "ingestion"
REMINDERS_QUEUE = "reminders"
EMBEDDINGS_QUEUE = "embeddings"
QUEUE_NAMES = [DEFAULT_QUEUE, INGESTION_QUEUE, REMINDERS_QUEUE, EMBEDDINGS_QUEUE]


def get_queue(name: str = DEFAULT_QUEUE) -> Queue:
    return Queue(name, connection=get_redis_connection())
