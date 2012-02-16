import datetime
start = datetime.datetime.now()
import bmemcached

client = bmemcached.Client('127.0.0.1')

total = 0
for i in xrange(1, 100000):
    client.set('foo', i)
    total += client.get('foo')

end = datetime.datetime.now()

print 'Finished in %.2f seconds, total %d' % ((end - start).seconds, total)
