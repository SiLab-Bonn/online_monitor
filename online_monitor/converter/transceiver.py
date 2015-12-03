import multiprocessing
import zmq
import logging
import signal
import psutil
import sys

from zmq.eventloop import ioloop, zmqstream

from online_monitor.utils import utils


class Transceiver(multiprocessing.Process):

    '''Every converter is a transceiver. The transceiver connects a data source / multiple data sources (e.g. DAQ systems, other converter, ...)
    and interprets the data according to the specified data type. The interpreted data is published as a ZeroMQ publisher.

    Usage:
    To specify a converter for a certain data type, inherit from this base class and define these methods accordingly:
        - setup_interpretation()
        - deserialze_data()
        - interpret_data()
        - serialze_data()
    New methods/objects that are not called/created within these function will not work!
    Since a new process is created that only knows the objects (and functions) defined there.

    Parameter
    ----------
    backend_address : str, list
        Address or list of adresses of the publishing device(s)
    frontend_address : str
        Address where the converter publishes the converted data
    kind : str
        String describing the kind of converter (e.g. forwarder)
    max_cpu_load : number
        Maximum CPU load of the conversion process in percent. Otherwise data is discarded to drop below max_cpu_load.
    loglevel : str
        The verbosity level for the logging (e.g. INFO, WARNING)
    '''

    def __init__(self, frontend, backend, kind, name='Undefined', max_cpu_load=100, loglevel='INFO', **kwarg):
        multiprocessing.Process.__init__(self)

        self.kind = kind  # kind of transeiver (e.g. forwarder)
        self.frontend_address = frontend  # socket facing a data publisher
        self.backend_address = backend  # socket facing a data receiver
        self.max_cpu_load = max_cpu_load  # Maximum CPU load allowed, otherwise data omitted
        self.name = name  # name of the DAQ/device
        self.frontend_socket = zmq.SUB  # std. setting is unidirectional frondend communication
        self.backend_socket = zmq.PUB  # std. setting is unidirectional backend communication
        self.config = kwarg  # Additional implementation specifig configurations given in yaml file

        if 'connection' in self.config.keys():
            if 'bidirectional' in self.config['connection']:
                self.frontend_socket = zmq.REP  # Client / Server pattern to allow bidirectional communication; backend is server
        if 'connection' in self.config.keys():
            if 'bidirectional' in self.config['connection']:
                self.backend_socket = zmq.REQ  # Client / Server pattern to allow bidirectional communication; frontend is client

        # Determine how many frontends/backends the converter has
        if not isinstance(self.frontend_address, list):  # just one frontend socket given
            self.frontend_address = [self.frontend_address]
            self.n_frontends = 1
        else:
            self.n_frontends = len(self.frontend_address)
        if not isinstance(self.backend_address, list):  # just one backend socket given
            self.backend_address = [self.backend_address]
            self.n_backends = 1
        else:
            self.n_backends = len(self.backend_address)

        self.exit = multiprocessing.Event()  # exit signal

        self.loglevel = loglevel
        utils.setup_logging(self.loglevel)

        logging.debug("Initialize %s converter %s with frontends %s and backends %s", self.kind, self.name, self.frontend_address, self.backend_address)

    def setup_frontend(self):
        # Receiver sockets facing clients (DAQ systems)
        self.frontends = []
        for actual_frontend_address in self.frontend_address:
            actual_frontend = (actual_frontend_address, self.context.socket(self.frontend_socket))  # subscriber or server socket
            actual_frontend[1].connect(actual_frontend_address)
            if self.frontend_socket == zmq.SUB:  # A suscriber has to set to not filter any data
                actual_frontend[1].setsockopt_string(zmq.SUBSCRIBE, u'')  # do not filter any data
            self.frontends.append(actual_frontend)

    def setup_backend(self):
        # Send socket facing services (e.g. online monitor, other forwarders)
        self.backends = []
        for actual_backend_address in self.backend_address:
            actual_backend = (actual_backend_address, self.context.socket(self.backend_socket))  # publisher or client socket
            actual_backend[1].bind(actual_backend_address)
            self.backends.append(actual_backend)

    def setup_transceiver(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()

        self.setup_frontend()
        self.setup_backend()

    def recv_data(self):
        raw_data = []
        # Loop over all frontends
        for actual_frontend in self.frontends:
            try:
                actual_raw_data = actual_frontend[1].recv(flags=zmq.NOBLOCK)
                if sys.version_info >= (3, 0):  # http://stackoverflow.com/questions/24369666/typeerror-b1-is-not-json-serializable
                    actual_raw_data = actual_raw_data.decode('utf-8')
                raw_data.append((actual_frontend[0], self.deserialze_data(actual_raw_data)))
            except zmq.Again:  # no data
                pass
        return raw_data

    def send_data(self, data):
        # This function can be overwritten in derived class; std function is to broadcast all receiver data to all backends
        for frontend_data in data:
            serialized_data = self.serialze_data(frontend_data)
            if sys.version_info >= (3, 0):
                serialized_data = serialized_data.encode('utf-8')
            for actual_backend in self.backends:
                actual_backend[1].send(serialized_data)

    def run(self):  # the receiver loop
        utils.setup_logging(self.loglevel)
        self.setup_transceiver()
        self.setup_interpretation()

        process = psutil.Process(self.ident)  # access this process info
        self.cpu_load = 0.

        logging.debug("Start %s transceiver %s at %s", self.kind, self.name, self.backend_address)
        while not self.exit.wait(0.01):
            raw_data = self.recv_data()

            if not raw_data:  # read again if no raw data is read
                continue

            actual_cpu_load = process.cpu_percent()
            self.cpu_load = 0.95 * self.cpu_load + 0.05 * actual_cpu_load  # filter cpu load by running mean since it changes rapidly; cpu load spikes can be filtered away since data queues up through ZMQ
            if not self.max_cpu_load or self.cpu_load < self.max_cpu_load:  # check if already too much CPU is used by the conversion, then omit data
                data = self.interpret_data(raw_data)
                if data is not None and len(data) != 0:  # data is None if the data cannot be converted (e.g. is incomplete, broken, etc.)
                    self.send_data(data)
            else:
                logging.warning('CPU load of %s converter %s is with %1.2f > %1.2f too high, omit data!', self.kind, self.name, self.cpu_load, self.max_cpu_load)

        # Close connections
        for actual_frontend in self.frontends:
            actual_frontend[1].close()
        for actual_backend in self.backends:
            actual_backend[1].close()
        self.context.term()

        logging.debug("Close %s transceiver %s at %s", self.kind, self.name, self.backend_address)

    def shutdown(self):
        self.exit.set()

    def setup_interpretation(self):
        # This function has to be overwritten in derived class and is called once at the beginning
        pass

    def interpret_data(self, data):
        # Data is a list of tuples, with the input address in the first place and the data at the second.
        # This function has to be overwritten in derived class and should not throw exceptions
        # Invalid data and failed interpretations should return None
        # Valid data should return serializable data
        raise NotImplementedError("You have to implement a interpret_data method!")

    def deserialze_data(self, data):
        return data

    def serialze_data(self, data):
        return data
