import asyncio
import signal
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import suppress

from aiohttp import web


from config import CONFIG
from service.file_storage import LocalFileStorage
from service.image_resizer import ImageResizer
from service.repository import RedisRepository

from views import load_image, get_image, check_status


def register_signal_handler():
    signal.signal(signal.SIGINT, lambda _, __: None)


async def resize_task(app, file_id):
    loop = asyncio.get_event_loop()
    data = await app.repository.get(file_id)
    image_resizer = ImageResizer(app.files_storage)
    data.update({
        "status": "resizing"
    })
    await app.repository.update(file_id, data)
    loop.run_in_executor(
        app.process_pool,
        image_resizer.resize_img,
        data.get('file_name'), data.get('width'), data.get('height'), data.get('scale')
    )
    data.update({
        "status": "done",
        "updated_file_path": None
    })
    await app.repository.update(file_id, data)


async def input_queue_listener(app):
    print('listen input data..')
    while True:
        file_id = await app.input_images_queue.get()
        app.loop.create_task(resize_task(app, file_id))
        app.input_images_queue.task_done()


async def repository_process(app):
    repository = RedisRepository()
    await repository.connect()
    app.repository = repository
    print("Repository connected") # todo change everywhere to logging
    yield
    await app.repository.disconnect()
    print("Disconnected from repository")


async def files_storage_process(app):
    files_storage = LocalFileStorage(CONFIG['files_path'])
    app.files_storage = files_storage
    print("Files storage connected")
    yield
    print("Files storage disconnected")


async def queue_listener_process(app):
    input_images_queue = asyncio.Queue()
    app.input_images_queue = input_images_queue
    process_pool = ProcessPoolExecutor(
        initializer=register_signal_handler
    )
    loop = asyncio.get_event_loop()
    input_queue_listener_task = loop.create_task(
        input_queue_listener(app)
    )
    app.process_pool = process_pool
    print('Services started')
    yield

    input_queue_listener_task.cancel()
    app.process_pool.shutdown(wait=True)
    print('Services stopped')


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        app = web.Application()
        app.cleanup_ctx.append(repository_process)
        app.cleanup_ctx.append(files_storage_process)
        app.cleanup_ctx.append(queue_listener_process)
        app.add_routes([
            web.post('/', load_image),
            web.get('/{file_name}', get_image),
            web.get('/{file_name}/check', check_status),
        ])
        web.run_app(
            app,
            host=CONFIG.get('host'),
            port=CONFIG.get('port'),
        )
