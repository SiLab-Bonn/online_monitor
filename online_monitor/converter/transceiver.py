import multiprocessing
import threading
import zmq
import logging
import signal
import psutil
from queue import Queue
from online_monitor.utils import utils


class Transceiver(multiprocessing.Process):

    '''Every converter is a transceiver.

    The transceiver connects a data source / multiple data sources
    (e.g. DAQ systems, other converter, ...) and interprets the data according
    to the specified data type. The interpreted data is published as a ZeroMQ
    publisher.

    Usage:
    To specify a converter for a certain data type, inherit from this base
    class and define these methods accordingly:
        - setup_interpretation()
        - deserialize_data()
        - interpret_data()
        - serialize_data()

    New methods/objects that are not called/created within these function will
    not work! Since a new process is created that only knows the objects
    (and functions) defined there.

    Parameter
    ----------
    backend_address : str, list
        Address or list of adresses of the publishing device(s)
    frontend_address : str
        Address where the converter publishes the converted data
    kind : str
        String describing the kind of converter (e.g. forwarder)
    max_buffer : number
        Maximum messages buffered for interpretation, if exeeded
        data is discarded. If None no limit is applied.
    loglevel : str
        The verbosity level for the logging (e.g. INFO, WARNING)
    '''

    def __init__(self, frontend, backend, kind, name='Undefined',
                 max_buffer=None, loglevel='INFO', **kwarg):
        super(Transceiver, self).__init__()

        self.kind = kind  # kind of transeiver (e.g. forwarder)
        self.frontend_address = frontend  # socket facing a data publisher
        self.backend_address = backend  # socket facing a data receiver
        # Maximum number of input messages buffered, otherwise data omitted
        self.max_buffer = max_buffer
        self.name = name  # name of the DAQ/device
        # Std. setting is unidirectional frondend communication
        self.frontend_socket_type = zmq.SUB
        # Std. setting is unidirectional backend communication
        self.backend_socket_type = zmq.PUB
        # Whether the transceiver is bidirectional
        self._is_bidirectional = False

        if 'max_cpu_load' in kwarg:
            logging.warning('The parameter max_cpu_load is deprecated! Use max_buffer!')

        self.config = kwarg

        # Determine how many frontends/backends the converter has
        # just one frontend socket given
        if not isinstance(self.frontend_address, list):
            self.frontend_address = [self.frontend_address]
        self.n_frontends = len(self.frontend_address)
        
        # just one backend socket given
        if not isinstance(self.backend_address, list):
            self.backend_address = [self.backend_address]
        self.n_backends = len(self.backend_address)

        self.exit = multiprocessing.Event()  # exit signal

        self.loglevel = loglevel
        utils.setup_logging(self.loglevel)

        self.setup_transceiver()

        logging.debug("Initialize %s converter %s with frontends %s "
                      "and backends %s", self.kind, self.name,
                      self.frontend_address, self.backend_address)

    def set_bidirectional_communication(self):
        logging.info('Set bidirectional communication for converter %s '
                     'backend', self.name)
        self.backend_socket_type = zmq.DEALER
        self._is_bidirectional = True

    def _setup_frontend(self):
        ''' Receiver sockets facing clients (DAQ systems)
        '''
        self.frontends = []
        for actual_frontend_address in self.frontend_address:
            # Subscriber or server socket
            actual_frontend = (actual_frontend_address,
                               self.context.socket(self.frontend_socket_type))
            # Wait 0.5 s before termating socket
            actual_frontend[1].setsockopt(zmq.LINGER, 500)
            # Buffer only 10 meassages, then throw data away
            actual_frontend[1].set_hwm(10)
            # A suscriber has to set to not filter any data
            if self.frontend_socket_type == zmq.SUB:
                actual_frontend[1].setsockopt(zmq.SUBSCRIBE, b'')
            actual_frontend[1].connect(actual_frontend_address)
            self.frontends.append(actual_frontend)
        
    def _setup_backend(self):
        ''' Send sockets facing services (e.g. online monitor, other forwarders)
        '''
        self.backends = []
        for actual_backend_address in self.backend_address:
            # publisher or client socket
            actual_backend = (actual_backend_address,
                              self.context.socket(self.backend_socket_type))
            # Wait 0.5 s before termating socket
            actual_backend[1].setsockopt(zmq.LINGER, 500)
            # Buffer only 10 meassages, then throw data away
            actual_backend[1].set_hwm(10)
            actual_backend[1].bind(actual_backend_address)
            self.backends.append(actual_backend)

    def _setup_transceiver(self):
        # ignore SIGTERM; signal shutdown() is used for controlled proc. term.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connections, has to be within run;
        # otherwise ZMQ does not work
        self.context = zmq.Context()
        
        # Front end data queue and event
        self.raw_data = Queue()
        self.fe_stop = threading.Event()

        # If we have a bidirectional socket, e want to recv commnads
        if self._is_bidirectional:
            self.cmds = Queue()
            self.cmd_stop = threading.Event()

        self._setup_backend()

    def recv_data(self):
        
        # Sockets should be created within the thread that accesses them
        self._setup_frontend()

        while not self.fe_stop.is_set():
            raw_data = []
            # Loop over all frontends
            for actual_frontend in self.frontends:
                if actual_frontend[1].poll(timeout=1, flags=zmq.POLLIN):
                    actual_raw_data = actual_frontend[1].recv(flags=zmq.NOBLOCK)
                    raw_data.append((actual_frontend[0],
                                     self.deserialize_data(actual_raw_data)))
            if raw_data:
                self.raw_data.put_nowait(raw_data)

    def recv_commands(self):
        while not self.cmd_stop.wait(0.1):
            if not self.cmds.empty():
                self.handle_command(self.cmds.get_nowait())

    def check_for_cmds(self):
        cmds = []
        for actual_backend in self.backends:
            if actual_backend[1].poll(timeout=1, flags=zmq.POLLIN):
                command = actual_backend[1].recv_json(zmq.NOBLOCK)
                logging.debug("%s converter %s received command %s",
                                self.kind, self.name, command)
                cmds.append(command)
        if cmds:
            self.cmds.put_nowait(cmds)
                    

    def send_data(self, data):
        ''' This function can be overwritten in derived class

            Std. function is to broadcast all receiver data to all backends
        '''
        for frontend_data in data:
            serialized_data = self.serialize_data(frontend_data)
            for actual_backend in self.backends:
                actual_backend[1].send(serialized_data)

    def run(self):  # the Receiver loop run in extra process
        utils.setup_logging(self.loglevel)
        self._setup_transceiver()
        self.setup_interpretation()

        process = psutil.Process(self.ident)  # access this process info
        self.cpu_load = 0.

        # Spawn thread for receiving data
        fe_thread = threading.Thread(target=self.recv_data)
        fe_thread.start()

        # Spawn thread for receiving commands if needed
        if self._is_bidirectional:
            cmd_thread = threading.Thread(target=self.recv_commands)
            cmd_thread.start()

        logging.debug("Start %s transceiver %s at %s", self.kind, self.name,
                      self.backend_address)
        while not self.exit.wait(0.01):
            
            # Checks for commands; if commands are received, they are worked sequentially within a separate thread
            self.check_for_cmds()
            
            # Check for data
            if not self.raw_data.empty():
                
                raw_data = self.raw_data.get_nowait()

                actual_cpu_load = process.cpu_percent()
                # Filter cpu load by running mean since it changes rapidly;
                # cpu load spikes can be filtered away since data queues up
                # through ZMQ
                self.cpu_load = 0.90 * self.cpu_load + 0.1 * actual_cpu_load
                # Check if already too many messages queued up then omit data
                if not self.max_buffer or self.max_buffer > self.raw_data.qsize():
                    data = self.interpret_data(raw_data)
                    # Data is None if the data cannot be converted
                    # (e.g. is incomplete, broken, etc.)
                    if data is not None and len(data) != 0:
                        self.send_data(data)
                    else:
                        logging.warning(f"Converter {self.name} data after interpretation is None or empty!")
                else:
                    logging.warning(f'Converter {self.name} cannot keep up, omitting data for interpretation!')

        # Set all threads stop signals and block until they finish
        self.fe_stop.set()
        fe_thread.join()

        if self._is_bidirectional:
            self.cmd_stop.set()
            cmd_thread.join()

        # Close all sockets from main thread and terminate the context
        for actual_frontend in self.frontends:
            actual_frontend[1].close()
        for actual_backend in self.backends:
            actual_backend[1].close()
        self.context.term()

        logging.debug(
            "Close %s transceiver %s at %s", self.kind, self.name,
            self.backend_address)

    def shutdown(self):
        self.exit.set()

    def setup_transceiver(self):
        ''' Method can be defined to setup transceiver specific parameters

            (e.g. bidirectional communication)
        '''
        pass

    def setup_interpretation(self):
        # This function has to be overwritten in derived class and is called
        # once at the beginning
        pass

    def deserialize_data(self, data):
        ''' To be overwritten when custom serialization is used
        '''
        return zmq.utils.jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def interpret_data(self, data):
        # Data is a list of tuples, with the input address in the first place
        # and the data at the second. This function has to be overwritten in
        # derived class and should not throw exceptions
        # Invalid data and failed interpretations should return None
        # Valid data should return serializable data
        raise NotImplementedError("You have to implement a interpret_data "
                                  "method!")

    def serialize_data(self, data):
        ''' To be overwritten when object needs custom serialization
        '''
        return zmq.utils.jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def handle_command(self, commands):
        ''' Command received from a receiver (bidir. commun. mode).'''
        raise NotImplementedError("You have to implement a handle_command "
                                  "method!")
