import asyncio
import os
import uuid

import pytest
from aiofile import AIOFile, LineReader
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware

from config import CONFIG
from service.file_storage import ImageNotFoundError
from tests.service.conftest import TEST_FILE_NAME, IMAGE_BYTES
from tests.service.test_file_storage import MockMultipartReader
from views import load_image, get_image, check_status


class MockFilesStorage:

    async def save_default(self, *args, **kwargs):
        pass

    async def get_result(self, file_path, response):
        async with AIOFile(file_path, 'rb') as f:
            async for line in LineReader(f):
                await response.write(line)

    async def delete_result(self, file_path):
        raise ImageNotFoundError(f"Not found {file_path}")


class MockRepo:

    async def insert(self, *args, **kwargs):
        pass

    async def get(self, image_id):
        return {
            'id': image_id,
            'status': "done"
        }

    async def delete(self, *args, **kwargs):
        pass


@pytest.fixture()
async def aio_client(test_client):
    app = web.Application()
    setup_aiohttp_apispec(app)
    app.files_storage = MockFilesStorage()
    app.repository = MockRepo()
    app.middlewares.append(validation_middleware)
    app.input_images_queue = asyncio.Queue()
    app.add_routes([
        web.post('/api/v1/image', load_image),
        web.get('/api/v1/image/{image_id}', get_image),
        web.get('/api/v1/image/{image_id}/check', check_status),
    ])
    client = await test_client(app)
    return client


async def test_load_image(aio_client, mocker):
    default_uuid = '01ec3385-47fa-4df8-b10f-86b6cfe6ecc5'
    url = "/api/v1/image"
    params = {'scale': 2}
    mocker.patch.object(uuid, "uuid4", return_value=default_uuid)
    mocker.patch.object(Request, "multipart", side_effect=MockMultipartReader)
    resp = await aio_client.post(url, params=params)
    resp_data = await resp.json()
    assert resp.status == 201
    assert resp_data == {'id': default_uuid[:13], 'status': 'loaded'}


async def test_load_empty(aio_client, mocker):
    default_uuid = '01ec3385-47fa-4df8-b10f-86b6cfe6ecc5'
    url = "/api/v1/image"
    mocker.patch.object(uuid, "uuid4", return_value=default_uuid)
    mocker.patch.object(Request, "multipart", side_effect=MockMultipartReader)
    resp = await aio_client.post(url)
    resp_data = await resp.json()
    assert resp.status == 422
    expected_data = {
        "error": [
            "Please select correct arguments combination: 1)scale 2)height 3)width 4)height and width"
        ]
    }
    assert resp_data == expected_data


async def test_load_error_params(aio_client, mocker):
    default_uuid = '01ec3385-47fa-4df8-b10f-86b6cfe6ecc5'
    url = "/api/v1/image"
    mocker.patch.object(uuid, "uuid4", return_value=default_uuid)
    mocker.patch.object(Request, "multipart", side_effect=MockMultipartReader)
    params = {
        "width": 2,
        "scale": 5,
    }
    resp = await aio_client.post(url, params=params)
    resp_data = await resp.json()
    assert resp.status == 422
    expected_data = {
        "error": [
            "Please select correct arguments combination: 1)scale 2)height 3)width 4)height and width"
        ]
    }
    assert resp_data == expected_data


async def test_check_status(aio_client):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}/check"
    resp = await aio_client.get(url)
    assert resp.status == 200
    resp_data = await resp.json()
    assert resp_data == {
        'id': image_id,
        'status': "done"
    }


async def test_check_status_not_found_id(aio_client, mocker):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}/check"
    mocker.patch.object(MockRepo, "get", return_value=None)
    resp = await aio_client.get(url)
    assert resp.status == 404


async def test_get_image_not_found(aio_client, mocker):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}"
    mocker.patch.object(MockRepo, "get", return_value=None)
    resp = await aio_client.get(url)
    assert resp.status == 404


async def test_get_image_not_done(aio_client, mocker):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}"
    status_data = {
        'id': image_id,
        'status': "loaded"
    }
    mocker.patch.object(MockRepo, "get", return_value=status_data)
    resp = await aio_client.get(url)
    resp_data = await resp.json()
    assert resp.status == 200
    assert resp_data == status_data


async def test_get_image(aio_client, image_in_dir, mocker):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}"
    status_data = {
        'id': image_id,
        'status': "done",
        'updated_file_path': os.path.join(image_in_dir, TEST_FILE_NAME),
        'file_name': TEST_FILE_NAME,
    }
    mocker.patch.object(MockRepo, "get", return_value=status_data)
    mocker.patch.object(MockFilesStorage, "delete_result", return_value=None)
    resp = await aio_client.get(url)
    buffer = b""
    async for data, _ in resp.content.iter_chunks():
        buffer += data
    assert resp.status == 200
    assert buffer == IMAGE_BYTES

async def test_get_image_delete_error(aio_client, image_in_dir, mocker, monkeypatch):
    image_id = "01ec3385-47"
    url = f"/api/v1/image/{image_id}"
    status_data = {
        'id': image_id,
        'status': "done",
        'updated_file_path': os.path.join(image_in_dir, TEST_FILE_NAME),
        'file_name': TEST_FILE_NAME,
    }
    monkeypatch.setitem(CONFIG, 'clear', True)
    mocker.patch.object(MockRepo, "get", return_value=status_data)
    resp = await aio_client.get(url)
    buffer = b""
    async for data, _ in resp.content.iter_chunks():
        buffer += data
    assert resp.status == 200
    assert buffer == IMAGE_BYTES
