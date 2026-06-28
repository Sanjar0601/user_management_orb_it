from celery_app import celery_app
from celery.utils.log import get_task_logger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionLocal
from users.models import User
from datetime import datetime, timedelta
import asyncio

logger = get_task_logger(__name__)

# NOTE: Currently set to 1 minute for testing purposes.
# In production, change timedelta(minutes=1) to timedelta(days=2)
# to delete unverified users after 2 days as per business requirements.
# Also update beat_schedule interval from 60.0 to 3600.0 (every hour)

@celery_app.task
def delete_unverified_users():
    asyncio.run(_delete_unverified_users())


async def _delete_unverified_users():
    async with AsyncSessionLocal() as db:
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        result = await db.execute(
            select(User).where(
                User.is_verified == False,
                User.created_at < cutoff
            )
        )
        users = result.scalars().all()
        for user in users:
            await db.delete(user)
        await db.commit()
        logger.info(f"Deleted {len(users)} unverified users")



celery_app.conf.beat_schedule = {
    "delete-unverified-users-every-hour": {
        "task": "tasks.delete_unverified_users",
        # NOTE: Currently runs every 60 seconds for testing.
        # In production, change to 3600.0 to run every hour.
        "schedule": 60.0,  # every hour
    }
}