#!/usr/bin/env python
import os
from setuptools import setup, find_packages

version = '0.1.0a1'

here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='syntreenet',
    version=version,
    license='GPLv3',
    url='http://syntree.net/',
    author='Enrique Pérez Arnaud',
    author_email='enrique@cazalla.net',
    description='A library to develop production rule systems',
    classifiers=[ ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    zip_safe=True,
    include_package_data=True,
)
