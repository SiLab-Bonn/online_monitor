import multiprocessing
import zmq
import logging
import signal
import numpy as np

from online_monitor.utils import utils


class ProducerSim(multiprocessing.Process):
    ''' For testing we have to generate some random data to fake a DAQ. This is done with this Producer Simulation'''
    def __init__(self, send_address, name='Undefined', loglevel='INFO', **kwarg):
        multiprocessing.Process.__init__(self)

        self.send_address = send_address
        self.name = name  # name of the DAQ/device

        self.send_address = send_address

        self.exit = multiprocessing.Event()  # exit signal
        utils.setup_logging(loglevel)

        logging.info("Initialize test producer %s at %s", self.name, self.send_address)

    def setup_producer_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()

        # Send socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.bind(self.send_address)

    def run(self):  # the receiver loop
        self.setup_producer_device()

        logging.info("Start test producer %s at %s", self.name, self.send_address)
        while not self.exit.wait(0.2):
            random_data = {'position': np.random.randint(0, 10, 100 * 100).reshape((100, 100))}
            self.sender.send_json(random_data, cls=utils.NumpyEncoder)

        # Close connections
        self.sender.close()
        self.context.term()
        logging.info("Close test producer %s at %s", self.name, self.send_address)

    def shutdown(self):
        self.exit.set()


if __name__ == '__main__':
    import time
    args = utils.parse_arguments()
    configuration = utils.parse_config_file(args.config_file)

    daqs = []
    for (actual_producer_name, actual_producer_cfg) in configuration['producer'].items():
        daq = ProducerSim(send_address=actual_producer_cfg['send_address'],
                          name=actual_producer_name,
                          loglevel=args.log)
        daqs.append(daq)

    for daq in daqs:
        daq.start()

    while(True):
        try:
            time.sleep(2)
        except:
            for daq in daqs:
                daq.shutdown()
