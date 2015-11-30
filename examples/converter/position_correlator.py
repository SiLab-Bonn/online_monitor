from online_monitor.converter.correlator import Correlator
import json
import logging

from online_monitor.utils import utils


class PositionCorrelator(Correlator):

    def deserialze_data(self, data):
        return json.loads(data, object_hook=utils.json_numpy_obj_hook)

    def setup_interpretation(self):
        self.data_buffer = {}  # the data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior

    def interpret_data(self, data):
        for actual_device_data in data:  # loop over all devices
            print actual_device_data['time_stamp']
            print actual_device_data['time_stamp']
            for actual_data_type, actual_data in actual_device_data.iteritems():
                print actual_data_type, actual_data


#         print actual_interpret_data
#         intepreted_data = []
#         for one_receiver_data in data:
#             intepreted_data.append(yaml.load(one_receiver_data, object_hook=utils.json_numpy_obj_hook))
        return None
