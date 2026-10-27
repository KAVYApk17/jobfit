"""Broker, queues, and dead-letter setup. Imported by both the API (to publish) and the worker."""

from celery import Celery
from celery.signals import worker_ready
from kombu import Exchange, Queue

from app.config import get_settings

settings = get_settings()

WORK_EXCHANGE = Exchange("jobfit", type="direct")
DEAD_LETTER_EXCHANGE = Exchange("jobfit.dlx", type="direct")
DEAD_LETTER_QUEUE = Queue("dead", DEAD_LETTER_EXCHANGE, routing_key="dead")


def _work_queue(name: str) -> Queue:
    # A rejected message (retries exhausted) is routed to the dead-letter queue for review.
    return Queue(
        name,
        WORK_EXCHANGE,
        routing_key=name,
        queue_arguments={"x-dead-letter-exchange": DEAD_LETTER_EXCHANGE.name, "x-dead-letter-routing-key": "dead"},
    )


celery_app = Celery("jobfit", broker=settings.broker_url, include=["worker.tasks"])
celery_app.conf.update(
    task_queues=[_work_queue("parse"), _work_queue("match"), _work_queue("eval")],
    task_default_queue="parse",
    task_routes={
        "jobfit.parse_*": {"queue": "parse"},
        "jobfit.run_analysis": {"queue": "match"},
        "jobfit.run_eval": {"queue": "eval"},
    },
    # Ack only after the result is saved, so a crashed worker returns the job to the queue.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
)


@worker_ready.connect
def declare_dead_letter_queue(**_) -> None:
    with celery_app.connection_for_write() as conn:
        DEAD_LETTER_QUEUE(conn.default_channel).declare()
