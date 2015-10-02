import utils
from converter.converter_manager import ConverterManager


if __name__ == '__main__':
    args = utils.parse_arguments()
    utils.setup_logging(args.log)

    cm = ConverterManager(args.config_file)
    cm.start()  # blocking function, returns on SIGTERM signal
