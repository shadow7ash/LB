from setuptools import setup, find_packages

setup(
    name="sa-leech-bot",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.0",
        "pymongo==3.12.1",
        "requests==2.31.0"
    ],
    entry_points={
        "console_scripts": [
            "start-bot=bot:main",
        ],
    },
)
