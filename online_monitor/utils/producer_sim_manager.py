import logging
import time
import psutil
import sys

from online_monitor.utils.producer_sim import ProducerSim
from online_monitor.utils import utils


class ProducerSimManager(object):
    def __init__(self, configuration, loglevel='INFO'):
        utils.setup_logging(loglevel)
        logging.info("Initialize producer simulation mananager with configuration in %s", configuration)
        self.configuration = utils.parse_config_file(configuration)

    def _info_output(self, process_infos):
        info_str = 'INFO: Sytem CPU: %1.1f' % psutil.cpu_percent()
        for process_info in process_infos:
            info_str += ', %s: %1.1f ' % (process_info[0], process_info[1].cpu_percent())
        info_str += '\r'
        sys.stdout.write(info_str)
        sys.stdout.flush()

    def start(self):
        try:
            self.configuration['producer_sim']
        except KeyError:
            logging.info('No producer simulation defined in config file')
            logging.info('Close producer simulation manager')
            return
        logging.info('Starting %d producer simulations', len(self.configuration['producer_sim']))
        producer_sims, process_infos = [], []

        for (producer_sim_name, producer_sim_settings) in self.configuration['producer_sim'].items():
            producer_sim_settings['name'] = producer_sim_name
            producer_sim = utils.load_producer_sim(producer_sim_settings['kind'], base_class_type=ProducerSim, *(), **producer_sim_settings)
            producer_sim.start()
            process_infos.append((producer_sim_name, psutil.Process(producer_sim.ident)))
            producer_sims.append(producer_sim)
        try:
            while True:
                self._info_output(process_infos)
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info('CRTL-C pressed, shutting down %d producer simulations', len(self.configuration['producer_sim']))
            for producer_sim in producer_sims:
                producer_sim.shutdown()

        for producer_sim in producer_sims:
            producer_sim.join()
        logging.info('Close producer simulation manager')

