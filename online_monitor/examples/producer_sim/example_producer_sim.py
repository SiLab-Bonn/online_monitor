import time
import numpy as np

from online_monitor.utils.producer_sim import ProducerSim
from online_monitor.utils import utils


class ExampleProducerSim(ProducerSim):

    def setup_producer_device(self):
        ProducerSim.setup_producer_device(self)
        self.time_stamp = 0

    def send_data(self):
        time.sleep(float(self.config['delay']))  # delay is given in seconds
        random_data = {'time_stamp': self.time_stamp, 'position': np.random.randint(0, 10, 100 * 100).reshape((100, 100))}
        self.sender.send_json(random_data, cls=utils.NumpyEncoder)
        self.time_stamp += 1
