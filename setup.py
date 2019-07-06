#!/usr/bin/env python
import setuptools

version = '0.1.0a9'


with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='syntreenet',
    version=version,
    license='GPLv3',
    url='http://www.syntree.net/',
    author='Enrique Pérez Arnaud',
    author_email='enrique@cazalla.net',
    description='A library to develop scalable production rule systems',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'':'src'},
    include_package_data=True
)
