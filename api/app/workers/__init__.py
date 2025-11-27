import redis
from rq import Queue
from app.config import settings

# Redis connection
redis_conn = redis.from_url(settings.redis_url)

# RQ queues
scan_queue = Queue('scans', connection=redis_conn)
retrain_queue = Queue('retrain', connection=redis_conn)


def enqueue_scan_job(scan_id: int):
    """Enqueue a scan job for async processing."""
    from app.workers.scan_worker import process_scan
    job = scan_queue.enqueue(process_scan, scan_id)
    return job


def enqueue_retrain_job():
    """Enqueue a retrain job for async processing."""
    from app.workers.retrain_worker import retrain_model
    job = retrain_queue.enqueue(retrain_model, timeout='30m')
    return job
