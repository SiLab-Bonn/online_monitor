from online_monitor.converter.correlator import Correlator
import json

from online_monitor.utils import utils


class PositionCorrelator(Correlator):

    def deserialize_data(self, data):
        return json.loads(data, object_hook=utils.json_numpy_obj_hook)

    def setup_interpretation(self):
        self.data_buffer = {}  # the data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior

    def interpret_data(self, data):
        for actual_device_data in data:  # loop over all devices of actual received data
            for actual_data_type, actual_data in actual_device_data[1].items():
                if 'time_stamp' not in actual_data_type:
                    data_buffer = {actual_device_data[0]: actual_data}
                else:
                    actual_time_stamp = actual_data


#         print actual_interpret_data
#         intepreted_data = []
#         for one_receiver_data in data:
#             intepreted_data.append(yaml.load(one_receiver_data, object_hook=utils.json_numpy_obj_hook))
        return None
