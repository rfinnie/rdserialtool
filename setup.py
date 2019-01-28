#!/usr/bin/env python3

import os
import sys
from setuptools import setup, find_packages

assert(sys.version_info > (3, 4))


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


__version__ = None
with open(os.path.join(os.path.dirname(__file__), 'rdum', '__init__.py')) as f:
    for line in f:
        if not line.startswith('__version__ = '):
            continue
        __version__ = eval(line.rsplit(None, 1)[-1])
        break


setup(
    name='rdumtool',
    description='RDTech UM24C/UM25C/UM34C Bluetooth interface tool',
    long_description=read('README'),
    version=__version__,
    license='GPLv2+',
    platforms=['Unix'],
    author='Ryan Finnie',
    author_email='ryan@finnie.org',
    url='https://github.com/rfinnie/rdumtool',
    download_url='https://github.com/rfinnie/rdumtool',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
    ],
    entry_points={
        'console_scripts': [
            'rdumtool = rdum.tool:main',
        ],
    },
    test_suite='tests',
)
