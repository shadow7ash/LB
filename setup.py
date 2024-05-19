from setuptools import setup, find_packages

setup(
    name='SA Leech Bot',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==13.12',
        'pymongo==3.12.1',
        'requests==2.25.1'
    ],
)
