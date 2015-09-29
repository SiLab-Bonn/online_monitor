import sys
import zmq
import time
from optparse import OptionParser
import logging
import threading


class Converter(object):
    '''The converter connects to a DAQ system that delivers data as a ZeroMQ publisher and interprets the data according 
    to the specified data type. The interpreted data is published as a ZeroMQ publisher.
    The converted data can then be used e.g. by the online monitor.
    ----------
    type : str
        String describing the data type to convert (e.g. pyBAR_fei4)
    address : str
        Address of the publishing device
    loglevel : str
        The verbosity level for the logging (e.g. INFO, WARNING)
    '''
    def __init__(self, recv_address, data_type, send_address, loglevel='INFO'):
        # Setup logging
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

        self.data_type = data_type
        self.recv_address = recv_address
        self.send_address = send_address

        logging.info("Initialize converter for %s data at %s", self.data_type, self.recv_address)
        self.init_forwarder_device()  # Setup ZeroMQ connetions
        # Start the receiver loop
        self.receiver_loop()

    def init_forwarder_device(self):
        logging.info("Publish interpreted data at %s", self.send_address)
        self.context = zmq.Context()
        # Socket facing clients (DAQ systems)
        self.receiver = self.context.socket(zmq.SUB)  # subscriber
        self.receiver.connect(self.recv_address)
        self.receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        # Socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.connect(self.send_address)
#         # Init forwarder to just forward data without interpretation
#         zmq.device(zmq.FORWARDER, self.receiver, self.sender)
#         # Initialize poll set
#         self.poller = zmq.Poller()
#         self.poller.register(self.receiver, zmq.POLLIN)

    def receiver_loop(self):
        logging.info("Start receiver for %s", self.recv_address)
        while True:
            try:
                raw_data = self.receiver.recv()
                data = self.interpret_data(raw_data)
                print data
                self.sender.send(data)
            except KeyboardInterrupt:
                logging.info('Closing converter for %s', self.data_type)
                break

    def interpret_data(self, data):
        return data

    def __del__(self):
        self.receiver.close()
        self.sender.close()
        self.context.term()

if __name__ == '__main__':
    args = ['tcp://localhost:5678', 'pybar_fei4', 'tcp://localhost:5559']
    converter = Converter(*args, loglevel='INFO')
#     # Parse command line options
#     parser = OptionParser(usage="usage: %prog RECV_ADDRS TYPE SEND_ADDR", description="TYPE: RECV_ADDRS: Remote address of the sender\nTYPE: Data type (e.g. pybar_fei4)\nRECV_ADDRS: Address to publish interpreted data")
#     parser.add_option("-l", "--log", type="string", help="Logging level (e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL)")
#     (options, args) = parser.parse_args()
#     if len(args) != 3:
#         parser.error("Wrong number of arguments")
#     # Start converter instance, blocks until terminated

#     converter = Converter(*args, loglevel=options.log if options.log else 'INFO')
