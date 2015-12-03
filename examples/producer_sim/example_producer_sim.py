import time
import numpy as np
import logging

from online_monitor.utils.producer_sim import ProducerSim
from online_monitor.utils import utils


class ExampleProducerSim(ProducerSim):

    def setup_producer_device(self):
        ProducerSim.setup_producer_device(self)
        self.time_stamp = 0

    def send_data(self):
        time.sleep(float(self.config['delay']))  # delay is given in seconds
#         random_values = np.random.randint(0, 100, 100 * 100).reshape((100, 100))
#         random_positions = np.random.randint(0, 100, 100 * 100).reshape((100, 100))
#         random_positions[random_values < 95] = 0  # only set a few positions, otherwise position correlation is useless
#         random_data = {'time_stamp': self.time_stamp, 'position': random_positions}  # Generate random position data
#         self.sender.send_json(random_data, cls=utils.NumpyEncoder)  # Send numpy array with json
#         self.time_stamp += 1  # Time stamp is a simple counter here
        random_data = {'time_stamp': self.time_stamp, 'position': np.random.randint(0, 10, 100 * 100).reshape((100, 100))}
        self.sender.send_json(random_data, cls=utils.NumpyEncoder)
        self.time_stamp += 1
