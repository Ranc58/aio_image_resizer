import abc
import asyncio
import json
import logging

import aioredis
from config import CONFIG

logger = logging.getLogger('app_logger')


class Repository(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def connect(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def disconnect(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    async def insert(self, key, data):
        raise NotImplementedError

    @abc.abstractmethod
    async def update(self, key, data):
        raise NotImplementedError

    @abc.abstractmethod
    async def is_exist(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, key):
        raise NotImplementedError


class RedisRepository(Repository):

    def __init__(self):
        self.pool = None
        self.save_timeout = CONFIG['redis'].get('timeout')

    async def connect(self):
        while not self.pool:
            try:
                self.pool = await aioredis.create_redis_pool(
                    f"redis://{CONFIG['redis']['host']}:{CONFIG['redis']['port']}",
                    password=CONFIG['redis']['password'],
                    db=0,
                )
            except OSError as e:
                logger.error(f'Error: {e}.\nTry repoolect in 2 sec ')
                await asyncio.sleep(2)

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def _convert_key(self, key: str) -> str:
        if isinstance(key, bytes):
            key = str(key, encoding='UTF-8')
        return key

    async def _convert_data(self, data, action_type='set'):
        if isinstance(data, dict) and action_type == 'set':
            return json.dumps(data)
        if isinstance(data, bytes) and action_type == 'get':
            return json.loads(str(data, encoding='UTF-8'))
        return data

    async def insert(self, key: str, data):
        key = await self._convert_key(key)
        prepared_data = await self._convert_data(data)
        result = await self.pool.set(key, prepared_data)
        if self.save_timeout:
            await self.pool.expire(key, 60 * self.save_timeout)
        return result

    async def update(self, key: str, data):
        result = await self.insert(key, data)
        return result

    async def get(self, key):
        key = await self._convert_key(key)
        data = await self.pool.get(key)
        prepared_data = await self._convert_data(
            data, action_type='get'
        )
        return prepared_data

    async def is_exist(self, key: str):
        key = await self._convert_key(key)
        result = await self.pool.exists(key)
        return result

    async def delete(self, key: str):
        key = await self._convert_key(key)
        result = await self.pool.delete(key)
        return result
