from pyqtgraph.Qt import QtCore
import zmq
import logging
from threading import Event

from online_monitor.utils import utils


class DataWorker(QtCore.QObject):
    data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, deserialzer):
        QtCore.QObject.__init__(self)
        self.deserialzer = deserialzer
        self._stop_readout = Event()
        self._send_data = None

    def connect_zmq(self, frontend_address, socket_type):
        self.context = zmq.Context()
        self.receiver = self.context.socket(socket_type)  # subscriber
        self.socket_type = socket_type
        if self.socket_type == zmq.SUB:  # A suscriber has to set to not filter any data
            self.receiver.setsockopt_string(zmq.SUBSCRIBE, u'')  # do not filter any data
        self.receiver.connect(frontend_address)

    def receive_data(self):  # pragma: no cover; infinite loop via QObject.moveToThread(), does not block event loop, is shown as not covered in unittests due to qt event loop
        while(not self._stop_readout.wait(0.01)):  # use wait(), do not block here
            if self._send_data:
                if self.socket_type != zmq.DEALER:
                    raise RuntimeError('You send data without a bidirectional connection! Define a bidirectional connection.')
                self.receiver.send(self._send_data)
                self._send_data = None
            try:
                data_serialized = self.receiver.recv(flags=zmq.NOBLOCK)
                data = self.deserialzer(data_serialized)
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
    def __init__(self, frontend, kind, name='Undefined', max_cpu_load=100, loglevel='INFO', **kwarg):
        QtCore.QObject.__init__(self)
        self.kind = kind
        self.frontend_address = frontend
        self.max_cpu_load = max_cpu_load
        self.name = name  # name of the DAQ/device
        self.config = kwarg
        self._active = False  # flag to tell receiver if its active (viewed int the foreground)
        self.socket_type = zmq.SUB  # atandard is unidirectional communication with PUB/SUB pattern

        self.frontend_address = self.frontend_address

        utils.setup_logging(loglevel)
        logging.debug("Initialize %s receiver %s at %s", self.kind, self.name, self.frontend_address)
        self.setup_receiver_device()

        self.setup_receiver()

    def set_bidirectional_communication(self):
        self.socket_type = zmq.DEALER

    def setup_receiver_device(self):  # start new receiver thread
        logging.info("Start %s receiver %s at %s", self.kind, self.name, self.frontend_address)
        self.thread = QtCore.QThread()  # no parent

        self.worker = DataWorker(self.deserialze_data)  # no parent
        self.worker.moveToThread(self.thread)  # move worker instance to new thread

    def active(self, value):  # slot called if the receiver tab widget gets active
        self._active = value

    def start(self):
        self.worker.connect_zmq(self.frontend_address, self.socket_type)  # connect to ZMQ publisher
        self.worker.finished.connect(self.thread.quit)  # quit thread on worker finished
        self.worker.data.connect(self.handle_data_if_active)  # activate data handle

        self.thread.started.connect(self.worker.receive_data)  # start receive data loop when thread starts
        self.thread.finished.connect(self.finished_info)  # print on thread finished info
        self.thread.start()  # start thread

    def shutdown(self):
        self.worker.shutdown()  # set signal to quit receive loop; can take some time
        self.thread.exit()  # tell thread to exit, loop is/should be terminated already
        self.thread.wait(500)  # delay needed if thread did not exit yet, otherwise message: QThread: Destroyed while thread is still running

    def finished_info(self):  # called when thread finished successfully
        logging.info("Close %s receiver %s at %s", self.kind, self.name, self.frontend_address)

    def handle_data_if_active(self, data):
        ''' Forwards the data to the data handling function of the reveiver is active'''
        if self._active:
            self.handle_data(data)

    def setup_receiver(self):
        ''' Method can be defined to setup receiver specific parameters (e.g. bidirectional communication)'''
        pass

    def setup_widgets(self, parent, name):
        raise NotImplementedError("You have to implement a setup_widgets method!")

    def handle_data(self, data):
        ''' Handle data gets a dictionary with data and sets the visualization accordningly. It is only called if the receiver is active.'''
        raise NotImplementedError("You have to implement a handle_data method!")

    def send_command(self, command):
        self.worker.send_data(command)

    def deserialze_data(self, data):
        ''' Has to convert the data do a python dict '''
        raise NotImplementedError("You have to implement a deserialze_data method. Look at the examples!")
