import logging
import uuid
import datetime

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import json_response, StreamResponse
from aiohttp_apispec import request_schema

from serializer import ImageSchema
from models.Image import ImageData
from config import CONFIG
from service import AiohttpAdapter
from service.file_storage import ImageNotFoundError, ConnectionStorageError, PathNotFoundError

logger = logging.getLogger('app_logger')


@request_schema(ImageSchema(), locations=['query'])
async def load_image(request: Request) -> json_response:
    # todo think about validate file and fields
    reader = await request.multipart()
    file_name_field = await reader.next()
    file_name = await file_name_field.read()
    decoded_file_name = file_name.decode(encoding="UTF-8")
    adapter = AiohttpAdapter(request=request)
    current_timestamp = datetime.datetime.now().timestamp()
    filename = f'{current_timestamp}-{decoded_file_name}'
    await request.app.files_storage.save_default(filename, adapter)
    file_id = str(uuid.uuid4())[:13]
    file_data = ImageData(
        id=file_id,
        status='loaded',
        default_image_path=CONFIG['files_path'],
        file_name=filename,
        width=int(request.query.get('width', 0)),
        height=int(request.query.get('height', 0)),
        scale=int(request.query.get('scale', 0)),
    )
    await request.app.repository.insert(file_id, file_data.to_json())
    await request.app.input_images_queue.put(file_id)
    return web.json_response(data={"id": file_id, "status": "loaded"}, status=201)


async def check_status(request: Request) -> json_response:
    image_id = request.match_info.get('image_id')
    file_data = await request.app.repository.get(image_id)
    if not file_data:
        raise web.HTTPNotFound()
    data = {
        'id': file_data.get('id'),
        'status': file_data.get('status')
    }
    return web.json_response(data=data, status=200)


async def get_image(request: Request) -> StreamResponse:
    image_id = request.match_info.get('image_id')
    file_data = await request.app.repository.get(image_id)
    if not file_data:
        raise web.HTTPNotFound()
    if file_data.get('status') != 'done':
        data = {
            'id': file_data.get('id'),
            'status': file_data.get('status')
        }
        return web.json_response(data=data, status=200)
    response = web.StreamResponse()
    response.headers['Content-Disposition'] = f'attachment; filename="{file_data.get("file_name")}"'
    await response.prepare(request)
    file_path = file_data.get('updated_file_path')
    adapter = AiohttpAdapter(response=response)
    try:
        await request.app.files_storage.write_result(file_path, adapter)
    except (ConnectionStorageError, PathNotFoundError) as e:
        logger.error(e)
        response.force_close()
        return response
    response.force_close()
    if CONFIG.get('clear'):
        try:
            await request.app.files_storage.delete_result(file_path)
        except ImageNotFoundError as e:
            logger.error(e)
        await request.app.repository.delete(image_id)
    return response
