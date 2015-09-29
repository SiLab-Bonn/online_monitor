import argparse
import logging
import yaml
import time

from importlib import import_module
from inspect import getmembers, isclass

from transceiver import Transceiver


class ConverterManager(object):
    def __init__(self, configuration, loglevel='INFO'):
        self._setup_logging(loglevel)
        logging.info("Initialize converter mananager with configuration %s", configuration)
        self.configuration = self._parse_config_file(configuration)

    def _setup_logging(self, loglevel):
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

    def _parse_config_file(self, config_file):  # create config dict from yaml text file
        try:
            with open(config_file, 'r') as config_file:
                configuration = yaml.safe_load(config_file)
        except IOError:
            logging.error("Cannot open configuration file")
        return configuration

    def _factory(self, importname, *args, **kargs):  # load module from string
        def is_base_class(item):
            return isclass(item) and issubclass(item, Transceiver) and item.__module__ == importname

        mod = import_module(importname)
        clsmembers = getmembers(mod, is_base_class)
        if not len(clsmembers):
            raise ValueError('Found no matching class in %s.' % importname)
        else:
            cls = clsmembers[0][1]
        return cls(*args, **kargs)

    def start(self):
        logging.info('Starting %d converters', len(self.configuration['converter']))
        converters = []
        for (_, converter_settings) in self.configuration['converter'].items():
            converter = self._factory('converter.%s' % converter_settings['data_type'], *(), **converter_settings)
            converter.start()
            converters.append(converter)
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logging.info('CRTL-C pressed, shutting down converters')
            for converter in converters:
                converter.shutdown()

        for converter in converters:
            converter.join()

