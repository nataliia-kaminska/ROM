import os

from rq import SimpleWorker, Worker

from app.core.logging import configure_logging
from app.core.redis import get_redis_connection
from app.workers.queues import QUEUE_NAMES


def main() -> None:
    configure_logging()
    connection = get_redis_connection()
    worker_class = SimpleWorker if os.name == "nt" else Worker
    worker = worker_class(QUEUE_NAMES, connection=connection)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
