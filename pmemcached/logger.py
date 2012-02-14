import logging
import sys

log = logging.getLogger('pmemcached')
handler = logging.StreamHandler()
log.addHandler(handler)
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
if '-v' in sys.argv:
    log.setLevel(logging.DEBUG)  #pragma: no cover
