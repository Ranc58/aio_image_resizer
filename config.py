import os

CONFIG = {
    'redis': {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'password': os.environ.get('REDIS_PASSWORD', 'SetPass'),
    },
    'host': os.environ.get('HOST', 'localhost'),
    'port': int(os.environ.get('PORT', 8080)),
    'files_path': os.environ.get('TEMP_FILES_PATH', os.getcwd()),
    'debug': os.environ.get('DEBUG')
}
