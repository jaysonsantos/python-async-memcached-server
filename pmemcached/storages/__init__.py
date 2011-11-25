from .memory import Storage as Memcached
STORAGES = {
    'memcached': Memcached
}


def getStorage(name=None):
    if name in STORAGES:
        return STORAGES[name]()

    return Memcached()
