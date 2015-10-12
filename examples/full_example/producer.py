import multiprocessing
import zmq
import logging
import signal

from online_monitor.utils import utils
import numpy as np


class Producer(multiprocessing.Process):
    ''' For testing we have to generate some random data to fake a DAQ. This is done here'''
    def __init__(self, send_address, name='Undefined', loglevel='INFO'):
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