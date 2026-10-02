from abc import ABC, abstractmethod


class ModelRuntime(ABC):

    @abstractmethod
    def detect_regions(self, image):
        pass

    @abstractmethod
    def recognize_line(self, image):
        pass

    @property
    @abstractmethod
    def model_version_id(self):
        pass