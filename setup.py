#!/usr/bin/env python
import os
from setuptools import setup, find_packages  # This setup relies on setuptools since distutils is insufficient and badly hacked code

version = '0.2.1'
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
    keywords=['online monitor', 'real time', 'plots'],
    entry_points={
        'console_scripts': [
            'online_monitor = online_monitor.OnlineMonitor:main',  # starts the online monitor application; blocking until app exit
            'start_converter = online_monitor.start_converter:main',  # starts the converters; blocking until CRTL-C
            'start_producer_sim = online_monitor.start_producer_sim:main',  # starts the producer simulatiion; blocking until CRTL-C
            'start_online_monitor = online_monitor.start_online_monitor:main',  # starts the online monitor application + covnerters + producer simulation defined on the configuration.yaml
        ]
    },
    platforms='any'
)

# Add the examples and the entity base classes to the online_monitor search paths
# To do that much logic in the setup.py is bad; better ideas welcome

import online_monitor
from  online_monitor.utils import settings
package_path = os.path.dirname(online_monitor.__file__)

# Add std. paths with the std. modules
settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/online_monitor/producer_sim')))
settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/online_monitor/converter')))
settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/online_monitor/receiver')))

# Add examples folder
settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/producer_sim')))
settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/converter')))
settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/receiver')))
