import io

from PIL import Image

from service.file_storage import ImageNotFoundError, PathNotFoundError


class ImageResizerError(BaseException):
    pass


class ImageResizer:

    def __init__(self, file_storage):
        self.file_storage = file_storage
        self.image_name = None
        self.width = None
        self.height = None
        self.scale = None

    def _get_image(self):
        try:
            image_data = self.file_storage.get(self.image_name)
        except ImageNotFoundError:
            raise
        image = Image.open(io.BytesIO(image_data))
        return image

    def _save_image(self, image):
        format_image = self.image_name.split('.')[-1:][0].upper()
        bytes_data = io.BytesIO()
        image.save(bytes_data, format=format_image)
        try:
            saved = self.file_storage.save_result(bytes_data.getvalue(), self.image_name)
        except PathNotFoundError:
            raise
        return saved

    def _delete_default_image(self):
        try:
            self.file_storage.delete_default(self.image_name)
        except (PathNotFoundError, ImageNotFoundError):
            raise

    def _resize_image(self, image):
        new_width = self.width
        new_height = self.height
        if self.width and self.height:
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
        error = None
        try:
            image_before_update = self._get_image()
        except ImageNotFoundError as e:
            return None, str(e)
        image_after_update = self._resize_image(image_before_update)
        try:
            self._delete_default_image()
        except (PathNotFoundError, ImageNotFoundError) as e:
            # not return because we can clear files later (by cron for example)
            error = f"Delete default img err: {e}"
        try:
            saved = self._save_image(image_after_update)
        except PathNotFoundError as e:
            if error:
                error = f"{error}; Save new img err: {e}"
            else:
                error = f"Save new img err: {e}"
            return None, str(error)
        return saved, error
