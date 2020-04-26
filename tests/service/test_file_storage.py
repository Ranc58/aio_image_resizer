import os

import funcy
import pytest
from botocore.exceptions import EndpointConnectionError

from service.file_storage import ImageNotFoundError, PathNotFoundError, AmazonFileStorage, ConnectionStorageError
from tests.service.conftest import IMAGE_BYTES, TEST_FILE_NAME

AWS_TEST_FILE_NAME = f"AWS_{TEST_FILE_NAME}"

@pytest.fixture(scope='module')
def aws_image_in_dir(images_dir):
    image_file = images_dir.join(AWS_TEST_FILE_NAME)
    image_file.write('')
    with open(image_file, 'wb') as f:
        f.write(IMAGE_BYTES)
    yield str(images_dir)


@pytest.fixture(scope='module')
def aws_storage(images_dir, aws_image_in_dir):
    storage = AmazonFileStorage(
        images_path=images_dir,
    )
    return storage



class MockMultipartReader:

    def __init__(self):
        self.image_b = list(funcy.chunks(10000, IMAGE_BYTES))

    async def read_chunk(self):
        if not self.image_b:
            return
        chunk = self.image_b[0]
        self.image_b = self.image_b[1:]
        return chunk

    async def next(self):
        class Field:
            def __init__(self):
                self.filename = TEST_FILE_NAME

        return Field()

class SyncConn:

    def put_object(self, *args, **kwargs):
        pass

class AsyncConn:

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def delete_object(self, *args, **kwargs):
        pass

    async def get_object(self, *args, **kwargs):
        class Stream:

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def read(self):
                return IMAGE_BYTES

        return {"Body": Stream}


def mock_get_client(sync=False):

    if sync:
        return SyncConn()
    else:
        return AsyncConn()


class TestLocalFileStorage:

    def test_get_image(self, local_storage):
        assert local_storage.get_default('test.png') == IMAGE_BYTES

    def test_get_image_exception(self, local_storage, monkeypatch):
        full_image_path = "/test/"
        monkeypatch.setattr(local_storage, "images_path", full_image_path)
        with pytest.raises(ImageNotFoundError) as exc:
            local_storage.get_default('test.png')
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {full_image_path}test.png"
        assert exception_msg == excepted_msg

    def test_save_result_image(self, local_storage):
        image_name = "test.png"
        image = IMAGE_BYTES
        result_path = local_storage.save_result(image, image_name)
        assert os.path.exists(result_path)

    def test_save_result_image_exception(self, local_storage, monkeypatch):
        image_name = "test.png"
        image = IMAGE_BYTES
        full_image_path = "/test/"
        monkeypatch.setattr(local_storage, "images_path", full_image_path)
        with pytest.raises(PathNotFoundError) as exc:
            local_storage.save_result(image, image_name)
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {full_image_path}"
        assert exception_msg == excepted_msg

    def test_delete_image(self, local_storage):
        image_name = "test.png"
        local_storage.delete_default(image_name)
        full_image_path = os.path.join(local_storage.images_path, image_name)
        assert not os.path.exists(full_image_path)

    def test_delete_image_exception(self, local_storage):
        image_name = "test_not_exist.png"
        with pytest.raises(ImageNotFoundError) as exc:
            local_storage.delete_default(image_name)
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {os.path.join(local_storage.images_path, image_name)}"
        assert exception_msg == excepted_msg

    @pytest.mark.asyncio
    async def test_save_default(self, local_storage, images_dir, mocker):
        file_name = 'default.png'
        full_path = os.path.join(images_dir, file_name)
        mocker.patch.object(os.path, "join", return_value=full_path)
        field = MockMultipartReader()
        await local_storage.save_default(file_name, field)
        assert os.path.exists(os.path.join(images_dir, file_name))

    @pytest.mark.asyncio
    async def test_delete_result(self, local_storage, images_dir):
        image_name = "new.png"
        image_file = images_dir.join(image_name)
        image_file.write(b'')
        full_path = os.path.join(images_dir, image_name)
        await local_storage.delete_result(full_path)
        full_image_path = os.path.join(local_storage.images_path, image_name)
        assert not os.path.exists(full_image_path)

    @pytest.mark.asyncio
    async def test_delete_result_image_exception(self, local_storage):
        image_name = "test_not_exist.png"
        full_path = os.path.join(local_storage.images_path, image_name)
        with pytest.raises(ImageNotFoundError) as exc:
            await local_storage.delete_result(full_path)
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {full_path}"
        assert exception_msg == excepted_msg


