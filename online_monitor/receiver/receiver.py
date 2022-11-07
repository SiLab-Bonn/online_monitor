from PyQt5 import QtCore
import zmq
import logging
from threading import Event

from online_monitor.utils import utils




class DataWorker(QtCore.QObject):
    data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, deserializer):
        QtCore.QObject.__init__(self)
        self.deserializer = deserializer
        self._stop_readout = Event()
        self._send_data = None

    def connect_zmq(self, frontend_address, socket_type):
        self.context = zmq.Context()
        self.receiver = self.context.socket(socket_type)  # subscriber
        self.socket_type = socket_type
        # A subscriber has to set to not filter any data
        if self.socket_type == zmq.SUB:
            self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'')
        # Buffer only 10 meassages, then throw data away
        self.receiver.set_hwm(10)
        self.receiver.connect(frontend_address)

    def receive_data(self):  # pragma: no cover; no covered since qt event loop
        ''' Infinite loop via QObject.moveToThread(), does not block event loop
        '''
        while(not self._stop_readout.wait(0.01)):  # use wait(), do not block
            if self._send_data:
                if self.socket_type != zmq.DEALER:
                    raise RuntimeError('You send data without a bidirectional '
                                       'connection! Define a bidirectional '
                                       'connection.')
                self.receiver.send_json(self._send_data)
                self._send_data = None
            try:
                data_serialized = self.receiver.recv(flags=zmq.NOBLOCK)
                data = self.deserializer(data_serialized)
                self.data.emit(data)
            except zmq.Again:
                pass
        self.finished.emit()

    def shutdown(self):
        self._stop_readout.set()

    def send_data(self, data):  # FIXME: not thread safe
        self._send_data = data


class Receiver(QtCore.QObject):

    '''The receiver connects to a converter and vizualizes the data according
    to the specified data type.

    Usage:
    '''

    @property
    def refresh_rate(self):
        return self._refresh_rate

    @refresh_rate.setter
    def refresh_rate(self, rate):

        if isinstance(rate, (int, float)):
            
            if rate == 0:
                logging.warning(f"{self.name} receiver refreshing stopped. Data is not buffered!")
                self.refresh_timer.stop()
            else:
                logging.debug(f"{self.name} receiver refreshing at {rate} Hz!")
                self.refresh_timer.start(int(1e3 / rate))  # timer interval needs to be given in ms
            
        self._refresh_rate = rate        

    def __init__(self, frontend, kind, name='Undefined', loglevel='INFO', **kwarg):
        QtCore.QObject.__init__(self)
        self.kind = kind
        self.frontend_address = frontend
        self.name = name  # name of the DAQ/device
        self.config = kwarg
        # Flag to tell receiver if its active (viewed int the foreground)
        self._active = False
        # Standard is unidirectional communication with PUB/SUB pattern
        self.socket_type = zmq.SUB

        self.frontend_address = self.frontend_address

        utils.setup_logging(loglevel)
        logging.debug("Initialize %s receiver %s at %s", self.kind, self.name,
                      self.frontend_address)
        self.setup_receiver_device()

        self.setup_receiver()

        # Qtimer to detach plot refresh rate from data rate
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_rate = None  # go as fast as data

        self._deprecation_warning_handle_data_issued = False

    def set_bidirectional_communication(self):
        self.socket_type = zmq.DEALER

    def setup_receiver_device(self):  # start new receiver thread
        logging.info("Start %s receiver %s at %s", self.kind, self.name,
                     self.frontend_address)
        self.thread = QtCore.QThread()  # no parent

        self.worker = DataWorker(self.deserialize_data)  # no parent
        # move worker instance to new thread
        self.worker.moveToThread(self.thread)

    # Slot called if the receiver tab widget gets active
    def active(self, value):
        self._active = value

    def start(self):
        # Connect to ZMQ publisher
        self.worker.connect_zmq(self.frontend_address, self.socket_type)
        # Quit thread on worker finished
        self.worker.finished.connect(self.thread.quit)
        # Activate data handle
        self.worker.data.connect(self.handle_data_if_active)

        # Start receive data loop when thread starts
        self.thread.started.connect(self.worker.receive_data)
        # Print on thread finished info
        self.thread.finished.connect(self.finished_info)
        self.thread.start()  # start thread

    def shutdown(self):
        # Set signal to quit receive loop; can take some time
        self.worker.shutdown()
        # Tell thread to exit, loop is/should be terminated already
        self.thread.exit()
        # Delay needed if thread did not exit yet, otherwise message:
        # QThread: Destroyed while thread is still running
        self.thread.wait(500)

    def finished_info(self):  # called when thread finished successfully
        logging.info("Close %s receiver %s at %s", self.kind, self.name,
                     self.frontend_address)

    def handle_data_if_active(self, data):
        ''' Forwards data to data handling function if reveiver is active'''
        if self._active:
            self.handle_data(data)
            if self.refresh_rate is None:
                self.refresh_data()

    def setup_receiver(self):
        ''' Method can be defined to setup receiver specific parameters
            (e.g. bidirectional communication)
        '''
        pass

    def setup_widgets(self, parent, name):
        raise NotImplementedError('You have to implement a setup_widgets '
                                  'method!')

    def handle_data(self, data):
        ''' Handle data

            Receives a dictionary with data and sets the visualization
            accordningly. It is only called if the receiver is active.
        '''
        raise NotImplementedError('You have to implement a handle_data '
                                  'method!')

    def refresh_data(self):
        ''' Method can be defined to detach data handling from refreshing plot data
        '''
        if not self._deprecation_warning_handle_data_issued:
            warning_msg =  "Plotting in the 'handle_data' method is deprecated. Use the 'refresh_data' to plot e.g. set data to a pg.ImageItem, allowing to separate data handling from visualization" 
            logging.warning('DeprecationWarning: ' + warning_msg)
            self._deprecation_warning_handle_data_issued = True


    def send_command(self, command):
        ''' Send command to transceiver

            Has to be json serializable
        '''
        self.worker.send_data(command)

    def deserialize_data(self, data):
        ''' Has to convert the data do a python dict '''
        return zmq.utils.jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
