import multiprocessing
import zmq
import logging
import signal


class Transceiver(multiprocessing.Process):

    '''The transceiver connects to a DAQ system that delivers data as a ZeroMQ publisher and interprets the data according
    to the specified data type. The interpreted data is published as a ZeroMQ publisher.
    ----------
    receive_address : str
        Address of the publishing device
    send_address : str
        Address where the converter publishes the converted data
    data_type : str
        String describing the data type to convert (e.g. pybar_fei4)
    loglevel : str
        The verbosity level for the logging (e.g. INFO, WARNING)
    '''

    def __init__(self, receive_address, send_address, data_type, loglevel='INFO'):
        multiprocessing.Process.__init__(self)

        self.data_type = data_type
        self.receive_address = receive_address
        self.send_address = send_address

        self.exit = multiprocessing.Event()  # exit signal
        self.setup_logging(loglevel)

        logging.info("Initialize %s converter for data at %s", self.data_type, self.receive_address)

    def setup_logging(self, loglevel):
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

    def run(self):  # the receiver loop
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        context = zmq.Context()
        # Socket facing clients (DAQ systems)
        receiver = context.socket(zmq.SUB)  # subscriber
        receiver.connect(self.receive_address)
        receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        # Socket facing services (e.g. online monitor)
        sender = context.socket(zmq.PUB)
        sender.connect(self.send_address)

        logging.info("Start %s transceiver for %s", self.data_type, self.receive_address)
        while not self.exit.wait(0.01):
            try:
                raw_data = receiver.recv(flags=zmq.NOBLOCK)
                data = self.interpret_data(raw_data)
                sender.send(data)
            except zmq.Again:
                pass

        receiver.close()
        sender.close()
        context.term()
        logging.info("Close %s transceiver for %s", self.data_type, self.receive_address)

    def shutdown(self):
        self.exit.set()

    def interpret_data(self, data):  # this function has to be overwritten in derived class
        raise NotImplementedError("You have to implement a interpret_data method!")
