import io
import os

import pytest
from PIL import Image

from service import ImageResizer, LocalFileStorage
from service.file_storage import ImageNotFoundError, PathNotFoundError
from service.tests.conftest import TEST_FILE_NAME, IMAGE_BYTES


@pytest.fixture(scope='module')
def image_resizer(local_storage):
    resizer = ImageResizer(file_storage=local_storage)
    resizer.image_name = TEST_FILE_NAME
    return resizer


@pytest.fixture(scope='module')
def pillow_image():
    image = Image.open(io.BytesIO(IMAGE_BYTES))
    return image


def test__get_image(image_resizer, mocker):
    mocker.patch.object(LocalFileStorage, 'get', return_value=IMAGE_BYTES)
    result = image_resizer._get_image()
    assert result == Image.open(io.BytesIO(IMAGE_BYTES))


def test__get_image_exception(image_resizer, monkeypatch):
    monkeypatch.setattr(image_resizer, "image_name", "not_valid.png")
    with pytest.raises(ImageNotFoundError):
        image_resizer._get_image()


def test__save_image(image_resizer, images_dir, pillow_image):
    image_after_resize = pillow_image.resize((10, 10))
    resized_path = f"{images_dir}/resized_{TEST_FILE_NAME}"
    image_resizer._save_image(image_after_resize)
    assert os.path.exists(resized_path)


def test__save_image_exception(image_resizer, local_storage, pillow_image, monkeypatch):
    monkeypatch.setattr(local_storage, "images_path", "/test/")
    with pytest.raises(PathNotFoundError):
        image_resizer._save_image(pillow_image)


def test_delete_default_image(image_resizer, images_dir, monkeypatch):
    new_file_name = "new.png"
    new_file = images_dir.join(new_file_name)
    with open(new_file, 'wb') as f:
        f.write(IMAGE_BYTES)
    monkeypatch.setattr(image_resizer, "image_name", new_file_name)
    image_resizer._delete_default_image()
    assert not os.path.exists(os.path.join(images_dir, new_file_name))


def test_delete_default_image_exception_image_not_found(image_resizer, monkeypatch):
    new_file_name = "tra.png"
    monkeypatch.setattr(image_resizer, "image_name", new_file_name)
    with pytest.raises(ImageNotFoundError):
        image_resizer._delete_default_image()


def test_delete_default_image_exception_path_not_found(image_resizer,local_storage, monkeypatch):
    monkeypatch.setattr(local_storage, "images_path", "/test/")
    with pytest.raises(PathNotFoundError):
        image_resizer._delete_default_image()


def test_resize_image_width_height(image_resizer, monkeypatch, pillow_image):
    monkeypatch.setattr(image_resizer, "width", 4)
    monkeypatch.setattr(image_resizer, "height", 5)
    resized_image = image_resizer._resize_image(pillow_image)
    assert resized_image.width == 4
    assert resized_image.height == 5


def test_resize_image_width(image_resizer, monkeypatch, pillow_image):
    monkeypatch.setattr(image_resizer, "width", 2)
    resized_image = image_resizer._resize_image(pillow_image)
    assert resized_image.width == 2
    assert resized_image.height == 2


def test_resize_image_height(image_resizer, monkeypatch, pillow_image):
    monkeypatch.setattr(image_resizer, "height", 10)
    resized_image = image_resizer._resize_image(pillow_image)
    assert resized_image.width == 10
    assert resized_image.height == 10


def test_resize_image_scale(image_resizer, monkeypatch, pillow_image):
    monkeypatch.setattr(image_resizer, "scale", 2)
    resized_image = image_resizer._resize_image(pillow_image)
    assert resized_image.width == 27
    assert resized_image.height == 27


def test_resize_image(image_resizer, images_dir, mocker):
    mocker.patch.object(LocalFileStorage, 'get', return_value=IMAGE_BYTES)
    resized_path = f"{images_dir}/resized_{TEST_FILE_NAME}"
    result, err = image_resizer.resize_img(TEST_FILE_NAME, 10, None, None)
    assert not err
    assert os.path.exists(resized_path)


def test_resize_image_exception_default_image_not_found(image_resizer, local_storage):
    file_name = 'exc.png'
    result, err = image_resizer.resize_img(file_name, 10, None, None)
    assert not result
    assert err == f"Not found {os.path.join(local_storage.images_path, file_name)}"


def test_resize_image_exception_not_found_delete_not_found_save(image_resizer, pillow_image, local_storage, monkeypatch, mocker):
    mocker.patch.object(ImageResizer, '_get_image', return_value=pillow_image)
    monkeypatch.setattr(local_storage, "images_path", "/test/")
    result, err = image_resizer.resize_img(TEST_FILE_NAME, 10, None, None)
    assert not result
    assert err == f"Delete default img err: Not found /test/; Save new img err: Not found /test/"


def test_resize_image_exception_not_found_delete(image_resizer, pillow_image, images_dir, local_storage, monkeypatch, mocker):
    success_path = f"{images_dir}/resized_{TEST_FILE_NAME}"
    mocker.patch.object(ImageResizer, '_get_image', return_value=pillow_image)
    mocker.patch.object(ImageResizer, '_save_image', return_value=success_path)
    monkeypatch.setattr(local_storage, "images_path", "/test/")
    result, err = image_resizer.resize_img(TEST_FILE_NAME, 10, None, None)
    assert result == success_path
    assert err == f"Delete default img err: Not found /test/"

def test_resize_image_exception_not_found_save(image_resizer, pillow_image, images_dir, local_storage, monkeypatch, mocker):
    success_path = f"{images_dir}/resized_{TEST_FILE_NAME}"
    mocker.patch.object(ImageResizer, '_get_image', return_value=pillow_image)
    mocker.patch.object(ImageResizer, '_delete_default_image', return_value=None)
    monkeypatch.setattr(local_storage, "images_path", "/test/")
    result, err = image_resizer.resize_img(TEST_FILE_NAME, 10, None, None)
    assert not result
    assert err == f"Save new img err: Not found /test/"
