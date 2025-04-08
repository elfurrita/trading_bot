from setuptools import setup, find_packages

setup(
    name='trading_bot',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'ta-lib',
        'bayesian-optimization',
        'binance',
        'prometheus-client',
        'pytest',
        'dydx_v4_client',
    ],
    entry_points={
        'console_scripts': [
            'trading_bot=trading_bot.main:main',
        ],
    },
)
