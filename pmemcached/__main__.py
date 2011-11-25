from twisted.internet import protocol, reactor
from .server import MemcachedFactory
from .storages import getStorage

if __name__ == '__main__':
    reactor.listenTCP(11211, MemcachedFactory(getStorage('memory')))
    reactor.run()
