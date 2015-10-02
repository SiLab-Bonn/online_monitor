from PyQt4 import Qt
from pyqtgraph.Qt import QtCore
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import zmq
import logging
from threading import Event

from online_monitor import utils


class DataWorker(QtCore.QObject):
    data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, deserialzer):
        QtCore.QObject.__init__(self)
        self.deserialzer = deserialzer
        self._stop_readout = Event()

    def connect(self, receive_address):
        print receive_address
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.SUB)  # subscriber
        self.receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        self.receiver.connect(receive_address)

    def receive_data(self):  # infinite loop via QObject.moveToThread(), does not block event loop
        while(not self._stop_readout.wait(0.01)):  # use wait(), do not block here
            try:
                data_serialized = self.receiver.recv(flags=zmq.NOBLOCK)
                data = self.deserialzer(data_serialized)
                self.data.emit(data)
            except zmq.Again:
                pass
        self.finished.emit()

    def shutdown(self):
        self._stop_readout.set()


class Receiver(QtCore.QObject):

    '''The receiver connects to a converter and vizualizes the data according
    to the specified data type.

    Usage:
    '''
    def __init__(self, receive_address, data_type, device='Undefined', max_cpu_load=100, loglevel='INFO'):
        QtCore.QObject.__init__(self)
        self.data_type = data_type
        self.receive_address = receive_address
        self.max_cpu_load = max_cpu_load
        self.device = device  # name of the DAQ/device

        utils.setup_logging(loglevel)
        logging.debug("Initialize %s receiver for device %s at %s", self.data_type, self.device, self.receive_address)
        self.setup_receiver_device()

    def setup_receiver_device(self):  # start new receiver thread
        logging.info("Start %s receiver for device %s at %s", self.data_type, self.device, self.receive_address)
        self.thread = QtCore.QThread()  # no parent

        self.worker = DataWorker(self.deserialze_data)  # no parent
        self.worker.moveToThread(self.thread)  # move worker instance to new thread
        self.worker.connect(self.receive_address)  # connect to ZMQ publisher
        self.worker.finished.connect(self.thread.quit)  # quit thread on worker finished
        self.worker.data.connect(self.handle_data)

        self.thread.started.connect(self.worker.receive_data)  # start receive data loop when thread starts
        self.thread.finished.connect(self.finished_info)  # print on thread finished info
        self.thread.start()  # start thread

    def shutdown(self):
        self.worker.shutdown()  # set signal to quit receive loop; can take some time
        self.thread.exit()  # tell thread to exit, loop is/should be terminated already
        self.thread.wait(500)  # delay needed if thread di not exit yet, otherwise message: QThread: Destroyed while thread is still running

    def finished_info(self):  # called when thread finished successfully
        logging.info("Close %s receiver for device %s at %s", self.data_type, self.device, self.receive_address)

    def setup_plots(self, parent):
        raise NotImplementedError("You have to implement a setup_plots method!")

    def handle_data(self, data):
        ''' Handle data gets a dictionary with data and sets the visualization accordningly'''
        raise NotImplementedError("You have to implement a handle_data method!")

    def deserialze_data(self, data):
        ''' Has to convert the data do a python dict '''
        raise NotImplementedError("You have to implement a deserialze_data method. Look at the examples!")