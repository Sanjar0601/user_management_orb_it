from celery_app import celery_app
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from core.config import settings

logger = get_task_logger(__name__)


@celery_app.task
def delete_unverified_users():
    # NOTE: Using sync psycopg2 driver here instead of asyncpg
    # because Celery workers are synchronous and asyncpg conflicts
    # with Celery's event loop. In production with async Celery setup
    # this would use asyncpg properly.
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url)

    # NOTE: Currently 1 minute for testing. Change to timedelta(days=2) in production
    cutoff = datetime.utcnow() - timedelta(minutes=1)

    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM users WHERE is_verified = false AND created_at < :cutoff"),
            {"cutoff": cutoff}
        )
        conn.commit()
        logger.info(f"Deleted {result.rowcount} unverified users")

    engine.dispose()