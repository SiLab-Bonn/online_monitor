import ConfigParser
import ast
import sys
import os

file_name = os.path.dirname(sys.modules[__name__].__file__) + r'/../OnlineMonitor.ini'


def add_converter_path(path):  # path where to search for converter modules
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    paths = get_converter_path()
    paths.append(path)  # append actual path
    paths = list(set(paths))  # remove duplicates
    config.set('converter', 'path', str(paths)[1:-1])  # store new string representation
    with open(file_name, 'w') as f:
        config.write(f)


def add_receiver_path(path):  # path where to search for converter modules
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    paths = get_receiver_path()
    paths.append(path)  # append actual path
    paths = list(set(paths))  # remove duplicates
    config.set('receiver', 'path', str(paths)[1:-1])  # store new string representation
    with open(file_name, 'w') as f:
        config.write(f)


def delete_converter_path(path):  # path where to search for converter modules
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    paths = [p for p in get_converter_path() if p != path]
    config.set('converter', 'path', str(paths)[1:-1])  # store new string representation
    with open(file_name, 'w') as f:
        config.write(f)


def delete_receiver_path(path):  # path where to search for converter modules
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    paths = [p for p in get_receiver_path() if p != path]
    config.set('receiver', 'path', str(paths)[1:-1])  # store new string representation
    with open(file_name, 'w') as f:
        config.write(f)


def get_converter_path():
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)  # WARNING: ConfigParser.NoSectionError: can mean no file at all!
    path = ast.literal_eval(config.get('converter', 'path'))
    if isinstance(path, tuple):
        return [p for p in path]
    return [path]


def get_receiver_path():
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)  # WARNING: ConfigParser.NoSectionError: can mean no file at all!
    path = ast.literal_eval(config.get('receiver', 'path'))
    if isinstance(path, tuple):
        return [p for p in path]
    return [path]


def set_window_geometry(geometry):
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    try:
        config.add_section('OnlineMonitor')
    except ConfigParser.DuplicateSectionError:  # already existing
        pass
    config.set('OnlineMonitor', 'geometry', str(geometry)[1:-1])  # store new string representation
    with open(file_name, 'w') as f:
        config.write(f)


def get_window_geometry():
    config = ConfigParser.SafeConfigParser()
    config.read(file_name)
    try:
        return ast.literal_eval(config.get('OnlineMonitor', 'geometry'))
    except ConfigParser.NoSectionError:
        return (100, 100, 1024, 768)  # std. settings

if __name__ == '__main__':
    file_name = r'../OnlineMonitor.ini'
    add_receiver_path(r'receiver')
    add_converter_path(r'converter')

