#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='ccp2qif',
    version='1.0',
    description='CCP export to QIF converter',
    author='Michel Albert',
    author_email='michel@albert.lu',
    url='http://github.com/exhuma/ccp2qif',
    license='MIT',
    install_requires=[
        'schwifty',
        'xlrd',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': {
            'ccp2qif=ccp2qif.core:climain'
        }
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ]
)
