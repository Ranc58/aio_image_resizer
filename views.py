import os
import uuid
import datetime

from aiofile import AIOFile, Writer, LineReader
from aiohttp import web

from Image import ImageData
from config import CONFIG


async def load_image(request):
    reader = await request.multipart()
    field = await reader.next()
    current_timestamp = datetime.datetime.now().timestamp()
    filename = f'{current_timestamp}-{field.filename}'
    async with AIOFile(os.path.join(CONFIG['files_path'], filename), 'wb') as f:
        writer = Writer(f)
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            await writer(chunk)
        await f.fsync()
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
    return web.json_response(data={"id": file_id, "status": "ok"}, status=201)


async def check_status(request):
    image_id = request.match_info.get('image_id')
    if not image_id:
        raise web.HTTPBadRequest
    file_data = await request.app.repository.get(image_id)
    if not file_data:
        raise web.HTTPNotFound()
    data = {
        'id': file_data.get('id'),
        'status': file_data.get('status')
    }
    return web.json_response(data=data, status=200)


async def get_image(request):
    image_id = request.match_info.get('image_id')
    if not image_id:
        raise web.HTTPBadRequest
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
    async with AIOFile(file_path, 'rb') as f:
        async for line in LineReader(f):
            await response.write(line)
    response.force_close()
    os.remove(file_path)
    await request.app.repository.delete(image_id)
    return response
