from twisted.internet import protocol, reactor
from .server import MemcachedFactory
from .storages import getStorage


def run_server():
    reactor.listenTCP(11211, MemcachedFactory(getStorage('memory')))
    reactor.run()