class TestAmazonFileStorage:

    def test_get_image(self, aws_storage):
        assert aws_storage.get_default(AWS_TEST_FILE_NAME) == IMAGE_BYTES

    def test_get_image_exception(self, aws_storage, monkeypatch):
        full_image_path = "/test/"
        monkeypatch.setattr(aws_storage, "images_path", full_image_path)
        with pytest.raises(ImageNotFoundError) as exc:
            aws_storage.get_default('test.png')
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {full_image_path}test.png"
        assert exception_msg == excepted_msg

    def test_save_result_image(self, aws_storage, mocker):
        mocker.patch.object(AmazonFileStorage, '_get_client', return_value=mock_get_client(sync=True))
        image_name = "test.png"
        image = IMAGE_BYTES
        result_path = aws_storage.save_result(image, image_name)
        assert result_path == f"{aws_storage.folder}/resized_{image_name}"

    def test_save_result_image_exception_connection_storage_error(self, aws_storage, monkeypatch, mocker):
        image_name = "test.png"
        image = IMAGE_BYTES
        full_image_path = "/test/"
        mocker.patch.object(AmazonFileStorage, '_get_client', return_value=mock_get_client(sync=True))
        mocker.patch.object(SyncConn, 'put_object', side_effect=ConnectionError)
        monkeypatch.setattr(aws_storage, "images_path", full_image_path)
        with pytest.raises(ConnectionStorageError) as exc:
            aws_storage.save_result(image, image_name)
        exception_msg = exc.value.args[0]
        excepted_msg = f"Connection error for AWS: "
        assert exception_msg == excepted_msg

    def test_delete_image(self, aws_storage):
        image_name = AWS_TEST_FILE_NAME
        aws_storage.delete_default(image_name)
        full_image_path = os.path.join(aws_storage.images_path, image_name)
        assert not os.path.exists(full_image_path)

    def test_delete_image_exception(self, aws_storage):
        image_name = "test_not_exist.png"
        with pytest.raises(ImageNotFoundError) as exc:
            aws_storage.delete_default(image_name)
        exception_msg = exc.value.args[0]
        excepted_msg = f"Not found {os.path.join(aws_storage.images_path, image_name)}"
        assert exception_msg == excepted_msg

    @pytest.mark.asyncio
    async def test_save_default(self, aws_storage, images_dir, mocker):
        file_name = 'default.png'
        full_path = os.path.join(images_dir, file_name)
        mocker.patch.object(os.path, "join", return_value=full_path)
        field = MockMultipartReader()
        await aws_storage.save_default(file_name, field)
        assert os.path.exists(os.path.join(images_dir, file_name))

    @pytest.mark.asyncio
    async def test_delete_result(self, aws_storage, images_dir, mocker):
        mocker.patch.object(AmazonFileStorage, '_get_client', return_value=mock_get_client())
        image_name = "new.png"
        image_file = images_dir.join(image_name)
        image_file.write('')
        await aws_storage.delete_result(image_name)

    @pytest.mark.asyncio
    async def test_delete_result_image_exception(self, aws_storage, mocker):
        mocker.patch.object(AmazonFileStorage, '_get_client', return_value=mock_get_client())
        image_name = "test_not_exist.png"
        mocker.patch.object(AsyncConn, 'delete_object', side_effect=ConnectionError)
        with pytest.raises(ConnectionStorageError) as exc:
            await aws_storage.delete_result(image_name)
        exception_msg = exc.value.args[0]
        excepted_msg = "Connection error for AWS: "
        assert exception_msg == excepted_msg
