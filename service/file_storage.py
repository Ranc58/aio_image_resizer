import abc
import os


class FileStorage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get(self, image_name):
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, image, image_name):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, image_name):
        raise NotImplementedError


class LocalFileStorage(FileStorage):

    def __init__(self, images_path):
        self.images_path = images_path

    def get(self, image_name):
        with open(os.path.join(self.images_path, image_name), 'rb') as f:  # todo add errors handling
            image = f.read()
        return image

    def save(self, image, image_name):
        full_path = os.path.join(self.images_path, f'resized_{image_name}')
        with open(full_path, 'wb') as f:
            f.write(image)
        return full_path

    def delete(self, image_name):
        full_path = os.path.join(self.images_path, image_name)
        os.remove(full_path)
