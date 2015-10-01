import logging
import argparse
import yaml
from importlib import import_module
from inspect import getmembers, isclass


def parse_arguments():
    # Parse command line options
    parser = argparse.ArgumentParser(prog='PROG')
    parser.add_argument('config_file', nargs='?', help='Configuration yaml file', default=None)
#     parser.add_argument('--receive_address', '-r', help='Remote address of the sender', required=False)
#     parser.add_argument('--data_type', '-d', help='Data type (e.g. pybar_fei4)', required=False)
#     parser.add_argument('--send_address', '-s', help='Address to publish interpreted data', required=False)
    parser.add_argument('--log', '-l', help='Logging level (e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL)', default='INFO')
    args = parser.parse_args()

    if not args.config_file:
        parser.error("You have to specify a configuration file")

    return args


def parse_config_file(config_file):  # create config dict from yaml text file
    try:
        with open(config_file, 'r') as config_file:
            configuration = yaml.safe_load(config_file)
    except IOError:
        logging.error("Cannot open configuration file")
    return configuration


def setup_logging(loglevel):  # set logging level of this module
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)


def factory(importname, base_class_type, *args, **kargs):  # load module from string
        def is_base_class(item):
            return isclass(item) and item.__module__ == importname

        mod = import_module(importname)
        clsmembers = getmembers(mod, is_base_class)
        if not len(clsmembers):
            raise ValueError('Found no matching class in %s.' % importname)
        else:
            cls = clsmembers[0][1]
        return cls(*args, **kargs)
