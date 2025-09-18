from setuptools import setup, find_packages

setup(
    name='mc-cli',
    version='0.0.3',
    author='jhersbo',
    description='A simple CLI to manage a Minecraft Bedrock Server running in Docker.',
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