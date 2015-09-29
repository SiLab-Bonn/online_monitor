import argparse
import logging

from converter.converter_manager import ConverterManager


def setup_logging(loglevel):  # set logging level of this module
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)


if __name__ == '__main__':
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

    setup_logging(args.log)

    cm = ConverterManager('configuration.yaml')
    cm.start()  # blocking function, returns on SIGTERM signal
