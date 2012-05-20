import struct
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import task
from pmemcached.storages.memory import Storage
from pmemcached.storages import getStorage
from pmemcached.storages.memory import Storage as MemoryStorage
from pmemcached.server import MemcachedFactory


class ServerTests(unittest.TestCase):
    HEADER_STRUCT = '!BBHBBHLLQ'
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
        'stat': {'command': 0x10},
        'auth_negotiation': {'command': 0x20},
        'auth_request': {'command': 0x21, 'struct': '%ds%ds'}
    }

    STATUS = {
        'success': 0x00,
        'key_not_found': 0x01,
        'key_exists': 0x02,
        'auth_error': 0x08,
        'unknown_command': 0x81
    }

    FLAGS = {
        'pickle': 1 << 0,
        'integer': 1 << 1,
        'long': 1 << 2,
        'compressed': 1 << 3
    }

    def setUp(self):
        self.storage = Storage()
        factory = MemcachedFactory(self.storage)
        self.protocol = factory.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()

        self.clock = task.Clock()
        self.storage.callLater = self.clock.callLater

        self.protocol.makeConnection(self.tr)

    def tearDown(self):
        self.protocol.transport.loseConnection()

    def testGetInvalidKey(self):
        key = 'foobarbazdoesnotexist'
        expected = '\x81\x00\x00\x15\x00\x00\x00\x01\x00\x00\x00\t\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Not found'

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected)

    def testGet(self):
        key = 'foo'
        value = 'bar'
        expected = '\x81\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'+ \
            '\x81\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00bar'

        flags = 0
        time = 1000
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected)

    def testGetExpiredKey(self):
        key = 'foo'
        value = 'bar'
        expected = '\x81\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'+ \
            '\x81\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00bar'
        expected_not_found = '\x81\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00\t' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Not found'

        flags = 0
        time = 1000

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected)
        self.clock.advance(1)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))
        self.assertEqual(self.tr.value(), expected_not_found)

    def testOverwritedExpireTime(self):
        """
        This will test if storage wont create 2 callLaters for the same key. It have to
        aways delete old one if it is not expired and create a new one.
        """
        key = 'foo'
        value = 'bar'
        expected = '\x81\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'+ \
            '\x81\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00bar'
        expected_not_found = '\x81\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00\t' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Not found'

        flags = 0
        time = 1000

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected)

        time = 1500

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.clock.advance(1)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))
        self.assertEqual(self.tr.value(), '\x81\x00\x00\x00\x04\x00\x00\x00\x00' + \
            '\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00' + \
            '\x00\x00\x00bar')

        # Can't have more than one because the backend should overwrite the first
        # one
        self.assertEqual(len(self.clock.calls), 1)
        self.assertEqual(self.clock.calls[0].getTime(), 1.5)

    def testSet(self):
        key = 'foo'
        value = 'bar'
        expected = '\x81\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        flags = 0
        time = 1000
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.assertEqual(self.tr.value(), expected)

    def testAdd(self):
        key = 'foo'
        value = 'bar'
        expected_add_success = '\x81\x02\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_add_fail ='\x81\x02\x00\x00\x00\x00\x00\x02\x00\x00\x00\x14' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Data exists for key.'

        flags = 0
        time = 1000
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['add']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['add']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.assertEqual(self.tr.value(), expected_add_success)

        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['add']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['add']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.assertEqual(self.tr.value(), expected_add_fail)

    def testReplace(self):
        key = 'foo'
        value = 'bar'
        expected_replace = '\x81\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_get = '\x81\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x07' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00baz'

        flags = 0
        time = 1000
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))
        self.tr.clear()

        value = 'baz'
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['replace']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['replace']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))
        self.assertEqual(self.tr.value(), expected_replace)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected_get)

    def testReplaceInvalidKey(self):
        key = 'foo'
        value = 'bar'
        expected = '\x81\x03\x00\x00\x00\x00\x00\x01\x00\x00\x00\t\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Not found'

        flags = 0
        time = 1000

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['replace']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['replace']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.assertEqual(self.tr.value(), expected)

    def testDelete(self):
        key = 'foo'
        value = 'bar'
        expected_set = '\x81\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_delete = '\x81\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected_delete_fail = '\x81\x04\x00\x00\x00\x00\x00\x01\x00\x00\x00\t' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Not found'
        expected_get_should_not_exists = '\x81\x00\x00\x03\x00\x00\x00\x01' + \
            '\x00\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
            'Not found'

        flags = 0
        time = 1000
        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['set']['struct'] % (len(key), len(value)),
            self.MAGIC['request'],
            self.COMMANDS['set']['command'],
            len(key),
            8, 0, 0, len(key) + len(value) + 8, 0, 0, flags, time, key, value))

        self.assertEqual(self.tr.value(), expected_set)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['delete']['struct'] % len(key),
            self.MAGIC['request'],
            self.COMMANDS['delete']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected_delete)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['delete']['struct'] % len(key),
            self.MAGIC['request'],
            self.COMMANDS['delete']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected_delete_fail)
        self.tr.clear()

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            self.COMMANDS['get']['command'],
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected_get_should_not_exists)

    def testUnknownCommand(self):
        key = 'foo'
        expected = '\x81\x91\x00\x00\x00\x00\x00\x81\x00\x00\x00\x0F\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Unknown command'

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['get']['struct'] % (len(key)),
            self.MAGIC['request'],
            0x91,
            len(key), 0, 0, 0, len(key), 0, 0, key))

        self.assertEqual(self.tr.value(), expected)

    def testInvalidHeader(self):
        self.protocol.dataReceived('foobar')

        self.assertEqual(self.tr.value(), '')


    def testInvalidMagicCode(self):
        self.protocol.dataReceived(
            '\x82\x91\x00\x00\x00\x00\x00\x81\x00\x00\x00\x0F\x00\x00' + \
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(self.tr.value(), '')

    def testIncrement(self):
        key = 'foo'
        value = 1

        raise unittest.SkipTest("Skipping increment for now")

        self.protocol.dataReceived(struct.pack(self.HEADER_STRUCT + \
            self.COMMANDS['incr']['struct'] % len(key),
            self.MAGIC['request'],
            self.COMMANDS['incr']['command'],
            len(key),
            20, 0, 0, len(key) + 20, 0, 0, value, 0, 1000, key))

        self.assertEqual(1, self.tr.value())


class BaseTests(unittest.TestCase):
    def testGetValidStorage(self):
        self.assertTrue(isinstance(getStorage('memcached'), MemoryStorage))

    def testGetInvalidValidStorage(self):
        self.assertTrue(isinstance(getStorage('foo'), MemoryStorage))
