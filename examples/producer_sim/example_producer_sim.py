import time
import numpy as np

from online_monitor.utils.producer_sim import ProducerSim
from online_monitor.utils import utils


class ExampleProducerSim(ProducerSim):

    def send_data(self):
        time.sleep(0.2)
        random_data = {'position': np.random.randint(0, 10, 100 * 100).reshape((100, 100))}
        self.sender.send_json(random_data, cls=utils.NumpyEncoder)
