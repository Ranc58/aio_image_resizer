from dataclasses import dataclass
from typing import Dict


@dataclass
class ImageData:
    id: str
    status: str
    default_image_path: str
    file_name: str
    width: int
    height: int
    scale: int
    updated_file_path: str = None

    def to_json(self) -> Dict:
        return self.__dict__
