#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name="xbox-smartglass-nano",
    version="0.9.0",
    author="OpenXbox",
    description="The NANO part of the xbox smartglass library",
    long_description=open('README.rst').read() + '\n\n' + open('HISTORY.rst').read(),
    license="GPL",
    keywords="xbox one smartglass nano gamestreaming",
    url="https://github.com/OpenXbox/xbox-smartglass-nano-python",
    packages=[
        'xbox.nano',
        'xbox.nano.render',
        'xbox.nano.scripts',
        'xbox.nano.packet',
        'xbox.nano.factory',
        'xbox.nano.render.video',
        'xbox.nano.render.input',
        'xbox.nano.render.audio'
    ],
    namespace_packages=['xbox'],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],
    install_requires=[
        'xbox-smartglass-core>=1.0.10',
        'av==0.4.1',
        'PySDL2',
        'marshmallow-objects',
        'marshmallow-enum'
    ],
    tests_requires=[
        'pytest',
        'flake8',
        'tox'
    ],
    test_suite="tests",
    entry_points={
        'console_scripts': [
            'xbox-nano-client=xbox.nano.scripts.client:main',
            'xbox-nano-pcap=xbox.nano.scripts.pcap:main',
            'xbox-nano-replay=xbox.nano.scripts.replay:main'
        ]
    }
)
