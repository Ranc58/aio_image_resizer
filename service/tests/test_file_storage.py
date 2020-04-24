import os

import funcy
import pytest

from service.file_storage import ImageNotFoundError, PathNotFoundError
from service.tests.conftest import IMAGE_BYTES


class MockMultipartReader:

    def __init__(self):
        self.image_b = list(funcy.chunks(10000, IMAGE_BYTES))

    async def read_chunk(self):
        if not self.image_b:
            return
        chunk = self.image_b[0]
        self.image_b = self.image_b[1:]
        return chunk


def test_get_image(local_storage):
    assert local_storage.get('test.png') == IMAGE_BYTES


def test_get_image_exception(local_storage, monkeypatch):
    full_image_path = "/test/"
    monkeypatch.setattr(local_storage, "images_path", full_image_path)
    with pytest.raises(ImageNotFoundError) as exc:
        local_storage.get('test.png')
    exception_msg = exc.value.args[0]
    excepted_msg = f"Not found {full_image_path}test.png"
    assert exception_msg == excepted_msg


def test_save_result_image(local_storage):
    image_name = "test.png"
    image = IMAGE_BYTES
    result_path = local_storage.save_result(image, image_name)
    assert os.path.exists(result_path)


def test_save_result_image_exception(local_storage, monkeypatch):
    image_name = "test.png"
    image = IMAGE_BYTES
    full_image_path = "/test/"
    monkeypatch.setattr(local_storage, "images_path", full_image_path)
    with pytest.raises(PathNotFoundError) as exc:
        local_storage.save_result(image, image_name)
    exception_msg = exc.value.args[0]
    excepted_msg = f"Not found {full_image_path}"
    assert exception_msg == excepted_msg


def test_delete_image(local_storage):
    image_name = "test.png"
    local_storage.delete_default(image_name)
    full_image_path = os.path.join(local_storage.images_path, image_name)
    assert not os.path.exists(full_image_path)


def test_delete_image_exception(local_storage):
    image_name = "test_not_exist.png"
    with pytest.raises(ImageNotFoundError) as exc:
        local_storage.delete_default(image_name)
    exception_msg = exc.value.args[0]
    excepted_msg = f"Not found {os.path.join(local_storage.images_path, image_name)}"
    assert exception_msg == excepted_msg


@pytest.mark.asyncio
async def test_save_default(local_storage, images_dir, mocker):
    file_name = 'default.png'
    full_path = os.path.join(images_dir, file_name)
    mocker.patch.object(os.path, "join", return_value=full_path)
    field = MockMultipartReader()
    await local_storage.save_default(file_name, field)
    assert os.path.exists(os.path.join(images_dir, file_name))


@pytest.mark.asyncio
async def test_delete_result(local_storage, images_dir):
    image_name = "new.png"
    image_file = images_dir.join(image_name)
    image_file.write('')
    await local_storage.delete_result(image_name)
    full_image_path = os.path.join(local_storage.images_path, image_name)
    assert not os.path.exists(full_image_path)

@pytest.mark.asyncio
async def test_delete_result_image_exception(local_storage):
    image_name = "test_not_exist.png"
    with pytest.raises(ImageNotFoundError) as exc:
        await local_storage.delete_result(image_name)
    exception_msg = exc.value.args[0]
    excepted_msg = f"Not found {os.path.join(local_storage.images_path, image_name)}"
    assert exception_msg == excepted_msg
