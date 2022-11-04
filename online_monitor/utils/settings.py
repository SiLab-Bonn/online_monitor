import ast
import sys
import os
import configparser


_file_name = os.path.dirname(sys.modules[__name__].__file__) + r'/../OnlineMonitor.ini'


def check_package_initialized():
    config = configparser.ConfigParser()
    config.read(_file_name)
    initialized = False
    try:
        initialized = ast.literal_eval(config.get('OnlineMonitor', 'initialized'))
    except configparser.NoSectionError:
        config.add_section('OnlineMonitor')
        config.set('OnlineMonitor', 'initialized', str(False))
        with open(_file_name, 'w') as f:
            config.write(f)
    
    if not initialized:
        initialize_monitor()


def initialize_monitor():

    ini_path = os.path.dirname(_file_name)
    generate_abspath = lambda *keys: os.path.abspath(os.path.join(ini_path, *keys))

    # Add online_monitor plugin folder to entity search paths
    add_producer_sim_path(generate_abspath('utils'))
    add_converter_path(generate_abspath('converter'))
    add_receiver_path(generate_abspath('receiver'))

    # Add example online_monitor plugins to entity search paths
    add_producer_sim_path(generate_abspath('examples', 'producer_sim'))
    add_converter_path(generate_abspath('examples', 'converter'))
    add_receiver_path(generate_abspath('examples', 'receiver'))

    config = configparser.ConfigParser()
    config.read(_file_name)
    config.set('OnlineMonitor', 'initialized', str(True))
    with open(_file_name, 'w') as f:
        config.write(f)
    

def add_converter_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    try:
        paths = get_converter_path()
    except configparser.NoOptionError:
        config.set('converter', 'path', str([path])[1:-1])  # On first call the path section does not exist
        with open(_file_name, 'w') as f:
            config.write(f)
            return
    paths.append(path)  # append actual path
    paths = list(set(paths))  # remove duplicates
    config.set('converter', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def add_receiver_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    try:
        paths = get_receiver_path()
    except configparser.NoOptionError:
        config.set('receiver', 'path', str([path])[1:-1])  # On first call the path section does not exist
        with open(_file_name, 'w') as f:
            config.write(f)
            return
    paths.append(path)  # append actual path
    paths = list(set(paths))  # remove duplicates
    config.set('receiver', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def add_producer_sim_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    try:
        paths = get_producer_sim_path()
    except configparser.NoOptionError:
        config.set('producer_sim', 'path', str([path])[1:-1])  # On first call the path section does not exist
        with open(_file_name, 'w') as f:
            config.write(f)
            return
    paths.append(path)  # append actual path
    paths = list(set(paths))  # remove duplicates
    config.set('producer_sim', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def delete_converter_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    paths = [p for p in get_converter_path() if p != path]
    config.set('converter', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def delete_receiver_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    paths = [p for p in get_receiver_path() if p != path]
    config.set('receiver', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def delete_producer_sim_path(path):  # path where to search for converter modules
    config = configparser.ConfigParser()
    config.read(_file_name)
    paths = [p for p in get_producer_sim_path() if p != path]
    config.set('producer_sim', 'path', str(paths)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def get_converter_path():
    config = configparser.ConfigParser()
    config.read(_file_name)  # WARNING: configparser.NoSectionError: can mean no file at all!
    path = ast.literal_eval(config.get('converter', 'path'))
    if isinstance(path, tuple):
        return [p for p in path]
    return [path]


def get_receiver_path():
    config = configparser.ConfigParser()
    config.read(_file_name)  # WARNING: configparser.NoSectionError: can mean no file at all!
    path = ast.literal_eval(config.get('receiver', 'path'))
    if isinstance(path, tuple):
        return [p for p in path]
    return [path]


def get_producer_sim_path():
    config = configparser.ConfigParser()
    config.read(_file_name)  # WARNING: configparser.NoSectionError: can mean no file at all!
    path = ast.literal_eval(config.get('producer_sim', 'path'))
    if isinstance(path, tuple):
        return [p for p in path]
    return [path]


def set_window_geometry(geometry):
    config = configparser.ConfigParser()
    config.read(_file_name)
    try:
        config.add_section('OnlineMonitor')
    except configparser.DuplicateSectionError:  # already existing
        pass
    config.set('OnlineMonitor', 'geometry', str(geometry)[1:-1])  # store new string representation
    with open(_file_name, 'w') as f:
        config.write(f)


def get_window_geometry():
    config = configparser.ConfigParser()
    config.read(_file_name)
    try:
        return ast.literal_eval(config.get('OnlineMonitor', 'geometry'))
    except configparser.NoOptionError:
        return (100, 100, 1024, 768)  # std. settings
