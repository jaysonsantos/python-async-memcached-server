from setuptools import setup

setup(
    name='python-async-memcached-server',
    version='0.0.1',
    author='Jayson Reis',
    author_email='santosdosreis@gmail.com',
    description='A binary protocol memcached server written with twisted.',
    url='https://github.com/jaysonsantos/python-async-memcached-server',
    packages=['pmemcached'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': ['pmemcached=pmemcached:run_server'],
    },
    install_requires=[
        'Twisted==16.1.1'
    ]
)
