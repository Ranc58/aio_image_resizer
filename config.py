import os

CONFIG = {
    'redis': {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'password': os.environ.get('REDIS_PASSWORD', 'SetPass'),
        # in secs. If not timeout - stored indefinitely
        'timeout': os.environ.get('REDIS_TIMEOUT')
    },
    'file_storage_type': os.environ.get('STORAGE_TYPE', 'local'),
    "clear": os.environ.get("FILES_CLEAR", False),
    'amazon': {
        "bucket": os.environ.get('AWS_BUCKET'),
        "folder": os.environ.get("AWS_FOLDER"),
        "aws_access_key": os.environ.get('AWS_ACCESS_KEY'),
        "aws_secret_access": os.environ.get('AWS_SECRET_ACCESS'),
        "region": os.environ.get("AWS_REGION", 'eu-central-1'),
        "ssl": os.environ.get('AWS_SSL', False),
    },
    'host': os.environ.get('HOST', 'localhost'),
    'port': int(os.environ.get('PORT', 8080)),
    'files_path': os.environ.get('TEMP_FILES_PATH', os.getcwd()),
    'debug': os.environ.get('DEBUG')
}
