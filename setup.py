#!/usr/bin/env python
from setuptools import setup, find_packages
import pkg_resources

version = '0.4.2'
author = 'David-Leon Pohl'
author_email = 'pohl@physik.uni-bonn.de'

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
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
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
        ]
    },
    platforms='any'
)

# FIXME: bad practice to put code into setup.py
# Add the online_monitor bdaq53 plugins
try:
    import online_monitor
    import os
    from online_monitor.utils import settings
    # Get the absoulte path of this package
    package_path = os.path.dirname(online_monitor.__file__)
    # Add online_monitor plugin folder to entity search paths
    settings.add_producer_sim_path(os.path.join(package_path, 'utils'))
    settings.add_converter_path(os.path.join(package_path, 'converter'))
    settings.add_receiver_path(os.path.join(package_path, 'receiver'))

    # Add example online_monitor plugins to entity search paths
    settings.add_producer_sim_path(os.path.join(package_path, 'examples', 'producer_sim'))
    settings.add_converter_path(os.path.join(package_path, 'examples', 'converter'))
    settings.add_receiver_path(os.path.join(package_path, 'examples', 'receiver'))
except (ImportError, pkg_resources.DistributionNotFound):
    pass
