import multiprocessing
import zmq
import logging
import signal
import time

from online_monitor.utils import utils


class ProducerSim(multiprocessing.Process):

    ''' For testing we have to generate some random data to fake a DAQ. This is done with this Producer Simulation'''

    def __init__(self, send_address, kind='Test', name='Undefined', loglevel='INFO', **kwarg):
        multiprocessing.Process.__init__(self)

        self.send_address = send_address
        self.name = name  # name of the DAQ/device
        self.kind = kind
        self.config = kwarg
        self.send_address = send_address

        self.loglevel = loglevel
        self.exit = multiprocessing.Event()  # exit signal
        utils.setup_logging(loglevel)

        logging.info("Initialize %s producer %s at %s", self.kind, self.name, self.send_address)

    def setup_producer_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise zMQ does not work
        self.context = zmq.Context()
        # Send socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.bind(self.send_address)

    def run(self):  # the receiver loop
        utils.setup_logging(self.loglevel)
        self.setup_producer_device()

        logging.info("Start %s producer %s at %s", self.kind, self.name, self.send_address)
        while not self.exit.wait(0.2):
            self.send_data()

        # Close connections
        self.sender.close()
        self.context.term()
        logging.info("Close %s producer %s at %s", self.kind, self.name, self.send_address)

    def shutdown(self):
        self.exit.set()

    def send_data(self):
        raise NotImplemented('This function has to be defined in derived simulation producer')


def main():
    args = utils.parse_arguments()
    configuration = utils.parse_config_file(args.config_file)

    try:
        daqs = []
        for (actual_producer_name, actual_producer_cfg) in configuration['producer'].items():
            actual_producer_cfg['name'] = actual_producer_name
            # only take test producers
            if actual_producer_cfg['kind'] != 'test':
                continue
            daq = ProducerSim(loglevel=args.log, **actual_producer_cfg)
            daqs.append(daq)

        for daq in daqs:
            daq.start()

        while(True):
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                for daq in daqs:
                    daq.shutdown()
                for daq in daqs:
                    daq.join(timeout=500)
                return
    except KeyError:  # A simulation producer is just for testing, do not require one in the configuration file
        pass

if __name__ == '__main__':
    main()
