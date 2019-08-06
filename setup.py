#!/usr/bin/env python
import setuptools

version = '1.0.0b5'

with open("requirements.txt", "r") as fh:
    install_requires = [x for x in fh.read().split('\n') if len(x) > 0]

with open("test_requirements.txt", "r") as fh:
    testing_extras = [x for x in fh.read().split('\n')
                      if len(x) > 0 and not x.startswith('-')]

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='syntreenet',
    version=version,
    license='GPLv3',
    url='http://www.syntree.net/',
    author='Enrique Pérez Arnaud',
    author_email='enrique@cazalla.net',
    description='A library to develop scalable production rule systems for any parsing expression grammar',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'':'src'},
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
    },
    include_package_data=True
)
