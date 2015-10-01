import multiprocessing
import zmq
import logging
import signal
import psutil


class Transceiver(multiprocessing.Process):

    '''The transceiver connects to a DAQ system that delivers data as a ZeroMQ publisher and interprets the data according
    to the specified data type. The interpreted data is published as a ZeroMQ publisher.

    Usage:
    To specify a converter for a certain data type, inherit from this base class and define the methods:
        - setup_interpretation()
        - interpret_data()
    New methods/objects that are not called/created within these function will not work!
    Since a new real process is created that only knows the objects (and functions) defined there.

    ----------
    receive_address : str
        Address of the publishing device
    send_address : str
        Address where the converter publishes the converted data
    data_type : str
        String describing the data type to convert (e.g. pybar_fei4)
    max_cpu_load : number
        Maximum CPU load of the conversion process in percent. Otherwise data is discarded to drop below max_cpu_load.
    loglevel : str
        The verbosity level for the logging (e.g. INFO, WARNING)
    '''

    def __init__(self, receive_address, send_address, data_type, max_cpu_load=100, loglevel='INFO'):
        multiprocessing.Process.__init__(self)

        self.data_type = data_type
        self.receive_address = receive_address
        self.send_address = send_address
        self.max_cpu_load = max_cpu_load

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

        process = psutil.Process(self.ident)  # access this process info
        self.cpu_load = 0.

        logging.info("Start %s transceiver for %s", self.data_type, self.receive_address)
        while not self.exit.wait(0.01):
            try:
                raw_data = self.receiver.recv(flags=zmq.NOBLOCK)
                actual_cpu_load = process.cpu_percent()
                self.cpu_load = 0.95 * self.cpu_load + 0.05 * actual_cpu_load  # filter cpu load by running mean since it changes rapidly; cpu load spikes can be filtered away since data queues up through ZMQ
                if self.cpu_load < self.max_cpu_load:  # check if already too much CPU is used by the conversion, then omit data
                    data = self.interpret_data(raw_data)
                    if data is not None:  # data is None if the data cannot be converted (e.g. is incomplete, broken, etc.)
                        self.sender.send(data)
                else:
                    logging.warning('CPU load of %s converter is with %1.2f > %1.2f too high, omit data!', self.data_type, self.cpu_load, self.max_cpu_load)
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

    def interpret_data(self, data):
        # This function has to be overwritten in derived class and should not throw exceptions
        # if the data is not valid. Invalid data should return None
        raise NotImplementedError("You have to implement a interpret_data method!")
