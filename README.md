[![Build Status](https://secure.travis-ci.org/jaysonsantos/python-async-memcached-server.png?branch=master)](http://travis-ci.org/jaysonsantos/python-async-memcached-server)

# WHY?
For fun.
This is not intended to be used in production, however I'm focusing in using pypy to boost performance.
I'm planning to have some sort of storages and add a possibility to persist data.

## What is working?
- Get, set, add, replace and delete functions.
- Key expiration.
- Support for custom storages.

## Testing
```bash
trial tests.py
```

## Benchmarks
To execute benchmarks, you need to run the server with:
```
python -mpmemached
```

### PyPy 1.8
```
(pypy)jayson@jayson-ThinkPad-Edge:~/github/python-async-memcached-server (master) Python 2.7.2 (0e28b379d8b3, Feb 09 2012, 19:41:03) [PyPy 1.8.0 with GCC 4.4.3]
$ python benchmark.py 
Finished in 23.00 seconds, total 4999950000
```

### CPython 2.7.1
```
(dev)jayson@jayson-ThinkPad-Edge:~/github/python-async-memcached-server (master) Python 2.7.1+
$ python benchmark.py 
Finished in 45.00 seconds, total 4999950000
```

### Original memcached server
```
(dev)jayson@jayson-ThinkPad-Edge:~/github/python-async-memcached-server (master) Python 2.7.1+
$ python benchmark.py 
Finished in 19.00 seconds, total 4999950000
```