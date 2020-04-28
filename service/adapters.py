import abc
from typing import Any, Optional


class AdapterBase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def read(self) -> Optional[Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def write(self, body: Any) -> Optional[Any]:
        raise NotImplementedError


class AiohttpAdapter(AdapterBase):
    # Todo think how to standardize this
    def __init__(self, request: Any = None, response: Any = None) -> None:
        self.request = request
        self.response = response

    async def read(self) -> Any:
        reader = await self.request.multipart()
        field = await reader.next()
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            yield chunk

    async def write(self, body: Any) -> None:
        await self.response.write(body)
