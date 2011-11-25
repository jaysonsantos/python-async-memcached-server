from twisted.internet import protocol, reactor
from .server import MemcachedFactory

if __name__ == '__main__':
    reactor.listenTCP(11211, MemcachedFactory())
    reactor.run()
