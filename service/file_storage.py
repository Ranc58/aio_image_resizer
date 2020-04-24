import abc
import os

from aiofile import Writer, AIOFile
from aiofiles.os import remove

from config import CONFIG


class ImageNotFoundError(BaseException):
    pass


class PathNotFoundError(BaseException):
    pass


class FileStorage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get(self, image_name):
        raise NotImplementedError

    @abc.abstractmethod
    def save_result(self, image, image_name):
        raise NotImplementedError

    @abc.abstractmethod
    # async because used in aiohttp handler
    async def save_default(self, filename, field):
        raise NotImplementedError

    @abc.abstractmethod
    # async because used in aiohttp handler
    async def delete(self, image_name):
        raise NotImplementedError


class LocalFileStorage(FileStorage):

    def __init__(self, images_path):
        self.images_path = images_path

    def get(self, image_name):
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        with open(full_path, 'rb') as f:
            image = f.read()
        return image

    def save_result(self, image, image_name):
        if not os.path.exists(self.images_path):
            raise PathNotFoundError(f"Not found {self.images_path}")
        full_path = os.path.join(self.images_path, f'resized_{image_name}')
        with open(full_path, 'wb') as f:
            f.write(image)
        return full_path

    async def save_default(self, filename, field):
        async with AIOFile(os.path.join(CONFIG['files_path'], filename), 'wb') as f:
            writer = Writer(f)
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                await writer(chunk)
            await f.fsync()

    async def delete(self, image_name):
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        await remove(full_path)
