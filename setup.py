from setuptools import setup, find_packages

setup(
    name='SA LEECH BOT',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==20.0',
        'pymongo[srv]==4.0',
        'dnspython',
        'requests'
    ],
)
