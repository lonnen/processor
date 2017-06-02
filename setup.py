# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
module installation information
"""

import codecs
import os
from setuptools import setup

# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    # pylint: disable=W0611,C0411
    import multiprocessing
except ImportError:
    pass


def read(fname):
    """
    utility function to read and return file contents
    """
    fpath = os.path.join(os.path.dirname(__file__), fname)
    with codecs.open(fpath, 'r', 'utf8') as fhandle:
        return fhandle.read().strip()


def find_install_requires():
    """
    utility function to build a list of requirements from requirements.txt
    """
    return [x.strip().split()[0].strip() for x in
            read('requirements.txt').splitlines()
            if x.strip() and not x.startswith('#')]


setup(
    name="jansky",
    version="0.1.0",
    author="mozilla socorro team and friends",
    description="the socorro crash processor",
    long_description=read("README.md"),
    license="MPL-2",
    packages=[
        'jansky',
    ],
    install_requires=find_install_requires(),
    include_package_data=True,
    zip_safe=False,
    keywords='breakpad crash',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.5',
    ],
)
