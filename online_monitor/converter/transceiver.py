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

        logging.debug("Initialize %s converter for data at %s", self.data_type, self.receive_address)

    def setup_logging(self, loglevel):
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

    def setup_forwarder_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()
        # Socket facing clients (DAQ systems)
        self.receiver = self.context.socket(zmq.SUB)  # subscriber
        self.receiver.connect(self.receive_address)
        self.receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        # Socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.connect(self.send_address)

    def run(self):  # the receiver loop
        # Thisfunction has to work 'stand alone' since it is spawned as a new process
        # Thus all setting has to take place here
        self.setup_forwarder_device()
        self.setup_interpretation()

        logging.info("Start %s transceiver for %s", self.data_type, self.receive_address)
        while not self.exit.wait(0.01):
            try:
                raw_data = self.receiver.recv(flags=zmq.NOBLOCK)
                data = self.interpret_data(raw_data)
                if data is not None:  # data is None if there is nothing to convert
                    self.sender.send(data)
            except zmq.Again:  # no data
                pass

        self.receiver.close()
        self.sender.close()
        self.context.term()
        logging.info("Close %s transceiver for %s", self.data_type, self.receive_address)

    def shutdown(self):
        self.exit.set()

    def setup_interpretation(self, data):  # this function can be overwritten in derived class
        pass

    def interpret_data(self, data):  # this function has to be overwritten in derived class
        raise NotImplementedError("You have to implement a interpret_data method!")
