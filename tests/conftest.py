import shutil

import pytest

from tests.service.conftest import TEST_FILE_NAME, IMAGE_BYTES


@pytest.fixture(scope='session')
def images_dir(tmpdir_factory):
    image_dir = tmpdir_factory.mktemp('testdir')
    yield image_dir
    shutil.rmtree(str(image_dir))


@pytest.fixture(scope='module')
def image_in_dir(images_dir):
    image_file = images_dir.join(TEST_FILE_NAME)
    image_file.write('')
    with open(image_file, 'wb') as f:
        f.write(IMAGE_BYTES)
    yield str(images_dir)
