from setuptools import setup, find_packages

setup(
    name='SA_Leech_Bot',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==20.0a6',
        'pymongo==3.11.4',
        'requests==2.25.1'
    ],
    entry_points={
        'console_scripts': [
            'bot = bot:main',
        ],
    },
)
