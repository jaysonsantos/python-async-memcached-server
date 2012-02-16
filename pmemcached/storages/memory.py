from .base import BaseStorage


class Storage(BaseStorage):
    data = {}

    def expire_key(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        super(Storage, self).__setitem__(key, value)

    def __getitem__(self, key):
        return self.data[key]
