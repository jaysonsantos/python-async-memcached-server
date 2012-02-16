import datetime
from twisted.internet import reactor
from ..logger import log


class BaseStorage(object):
    callLater = reactor.callLater
    expires = {}

    # Implemented in backend
    def expire_key(self, key):
        pass

    def _expire_key(self, key):
        if datetime.datetime.now() < self.expires[key]:
            log.debug('Expiring key %s' % key)
            self.expire_key(key)

    def __setitem__(self, key, value):
        expire_time = datetime.datetime.now() + \
            datetime.timedelta(microseconds=value['expiry'] * 1000)
        log.debug('Key %s will expire in %s. Microseconds %d' % (key, expire_time,
            value['expiry']))
        self.expires[key] = expire_time
        self.callLater(value['expiry'] / 1000.0, self._expire_key, key)

