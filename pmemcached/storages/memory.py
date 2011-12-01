from .base import BaseStorage


class Storage(BaseStorage):
    data = {}

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]
