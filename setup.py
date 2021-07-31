#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

setup(
    name="xbox-smartglass-nano",
    version="0.10.1",
    author="OpenXbox",
    author_email="noreply@openxbox.org",
    description="The NANO (v2) part of the xbox smartglass library",
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.md').read(),
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="xbox one smartglass nano gamestreaming xcloud",
    url="https://github.com/OpenXbox/xbox-smartglass-nano-python",
    python_requires=">=3.7",
    packages=find_namespace_packages(include=['xbox.*']),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    test_suite="tests",
    install_requires=[
        'xbox-smartglass-core==1.3.0',
        'av==8.0.3',
        'PySDL2==0.9.7'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-console-scripts', 'pytest-asyncio'],
    extras_require={
        "dev": [
            "pip",
            "bump2version",
            "wheel",
            "watchdog",
            "flake8",
            "coverage",
            "Sphinx",
            "sphinx_rtd_theme",
            "recommonmark",
            "twine",
            "pytest",
            "pytest-asyncio",
            "pytest-console-scripts",
            "pytest-runner",
        ],
    },
    entry_points={
        'console_scripts': [
            'xbox-nano-client=xbox.nano.scripts.client:main',
            'xbox-nano-pcap=xbox.nano.scripts.pcap:main',
            'xbox-nano-replay=xbox.nano.scripts.replay:main'
        ]
    }
)
