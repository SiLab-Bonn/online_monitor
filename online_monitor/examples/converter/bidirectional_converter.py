''' Example how to define a converter that is bidirectional (can receive commands from a receiver) '''
import zmq
import numpy as np

from online_monitor.utils import utils
from online_monitor.converter.transceiver import Transceiver


class ExampleConverter(Transceiver):

    def setup_transceiver(self):  # Called at the beginning
        self.set_bidirectional_communication()  # Sets bidirectional communication
        self.threshold = 0

    def deserialize_data(self, data):
        return zmq.utils.jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def interpret_data(self, data):  # apply a threshold to the data
        data = data[0][1]
        position_with_thr = data['position'].copy()
        position_with_thr[position_with_thr < self.threshold] = 0
        data_with_threshold = {'time_stamp': data['time_stamp'],
                               'position_with_threshold_%s' % self.name: position_with_thr}
        if np.any(position_with_thr):  # only return data if any position info is above threshold
            return [data_with_threshold]

    def serialize_data(self, data):
        return zmq.utils.jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def handle_command(self, command):
        self.threshold = int(command[0])
