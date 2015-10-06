import logging
import time
import psutil
import sys

from transceiver import Transceiver
from online_monitor import utils


class ConverterManager(object):
    def __init__(self, configuration, loglevel='INFO'):
        utils.setup_logging(loglevel)
        logging.info("Initialize converter mananager with configuration in %s", configuration)
        self.configuration = utils.parse_config_file(configuration)

    def _info_output(self, process_infos):
        info_str = 'INFO: Sytem CPU usage: %1.1f' % psutil.cpu_percent()
        for process_info in process_infos:
            info_str += ', %s CPU usage: %1.1f ' % (process_info[0], process_info[1].cpu_percent())
        info_str += '\r'
        sys.stdout.write(info_str)
        sys.stdout.flush()

    def start(self):
        logging.info('Starting %d converters', len(self.configuration['converter']))
        converters, process_infos = [], []

        for (converter_name, converter_settings) in self.configuration['converter'].items():
            converter_settings['name'] = converter_name
            converter = utils.factory('converter.%s' % converter_settings['data_type'], base_class_type=Transceiver, *(), **converter_settings)
            converter.start()
            process_infos.append((converter_name, psutil.Process(converter.ident)))
            converters.append(converter)
        try:
            while True:
                self._info_output(process_infos)
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info('CRTL-C pressed, shutting down %d converters', len(self.configuration['converter']))
            for converter in converters:
                converter.shutdown()

        for converter in converters:
            converter.join()
        logging.info('Close converter manager')

