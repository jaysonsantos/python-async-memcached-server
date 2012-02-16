import datetime
from ..logger import log


class BaseStorage(object):
    expires = {}

    def __setitem__(self, key, value):
        expire_time = datetime.datetime.now() + \
            datetime.timedelta(microseconds=value['expiry'] * 1000)
        log.debug('Key %s will expire in %s. Microseconds %d' % (key, expire_time,
            value['expiry']))
        self.expires[key] = expire_time
