import io

from PIL import Image


class ImageResizer:

    def __init__(self, file_storage):
        self.file_storage = file_storage
        self.image_name = None
        self.width = None
        self.height = None
        self.scale = None

    def _get_image(self):
        image_data = self.file_storage.get(self.image_name)
        image = Image.open(io.BytesIO(image_data))
        return image

    def _save_image(self, image):
        format = self.image_name.split('.')[-1:][0].upper()
        bytes_data = io.BytesIO()
        image.save(bytes_data, format=format)
        saved = self.file_storage.save(bytes_data.getvalue(), self.image_name)
        return saved

    def _delete_default_image(self):
        self.file_storage.delete(self.image_name)

    def _resize_image(self, image):
        new_width = self.width
        new_height = self.height
        if ((self.width and self.scale) or
                (self.height and self.scale)):
            return print('Please enter availiable arguments combination!')  # todo move to validator
        elif self.width and self.height:
            return image.resize((new_width, new_height))
        elif self.width:
            new_height = int(image.size[1] / (image.size[0] / self.width))
        elif self.height:
            new_width = int(image.size[0] / (image.size[1] / self.height))
        elif self.scale:
            new_width = int(image.size[0] / self.scale)
            new_height = int(image.size[1] / self.scale)
        return image.resize((new_width, new_height))

    def resize_img(self, image_name, width, height, scale):
        self.image_name, self.width, self.height, self.scale = image_name, width, height, scale
        image_before_update = self._get_image()
        image_after_update = self._resize_image(image_before_update)
        self._delete_default_image()
        saved = self._save_image(image_after_update)
        return saved

