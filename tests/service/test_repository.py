import json

import pytest

from service import RedisRepository


class MockRedisConn:

    async def set(self, key, data):
        return 1

    async def get(self, key):
        return b'{"test":"1"}'

    async def expire(self, key, exp_val):
        pass

    async def exists(self, key):
        if key == 'exist':
            return True
        return False

    async def delete(self, key):
        return 1


@pytest.fixture(scope='module')
def redis_repo():
    repo = RedisRepository()
    repo.pool = MockRedisConn()
    return repo


@pytest.mark.asyncio
async def test__convert_key_str(redis_repo):
    key = "tra"
    assert await redis_repo._convert_key(key) == key


@pytest.mark.asyncio
async def test__convert_key_bytes(redis_repo):
    key = b"tra"
    assert await redis_repo._convert_key(key) == "tra"


@pytest.mark.asyncio
async def test__convert_key_int(redis_repo):
    key = 1
    assert await redis_repo._convert_key(key) == 1


@pytest.mark.asyncio
async def test__convert_data_set(redis_repo):
    data = {"test": "1"}
    result = await redis_repo._convert_data(data, action_type='set')
    assert result == json.dumps(data)


@pytest.mark.asyncio
async def test__convert_data_get(redis_repo):
    data = b'{"test": "1"}'
    result = await redis_repo._convert_data(data, action_type='get')
    assert result == {"test": "1"}


@pytest.mark.asyncio
async def test_insert(redis_repo, mocker):
    assert await redis_repo.insert("test", {"data": True}) == 1


@pytest.mark.asyncio
async def test_update(redis_repo):
    assert await redis_repo.update("test", {"data": True}) == 1


@pytest.mark.asyncio
async def test_get(redis_repo):
    assert await redis_repo.get("test") == {"test": "1"}


@pytest.mark.asyncio
async def test_is_exist(redis_repo):
    assert await redis_repo.is_exist("exist")


@pytest.mark.asyncio
async def test_delete(redis_repo):
    assert await redis_repo.delete("exist") == 1
