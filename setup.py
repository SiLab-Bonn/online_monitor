#!/usr/bin/env python
from setuptools import setup, find_packages


version = '0.6.0'
author = 'David-Leon Pohl'
author_email = 'pohl@physik.uni-bonn.de'
maintainer = 'Pascal Wolf'
maintainer_email = 'wolf@physik.uni-bonn.de'

# Requirements for core functionality from requirements.txt
with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='online_monitor',
    version=version,
    description='A generic online monitor showing real-time plots from '
                'multiple independent data acquisition systems.',
    url='https://github.com/SiLab-Bonn/online_monitor',
    license='MIT License',
    long_description='',
    author=author,
    maintainer=maintainer,
    author_email=author_email,
    maintainer_email=maintainer_email,
    install_requires=install_requires,
    packages=find_packages(),
    # Accept all data files and directories matched by MANIFEST.in or found in
    # source control
    include_package_data=True,
    keywords=['online monitor', 'real time', 'plots'],
    entry_points={
        'console_scripts': [
            # starts the online monitor application; blocking until app exit
            'online_monitor = online_monitor.OnlineMonitor:main',
            # starts the converters; blocking until CRTL-C
            'start_converter = online_monitor.start_converter:main',
            # starts the producer simulatiion; blocking until CRTL-C
            'start_producer_sim = online_monitor.start_producer_sim:main',
            # starts the online monitor application + converters + producer
            # simulation defined on the configuration.yaml
            'start_online_monitor = online_monitor.start_online_monitor:main',
            # Helper function to clean up crashed instances
            'stop_online_monitor = online_monitor.stop_online_monitor:main',
            # Conveinience function to easially plugin online monitor 
            'plugin_online_monitor = online_monitor.plugin_online_monitor:main',
        ]
    },
    platforms='any'
)
