import multiprocessing
import zmq
import logging
import signal
import time

from online_monitor.utils import utils


class ProducerSim(multiprocessing.Process):

    ''' For testing we have to generate some random data to fake a DAQ. This is done with this Producer Simulation'''

    def __init__(self, backend, kind='Test', name='Undefined', loglevel='INFO', **kwarg):
        multiprocessing.Process.__init__(self)

        self.backend_address = backend
        self.name = name  # name of the DAQ/device
        self.kind = kind
        self.config = kwarg

        self.loglevel = loglevel
        self.exit = multiprocessing.Event()  # exit signal
        utils.setup_logging(loglevel)

        logging.info("Initialize %s producer %s at %s", self.kind, self.name, self.backend_address)

    def setup_producer_device(self):
        # ignore SIGTERM; signal shutdown() is used for controlled process termination
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # Setup ZeroMQ connetions, has to be within run; otherwise ZMQ does not work
        self.context = zmq.Context()
        # Send socket facing services (e.g. online monitor)
        self.sender = self.context.socket(zmq.PUB)
        self.sender.bind(self.backend_address)

    def run(self):  # The receiver loop running in extra process; is called after start() method
        utils.setup_logging(self.loglevel)
        logging.info("Start %s producer %s at %s", self.kind, self.name, self.backend_address)

        self.setup_producer_device()

        while not self.exit.wait(0.02):
            self.send_data()

        # Close connections
        self.sender.close()
        self.context.term()
        logging.info("Close %s producer %s at %s", self.kind, self.name, self.backend_address)

    def shutdown(self):
        self.exit.set()

    def send_data(self):
        raise NotImplemented('This function has to be defined in derived simulation producer')


def main():
    args = utils.parse_arguments()
    configuration = utils.parse_config_file(args.config_file)

    try:
        daqs = []
        for (actual_producer_name, actual_producer_cfg) in configuration['producer_sim'].items():
            actual_producer_cfg['name'] = actual_producer_name
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
