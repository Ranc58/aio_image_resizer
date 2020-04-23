import os

import pytest

from service.tests.conftest import image_bytes


def test_get_image(local_storage):
    assert local_storage.get('test.png') == image_bytes


def test_save_result_image(local_storage):
    image_name = "test.png"
    image = image_bytes
    result_path = local_storage.save_result(image, image_name)
    assert os.path.exists(result_path)


@pytest.mark.asyncio
async def test_delete_image(local_storage):
    image_name = "test.png"
    await local_storage.delete("test.png")
    full_image_path = os.path.join(local_storage.images_path, image_name)
    assert not os.path.exists(full_image_path)
