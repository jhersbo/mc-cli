from setuptools import setup, find_packages

setup(
    name='mc-cli',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'click',
        'loguru'
    ],
    entry_points='''
        [console_scripts]
        mc-cli=cli.cli:cli
    ''',
)