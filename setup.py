from setuptools import setup

setup(
    name='your-bot-name',
    version='1.0',
    packages=[],
    install_requires=[
        'python-telegram-bot==14.2',
        'pymongo==4.0.1',
        'requests==2.26.0'
    ],
    entry_points={
        'console_scripts': []
    },
    python_requires='>=3.12.3',
)
