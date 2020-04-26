import abc
import os
from typing import Union

import aiobotocore
import botocore.session
from aiobotocore import AioSession
from aiofile import Writer, AIOFile, LineReader
from aiofiles.os import remove
from aiohttp import BodyPartReader
from aiohttp.web import StreamResponse
from botocore.client import BaseClient

from config import CONFIG


class ImageNotFoundError(BaseException):
    pass


class PathNotFoundError(BaseException):
    pass


class FileStorage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_default(self, image_name: str) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def save_result(self, image: bytearray, image_name: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_default(self, image_name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    # async because used in aiohttp handler
    async def save_default(self, filename: str, field: BodyPartReader) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    # async because used in aiohttp handler
    async def delete_result(self, file_path: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    # async because used in aiohttp handler
    async def write_result(self, file_path: str, response: StreamResponse) -> None:
        raise NotImplementedError


class LocalFileStorage(FileStorage):

    def __init__(self, images_path: str) -> None:
        self.images_path = images_path

    def get_default(self, image_name: str) -> bytes:
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        with open(full_path, 'rb') as f:
            image = f.read()
        return image

    def save_result(self, image: bytearray, image_name: str) -> str:
        if not os.path.exists(self.images_path,):
            raise PathNotFoundError(f"Not found {self.images_path}")
        full_path = os.path.join(self.images_path, f'resized_{image_name}')
        with open(full_path, 'wb') as f:
            f.write(image)
        return full_path

    def delete_default(self, image_name: str) -> None:
        if not os.path.exists(self.images_path):
            raise PathNotFoundError(f"Not found {self.images_path}")
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        os.remove(full_path)

    async def save_default(self, filename: str, field: BodyPartReader) -> None:
        async with AIOFile(os.path.join(self.images_path, filename), 'wb') as f:
            writer = Writer(f)
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                await writer(chunk)
            await f.fsync()

    async def delete_result(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise ImageNotFoundError(f"Not found {file_path}")
        await remove(file_path)

    async def write_result(self, file_path: str, response: StreamResponse) -> None:
        async with AIOFile(file_path, 'rb') as f:
            async for line in LineReader(f):
                await response.write(line)


class AmazonFileStorage(FileStorage):

    def __init__(self, images_path: str) -> None:
        self.images_path = images_path
        self.bucket = CONFIG['amazon'].get("bucket")
        self.folder = CONFIG['amazon'].get("folder")

    def _get_client(self, sync: bool = False) -> botocore.client:
        if sync:
            session = botocore.session.get_session()
        else:
            session = aiobotocore.get_session()
        client = session.create_client(
             service_name='s3',
             region_name=CONFIG['amazon'].get("region"),
             aws_secret_access_key=CONFIG['amazon'].get('aws_secret_access'),
             aws_access_key_id=CONFIG['amazon'].get('aws_access_key'),
             use_ssl=CONFIG['amazon'].get('ssl'),
        )
        return client

    def get_default(self, image_name: str) -> bytes:
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        with open(full_path, 'rb') as f:
            image = f.read()
        return image

    def save_result(self, image: bytes, image_name: str) -> str:
        key = f'{self.folder}/resized_{image_name}'
        client = self._get_client(sync=True)
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image,
        )
        return key

    def delete_default(self, image_name: str) -> None:
        if not os.path.exists(self.images_path):
            raise PathNotFoundError(f"Not found {self.images_path}")
        full_path = os.path.join(self.images_path, image_name)
        if not os.path.exists(full_path):
            raise ImageNotFoundError(f"Not found {full_path}")
        os.remove(full_path)

    async def save_default(self, filename: str, field: BodyPartReader) -> None:
        async with AIOFile(os.path.join(self.images_path, filename), 'wb') as f:
            writer = Writer(f)
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                await writer(chunk)
            await f.fsync()

    async def delete_result(self, file_path: str) -> None:
        async with self._get_client() as client:
            await client.delete_object(Bucket=self.bucket, Key=file_path)

    async def write_result(self, file_path: str, response: StreamResponse) -> None:
        key = file_path
        async with self._get_client() as client:
            response_aws = await client.get_object(Bucket=self.bucket, Key=key)
            async with response_aws['Body'] as stream:
                body = await stream.read()
                await response.write(body)
