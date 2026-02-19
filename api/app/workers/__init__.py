"""Worker queue management — lazy-imports redis/rq to avoid hard dependency at startup."""
import logging

logger = logging.getLogger(__name__)

_redis_conn = None
_scan_queue = None
_retrain_queue = None


def _get_queues():
    """Lazily initialise Redis connection and RQ queues."""
    global _redis_conn, _scan_queue, _retrain_queue
    if _redis_conn is None:
        try:
            import redis
            from rq import Queue
            from app.config import settings
            _redis_conn = redis.from_url(settings.redis_url)
            _scan_queue = Queue('scans', connection=_redis_conn)
            _retrain_queue = Queue('retrain', connection=_redis_conn)
        except Exception as e:
            logger.warning("Redis/RQ not available: %s — async jobs will be skipped", e)
            return None, None
    return _scan_queue, _retrain_queue


def enqueue_scan_job(scan_id: int):
    """Enqueue a scan job for async processing."""
    scan_queue, _ = _get_queues()
    if scan_queue is None:
        logger.warning("Scan queue unavailable — skipping async enqueue for scan %d", scan_id)
        return None
    from app.workers.scan_worker import process_scan
    return scan_queue.enqueue(process_scan, scan_id)


def enqueue_retrain_job():
    """Enqueue a retrain job for async processing."""
    _, retrain_queue = _get_queues()
    if retrain_queue is None:
        logger.warning("Retrain queue unavailable — skipping async enqueue")
        return None
    from app.workers.retrain_worker import retrain_model
    return retrain_queue.enqueue(retrain_model, timeout='30m')
