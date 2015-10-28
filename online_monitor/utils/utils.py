import logging
import argparse
import yaml
import json
import base64
import sys
import numpy as np
from importlib import import_module
from inspect import getmembers, isclass

try:  # installing blosc can be troublesome under windows
    import blosc
    has_blosc = True
except ImportError:
    has_blosc = False

from online_monitor.utils import settings


def parse_arguments():
    # Parse command line options
    args = parse_args(sys.argv[1:])
    return args


def parse_args(args):  # argparse a string, http://stackoverflow.com/questions/18160078/how-do-you-write-tests-for-the-argparse-portion-of-a-python-module
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', nargs='?', help='Configuration yaml file', default=None)
    parser.add_argument('--log', '-l', help='Logging level (e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL)', default='INFO')
    args_parsed = parser.parse_args(args)
    if not args_parsed.config_file:
        parser.error("You have to specify a configuration file")  # pragma: no cover, sysexit that coverage does not cover
    return args_parsed


def parse_config_file(config_file, expect_receiver=False):  # create config dict from yaml text file
    with open(config_file, 'r') as in_config_file:
        configuration = yaml.safe_load(in_config_file)
        if expect_receiver:
            try:
                configuration['receiver']
            except KeyError:
                logging.warning('No receiver specified, thus no data can be plotted. Change %s!', config_file)
        return configuration


def setup_logging(loglevel):  # set logging level of this module
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)


def _factory(importname, base_class_type, *args, **kargs):  # load module from string
    def is_base_class(item):
        return isclass(item) and item.__module__ == importname

    mod = import_module(importname)
    clsmembers = getmembers(mod, is_base_class)
    if not len(clsmembers):
        raise ValueError('Found no matching class in %s.' % importname)
    else:
        cls = clsmembers[0][1]
    return cls(*args, **kargs)


def load_producer_sim(importname, base_class_type, *args, **kargs):  # search under all producer simulation paths for module with the name importname; return first occurence
    for producer_sim_path in settings.get_producer_sim_path():
        producer_sim_path = producer_sim_path.replace(r'/', '.')
        try:
            return _factory(producer_sim_path + '.' + importname, base_class_type, *args, **kargs)
        except ImportError:  # module not found in actual path
            pass
    raise RuntimeError('Producer simulation %s in paths %s not found!', importname, settings.get_producer_sim_path())


def load_converter(importname, base_class_type, *args, **kargs):  # search under all converter paths for module with the name importname; return first occurence
    for converter_path in settings.get_converter_path():
        converter_path = converter_path.replace(r'/', '.')
        try:
            return _factory(converter_path + '.' + importname, base_class_type, *args, **kargs)
        except ImportError:  # module not found in actual path
            pass
    raise RuntimeError('Converter %s in paths %s not found!', importname, settings.get_converter_path())


def load_receiver(importname, base_class_type, *args, **kargs):  # search under all receiver paths for module with the name importname; return first occurence
    for receiver_path in settings.get_receiver_path():
        receiver_path = receiver_path.replace(r'/', '.')
        try:
            return _factory(receiver_path + '.' + importname, base_class_type, *args, **kargs)
        except ImportError:  # module not found in actual path
            pass
    raise RuntimeError('Receiver %s in paths %s not found!', importname, settings.get_receiver_path())


# from http://stackoverflow.com/questions/3488934/simplejson-and-numpy-array#
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
            if has_blosc:
                obj_data = blosc.compress(obj_data, typesize=8)
            data_b64 = base64.b64encode(obj_data)
            if sys.version_info >= (3, 0):  # http://stackoverflow.com/questions/24369666/typeerror-b1-is-not-json-serializable
                data_b64 = data_b64.decode('utf-8')
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        return json.JSONEncoder.default(self, obj)


def json_numpy_obj_hook(dct):
    """Decodes a previously encoded numpy ndarray with proper shape and dtype.
    And decompresses the data with blosc

    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        array = dct['__ndarray__']
        if sys.version_info >= (3, 0):  # http://stackoverflow.com/questions/24369666/typeerror-b1-is-not-json-serializable
            array = array.encode('utf-8')
        data = base64.b64decode(array)
        if has_blosc:
            data = blosc.decompress(data)
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])

    return dct
