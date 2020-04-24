import asyncio
import logging
import signal
import time
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import suppress

from aiohttp import web
from aiohttp_apispec import validation_middleware, setup_aiohttp_apispec

from config import CONFIG
from service import LocalFileStorage, ImageResizer, RedisRepository
from views import load_image, get_image, check_status, tra

logger = logging.getLogger('app_logger')


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
    start_time = time.time()
    start_time_formatted = time.strftime("%H:%M:%S", time.localtime(start_time))

    new_image_path, error = await loop.run_in_executor(
        app.process_pool,
        image_resizer.resize_img,
        data.get('file_name'), data.get('width'), data.get('height'), data.get('scale')
    )
    if error:
        logger.error(f"{error}")
        if not new_image_path:
            data.update({
                "status": "error",
                "updated_file_path": None,
            })
    if new_image_path:
        end_time = time.time()
        end_time_formatted = time.strftime("%H:%M:%S", time.localtime(end_time))
        logger.debug(
            f'Start time: {start_time_formatted} End time: {end_time_formatted} Elapsed: {end_time-start_time}')
        data.update({
            "status": "done",
            "updated_file_path": new_image_path
        })
    await app.repository.update(file_id, data)


async def input_queue_listener(app):
    logger.debug('listen input data..')
    loop = asyncio.get_event_loop()
    while True:
        file_id = await app.input_images_queue.get()
        loop.create_task(resize_task(app, file_id))
        app.input_images_queue.task_done()


async def repository_process(app):
    repository = RedisRepository()
    await repository.connect()
    app.repository = repository
    logger.info("Repository started")
    yield
    await app.repository.disconnect()
    logger.info("Repository stopped")


async def files_storage_process(app):
    files_storage = LocalFileStorage(CONFIG['files_path'])
    app.files_storage = files_storage
    logger.info("Files storage started")
    yield
    logger.info("Files storage stopped")


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
    logger.info('Services started')
    yield
    input_queue_listener_task.cancel()
    app.process_pool.shutdown(wait=True)
    logger.info('Services stopped')


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        if CONFIG.get('debug'):
            logger.setLevel(logging.DEBUG)
        app = web.Application()
        app.cleanup_ctx.append(repository_process)
        app.cleanup_ctx.append(files_storage_process)
        app.cleanup_ctx.append(queue_listener_process)
        setup_aiohttp_apispec(app)
        app.middlewares.append(validation_middleware)
        app.add_routes([
            web.post('/api/v1/image', load_image),
            web.get('/api/v1/image/{image_id}', get_image),
            web.get('/api/v1/image/{image_id}/check', check_status),
        ])
        web.run_app(
            app,
            host=CONFIG.get('host'),
            port=CONFIG.get('port'),
        )
