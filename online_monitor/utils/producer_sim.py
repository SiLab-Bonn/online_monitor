import multiprocessing
import zmq
import logging
import signal
import numpy as np

from online_monitor.utils import utils


class ProducerSim(multiprocessing.Process):
    ''' For testing we have to generate some random data to fake a DAQ. This is done with this Producer Simulation'''
    def __init__(self, send_address, data_type='Test', name='Undefined', loglevel='INFO', **kwarg):
        multiprocessing.Process.__init__(self)

        self.send_address = send_address
        self.name = name  # name of the DAQ/device
        self.data_type = data_type
        self.config = kwarg
        self.send_address = send_address

        self.loglevel = loglevel
        self.exit = multiprocessing.Event()  # exit signal
        utils.setup_logging(loglevel)

        logging.info("Initialize %s producer %s at %s", self.data_type, self.name, self.send_address)

    def setup_producer_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()

        # Send socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.bind(self.send_address)

    def run(self):  # the receiver loop
        utils.setup_logging(self.loglevel)
        self.setup_producer_device()

        logging.info("Start %s producer %s at %s", self.data_type, self.name, self.send_address)
        while not self.exit.wait(0.2):
            self.send_data()

        # Close connections
        self.sender.close()
        self.context.term()
        logging.info("Close %s producer %s at %s", self.data_type, self.name, self.send_address)

    def shutdown(self):
        self.exit.set()

    def send_data(self):
        random_data = {'position': np.random.randint(0, 10, 100 * 100).reshape((100, 100))}
        self.sender.send_json(random_data, cls=utils.NumpyEncoder)


def main():
    import time
    args = utils.parse_arguments()
    configuration = utils.parse_config_file(args.config_file)

    daqs = []
    for (actual_producer_name, actual_producer_cfg) in configuration['producer'].items():
        actual_producer_cfg['name'] = actual_producer_name
        if actual_producer_cfg['data_type'] != 'test':  # only take pybar producers
            continue
        daq = ProducerSim(loglevel=args.log,
                          **actual_producer_cfg)
        daqs.append(daq)

    for daq in daqs:
        daq.start()

    while(True):
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            for daq in daqs:
                daq.shutdown()
            for daq in daqs:
                daq.join(timeout=500)
            return

if __name__ == '__main__':
    main()
