#!/usr/bin/env python
from setuptools import setup, find_packages  # This setup relies on setuptools since distutils is insufficient and badly hacked code

version = '0.0.1'
author = 'David-Leon Pohl'
author_email = 'pohl@physik.uni-bonn.de'

# requirements for core functionality from requirements.txt
with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='online_monitor',
    version=version,
    description='A generic online monitor showing real-time plots from multiple independent data acquisition systems.',
    url='https://github.com/SiLab-Bonn/online_monitor',
    license='MIT License',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,  # accept all data files and directories matched by MANIFEST.in or found in source control
    package_data={'': ['README.*', 'VERSION'], 'docs': ['*'], 'examples': ['*']},
    keywords=['online monitor', 'real time plots'],
    platforms='any'
)
