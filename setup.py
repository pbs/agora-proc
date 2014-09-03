from setuptools import setup
from codecs import open
from os import path

import agora

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

requires = open('requirements.txt').read().split()

setup(
    name='agora',
    version=agora.__version__,
    description='Batch analyze video stream logs',
    long_description=long_description,
    url='https://github.com/pbs/agora-proc',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='agora mrjob mapreduce',
    install_requires=requires,
    packages=['agora'],
    entry_points={
        'console_scripts': [
            'agora=agora.jobs:main',
        ],
    },
)
