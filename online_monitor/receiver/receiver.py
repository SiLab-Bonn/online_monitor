from PyQt4 import Qt
from pyqtgraph.Qt import QtCore
import zmq
import logging
from threading import Event

from online_monitor import utils


class DataWorker(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        print 'Init DATA WORKER'
        self._stop_readout = Event()

    def connect(self, receive_address):
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.SUB)  # subscriber
        self.receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        self.receiver.connect(receive_address)

    def receive_data(self):  # infinite loop via QObject.moveToThread(), does not block event loop
        while(not self._stop_readout.wait(1.01)):  # use wait(), do not block here
            print 'RECEIVE'
            try:
                data = self.receiver.recv(flags=zmq.NOBLOCK)
                print data
            except zmq.Again:
                pass

    def shutdown(self):
        self._stop_readout.set()


class Receiver(QtCore.QObject):

    '''The receiver connects to a converter and vizualizes the data according
    to the specified data type.

    Usage:
    '''

    def __init__(self, receive_address, data_type, max_cpu_load=100, loglevel='INFO'):
        self.data_type = data_type
        self.receive_address = receive_address
        self.max_cpu_load = max_cpu_load

        utils.setup_logging(loglevel)

        logging.debug("Initialize %s receiver for data at %s", self.data_type, self.receive_address)

        self.setup_receiver_device()

    def setup_receiver_device(self):  # start new receiver thread
        self.thread = QtCore.QThread()  # no parent
        self.worker = DataWorker()  # no parent
        self.worker.moveToThread(self.thread)
        self.worker.connect(self.receive_address)  # connect to ZMQ publisher
#         self.aboutToQuit.connect(self.worker.stop)  # QtGui.QApplication
        self.thread.started.connect(self.worker.receive_data)
        
#         self.thread.started.connect(self.worker.receive_data)
        
#         self.worker.finished.connect(self.thread.quit)
#         self.worker.finished.connect(self.worker.deleteLater)
#         self.thread.finished.connect(self.thread.deleteLater)
#         self.thread.start()

    def shutdown(self):
        self.exit.set()

    def setup_plots(self, parent):
        raise NotImplementedError("You have to implement a setup_plots method!")
