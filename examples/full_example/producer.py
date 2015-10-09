import multiprocessing
import zmq
import logging
import signal
from zmq.utils import jsonapi

from online_monitor import utils
import numpy as np


class Producer(multiprocessing.Process):
    ''' For testing we have to generate some random data to fake a DAQ. This is done here'''
    def __init__(self, send_address, name='Undefined', loglevel='INFO'):
        multiprocessing.Process.__init__(self)

        self.send_address = send_address
        self.name = name  # name of the DAQ/device

        # Determine how many receivers/sender the converter has
        if not isinstance(self.send_address, list):  # just one sender is given
            self.send_address = [self.send_address]
            self.n_senders = 1
        else:
            self.n_senders = len(self.send_address)

        self.exit = multiprocessing.Event()  # exit signal
        utils.setup_logging(loglevel)

        logging.debug("Initialize test producer %s at %s", self.name, self.receive_address)

    def setup_transceiver_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()

        # Send socket facing services (e.g. online monitor)
        self.senders = []
        for actual_send_address in self.send_address:
            actual_sender = self.context.socket(zmq.PUB)
            actual_sender.bind(actual_send_address)
            self.senders.append(actual_sender)

    def run(self):  # the receiver loop
        self.setup_transceiver_device()

        logging.info("Start test producer %s at %s", self.name, self.receive_address)
        while not self.exit.wait(0.1):
            self.send_data({'position': np.random(100, 100)})

        # Close connections
        for actual_receiver in self.receivers:
            actual_receiver.close()

        for actual_sender in self.senders:
            actual_sender.close()
        self.context.term()
        logging.info("Close test producer %s at %s", self.name, self.receive_address)

    def shutdown(self):
        self.exit.set()

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def send_data(self, serialized_data):
        for actual_sender in self.senders:
            actual_sender.send(serialized_data)