from abc import ABC, abstractmethod

class ImageHostProvider(ABC):
    @abstractmethod
    def upload(self, image_path):
        pass