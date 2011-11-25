import struct
from twisted.internet import protocol
from logger import log


class Memcached(protocol.Protocol):
    HEADER_STRUCT = ''.join([
        '!',  # big-endian
        'B',  # Magic
        'B',  # Command
        'H',  # Key length
        'B',  # Extras length
        'B',  # Data type
        'H',  # Status
        'L',  # Body length
        'L',  # Opaque
        'Q',  # CAS
    ])

    HEADER_SIZE = 24

    MAGIC = {
        'request': 0x80,
        'response': 0x81
    }

    # All structures will be appended to HEADER_STRUCT
    COMMANDS = {
        'get': {'command': 0x00, 'struct': '%ds'},
        'set': {'command': 0x01, 'struct': 'LL%ds%ds'},
        'add': {'command': 0x02, 'struct': 'LL%ds%ds'},
        'replace': {'command': 0x03, 'struct': 'LL%ds%ds'},
        'delete': {'command': 0x04, 'struct': '%ds'},
        'incr': {'command': 0x05, 'struct': 'QQL%ds'},
        'decr': {'command': 0x06, 'struct': 'QQL%ds'},
        'flush': {'command': 0x08, 'struct': 'I'},
        'auth_negotiation': {'command': 0x20},
        'auth_request': {'command': 0x21, 'struct': '%ds%ds'}
    }

    STATUSES = {
        'success': {'command': 0x00},
        'key_not_found': {'command': 0x01, 'message': 'Not found'},
        'key_exists': {'command': 0x02, 'message': ''},
        'value_too_large': {'command': 0x03, 'message': ''},
        'invalid_arguments': {'command': 0x04, 'message': 'Invalid arguments'},
        'item_not_stored': {'command': 0x05, 'message': ''},
        'non_numeric': {'command': 0x06, 'message': ''},
        'unknown_command': {'command': 0x81, 'message': 'Unknown command'},
        'out_of_memory': {'command': 0x82, 'message': ''},
    }

    def connectionMade(self):
        log.info('Yay one client!')

    def connectionLost(self, reason):
        log.info('Client disconnected. %s' % reason)

    def sendError(self, command, keyLength, extLength, statusCode, opaque,
        cas, body=None):
        body_length = 0
        if body:
            body_length = len(body)

        self.transport.write(struct.pack(self.HEADER, self.MAGIC['response'],
            self.command,
            keyLength,
            extLength,
            0x00,
            statusCode,
            body_length,
            opaque,
            cas))

    def handleHeader(self, header):
        if len(header) != self.HEADER_SIZE:
            log.debug('Invalid header')
            return False

    def handleData(self, data):
        header = self.handleHeader(data[:self.HEADER_SIZE])
        if header:
            pass

    def dataReceived(self, data):
        self.transport.write(self.handleData(data))


class MemcachedFactory(protocol.Factory):
    protocol = Memcached

    def buildProtocol(self, addr):
        return self.protocol()
