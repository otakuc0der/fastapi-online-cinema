import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete

from config.celery_app import celery_app
from database import ActivationTokenModel, get_db_contextmanager

logger = logging.getLogger(__name__)
runner = asyncio.Runner()


async def _delete_expired_activation_tokens() -> None:
    checked_at = datetime.now(timezone.utc)

    async with get_db_contextmanager() as session:
        result = await session.execute(
            delete(ActivationTokenModel)
            .where(ActivationTokenModel.expires_at <= checked_at)
            .returning(
                ActivationTokenModel.id,
                ActivationTokenModel.user_id,
                ActivationTokenModel.expires_at,
            )
        )

        deleted_tokens = result.all()

        await session.commit()

    logger.info(
        "Activation token cleanup: deleted=%s, checked_at=%s",
        len(deleted_tokens),
        checked_at.isoformat(),
    )

    for token in deleted_tokens:
        logger.info(
            "Deleted activation token: id=%s, user_id=%s, expires_at=%s",
            token.id,
            token.user_id,
            token.expires_at.isoformat(),
        )


@celery_app.task(ignore_result=True)
def delete_expired_activation_tokens() -> None:
    runner.run(_delete_expired_activation_tokens())
