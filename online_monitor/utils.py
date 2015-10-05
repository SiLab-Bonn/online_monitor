import logging
import argparse
import yaml
import blosc
import json
import base64
import numpy as np
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


def parse_config_file(config_file, expect_receiver=False):  # create config dict from yaml text file
    try:
        with open(config_file, 'r') as in_config_file:
            configuration = yaml.safe_load(in_config_file)
    except IOError:
        logging.error("Cannot open configuration file")
    if expect_receiver:
        try:
            if not configuration['receiver']:
                logging.warning('No receiver specified, thus no data can be plotted. Change %s!', config_file)
        except KeyError:
            logging.warning('No receiver specified, thus no data can be plotted. Change %s!', config_file)
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


#from http://stackoverflow.com/questions/3488934/simplejson-and-numpy-array#
class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict 
        holding dtype, shape and the data, base64 encoded and blosc compressed.
        """
        if isinstance(obj, np.ndarray):
            if obj.flags['C_CONTIGUOUS']:
                obj_data = obj.data
            else:
                cont_obj = np.ascontiguousarray(obj)
                assert(cont_obj.flags['C_CONTIGUOUS'])
                obj_data = cont_obj.data
            obj_data = blosc.compress(obj_data, typesize=8)
            data_b64 = base64.b64encode(obj_data)
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder(self, obj)


def json_numpy_obj_hook(dct):
    """Decodes a previously encoded numpy ndarray with proper shape and dtype.
    And decompresses the data with blosc

    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        data = blosc.decompress(data)
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])

    return dct
