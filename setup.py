from setuptools import setup, find_packages

setup(
    name="SA LEECH BOT",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.0",
        "pymongo==4.3.3",
        "requests==2.28.2"
    ],
    entry_points={
        "console_scripts": [
            "start-bot=bot:main",
        ],
    },
)
