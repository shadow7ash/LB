from setuptools import setup, find_packages

setup(
    name='telegram-leech-bot',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==20.0',
        'pymongo[srv]==4.0',
        'dnspython',
        'requests'
        
    ],
    entry_points={
        'console_scripts': [
            'telegram-leech-bot=bot:main'
        ],
    },
    description='A Telegram bot for downloading files via direct links.',
    author='Your Name',
    author_email='your_email@example.com',
    url='https://github.com/yourusername/telegram-leech-bot',
)
