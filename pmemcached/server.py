from twisted.internet import protocol, reactor
from logger import log


class Memcached(protocol.Protocol):
    def connectionMade(self):
        log.info('Yay one client!')

    def connectionLost(self, reason):
        log.info('Client disconnected. %s' % reason)

    def dataReceived(self, data):
        self.transport.write(self.handleData(data))


class MemcachedFactory(protocol.Factory):
    protocol = Memcached


reactor.listenTCP(11211, MemcachedFactory())
reactor.run()
