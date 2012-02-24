import datetime
from twisted.internet import reactor
from ..logger import log


class BaseStorage(object):
    def __init__(self):
        self.expires = {}
        self.callLater = reactor.callLater

    # Implemented in backend
    def expire_key(self, key):
        pass  # pragma: no cover

    def _expire_key(self, key):
        log.msg('Expiring key %s' % key)
        self.expire_key(key)
        del self.expires[key]

    def _add_expiry_time(self, key, expiry):
        log.msg('Key %s will expire in %d microseconds' % (key, expiry))

        if key in self.expires:
            log.msg('Key %s already exists, cancelling its expiral' % key)
            self.expires[key].cancel()
            del self.expires[key]

        self.expires[key] = self.callLater(expiry/ 1000.0, self._expire_key, key)

    def __setitem__(self, key, value):
        self._add_expiry_time(key, value['expiry'])
