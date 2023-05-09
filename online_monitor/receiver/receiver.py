import zmq
import logging
import traceback
from PyQt5 import QtCore
from threading import Event
from queue import Queue

from online_monitor.utils import utils



class QtWorkerSignals(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    exception = QtCore.pyqtSignal(Exception, str)
    timeout = QtCore.pyqtSignal()


class QtWorker(QtCore.QRunnable):
    """
    Implements a worker on which functions can be executed for multi-threading within Qt.
    The worker is an instance of QRunnable, which can be started and handled automatically by Qt and its QThreadPool.
    """

    def __init__(self, func, *args, **kwargs):
        super(QtWorker, self).__init__()

        # Main function which will be executed on this thread
        self.func = func
        # Arguments of main function
        self.args = args
        # Keyword arguments of main function
        self.kwargs = kwargs

        # Needs to be done this way since QRunnable cannot emit signals; QObject needed
        self.signals = QtWorkerSignals()

        # Timer to inform that a timeout occurred
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timeout = None

    def set_timeout(self, timeout):
        self.timeout = int(timeout)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Runs the function func with given arguments args and keyword arguments kwargs.
        If errors or exceptions occur, a signal sends the exception to main thread.
        """

        # Start timer if needed
        if self.timeout is not None:
            self.timer.timeout.connect(self.signals.timeout.emit())
            self.timer.start(self.timeout)

        try:
            if self.args and self.kwargs:
                self.func(*self.args, **self.kwargs)
            elif self.args:
                self.func(*self.args)
            elif self.kwargs:
                self.func(**self.kwargs)
            else:
                self.func()

        except Exception as e:
            # Format traceback and send
            trc_bck = traceback.format_exc()
            # Emit exception signal
            self.signals.exception.emit(e, trc_bck)

        self.signals.finished.emit()


class Receiver(QtCore.QObject):

    '''The receiver connects to a converter and vizualizes the data according
    to the specified data type.

    Usage:
    '''

    data = QtCore.pyqtSignal(dict)

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
        self.ctx = zmq.Context()
        self.threadpool = QtCore.QThreadPool()

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
        self._stop_recv_data = Event()
        self._cmd_queue = Queue()

    def _receive_data(self):
        """
        This function is run as a QRunnable in a different thread;
        Therefore create sockets in here.
        """
        receiver = self.ctx.socket(self.socket_type)
        receiver.setsockopt(zmq.RCVTIMEO, int(100))  # wait up to 100 ms for data
        # A subscriber has to set to not filter any data
        if self.socket_type == zmq.SUB:
            receiver.setsockopt(zmq.SUBSCRIBE, b'')
        # Buffer only 10 meassages, then throw data away
        receiver.set_hwm(10)
        receiver.connect(self.frontend_address)

        while not self._stop_recv_data.is_set():

            # We want to check for outgoing commands if we have a dealer
            while not self._cmd_queue.empty() and self.socket_type == zmq.DEALER:
                # Push out all commands in the queue
                receiver.send_json(self._cmd_queue.get_nowait())

            try:
                data = self.deserialize_data(receiver.recv())
                self.data.emit(data)
            except zmq.Again:
                pass

    def set_bidirectional_communication(self):
        self.socket_type = zmq.DEALER

    def setup_receiver_device(self):  # start new receiver thread
        logging.info("Start %s receiver %s at %s", self.kind, self.name,
                     self.frontend_address)
        
        self.qt_worker = QtWorker(func=self._receive_data)

    # Slot called if the receiver tab widget gets active
    def active(self, value):
        self._active = value

    def start(self):
        
        # Activate data handle
        self.data.connect(self.handle_data_if_active)

        # Print on thread finished info
        self.qt_worker.signals.finished.connect(self.finished_info)
        
        # Start the runnable
        self.threadpool.start(self.qt_worker)

    def shutdown(self):
        
        # Set signal to quit receive loop; can take some time
        self._stop_recv_data.set()
        
        # Delay needed if thread did not exit yet, otherwise message:
        # QThread: Destroyed while thread is still running
        self.threadpool.waitForDone(500)

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
            logging.warning(f'DeprecationWarning in {self.name} receiver: ' + warning_msg)
            self._deprecation_warning_handle_data_issued = True


    def send_command(self, command):
        ''' Send command to transceiver

            Has to be json serializable
        '''
        self._cmd_queue.put_nowait(command)

    def deserialize_data(self, data):
        ''' Has to convert the data do a python dict '''
        return zmq.utils.jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
