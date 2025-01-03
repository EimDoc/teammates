import logging
from typing import List

import redis.asyncio as redis
from pydantic import TypeAdapter
from redis import Redis

from src.models.models import QuestionnaireOut, Game

logger = logging.getLogger(__name__)

EXPIRATION_TIME = 3600


class RedisConnection:
    __con = None

    def __init__(self, init_data: dict):
        self.__init_data = init_data

    @staticmethod
    def __create_connection(redis_data: dict):
        try:
            RedisConnection.__con = redis.from_url(**redis_data)
        except Exception as e:
            logger.error("Can't connect to redis server", exc_info=e)

    @staticmethod
    async def get_connection(redis_data: dict) -> Redis:
        if not RedisConnection.__con:
            RedisConnection.__create_connection(redis_data)
        return RedisConnection.__con


class QuestionnairesCache:
    def __init__(self, init_data: dict):
        self.__con = None
        self.__init_data = init_data

    async def __create_connection(self):
        self.__con = await RedisConnection.get_connection(self.__init_data)

    async def set_questionnaires(self, user_id: int, game: Game, questionnaires: List[QuestionnaireOut]):
        if not self.__con:
            await self.__create_connection()

        try:
            logger.info("Adding questionnaires to cache for user %d", user_id)
            async with self.__con.pipeline() as connection:
                key = ':'.join([str(user_id), game.value])
                await connection.set(key, questionnaires).execute()
                await connection.expire(user_id, EXPIRATION_TIME).execute()
            logger.info("Done adding questionnaires to cache for user %d", user_id)
            return True
        except Exception as e:
            logger.error("Error while adding questionnaires to cache for user %d", user_id, exc_info=e)

    async def get_questionnaires(self, user_id: int, game: Game) -> List[QuestionnaireOut] | List[None]:
        if not self.__con:
            await self.__create_connection()

        try:
            logger.info("Getting questionnaires from cache for user %d and game '%s'", user_id, game.value)
            async with self.__con.pipeline() as connection:
                key = ':'.join([str(user_id), game.value])
                result = await connection.get(key).execute()

            if result[0] is not None:
                type_adapter = TypeAdapter(list[QuestionnaireOut])
                result = type_adapter.validate_json(result[0])
            logger.info("Done getting questionnaires from cache for user %d and game %s, total questionnaires: %d",
                        user_id, game.value, len(result))
            return result if len(result) > 0 else [None]
        except Exception as e:
            logger.error("Error while reading from cache", exc_info=e)
            return [None]
