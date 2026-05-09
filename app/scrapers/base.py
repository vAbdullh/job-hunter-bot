from abc import ABC, abstractmethod


class BaseScraper(ABC):

    @abstractmethod
    def fetch(self, url: str):
        pass

    @abstractmethod
    def parse(self, raw_data):
        pass
