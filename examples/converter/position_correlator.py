from online_monitor.converter.correlator import Correlator
import json

from online_monitor.utils import utils


class PositionCorrelator(Correlator):

    def setup_interpretation(self):
        self.data_buffer = {}  # the data does not have to arrive at the same receive command since ZMQ buffers data

    def interpret_data(self, data):
        for data_one_device in data:
            actual_device, actual_data = json.loads(data_one_device, object_hook=utils.json_numpy_obj_hook).popitem()
            self.data_buffer[actual_device] = actual_data

        for name in self.config['Correlate']:
            print name, 'in', self.data_buffer.keys()
            if name in self.data_buffer.iterkeys():
                print('FIND %s in data')
        
#         print actual_interpret_data
#         intepreted_data = []
#         for one_receiver_data in data:
#             intepreted_data.append(yaml.load(one_receiver_data, object_hook=utils.json_numpy_obj_hook))
        return data
