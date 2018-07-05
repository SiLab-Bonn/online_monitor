import json

from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils


class PositionCorrelator(Transceiver):

    def deserialize_data(self, data):
        return json.loads(data, object_hook=utils.json_numpy_obj_hook)

    def setup_interpretation(self):
        # Buffer data, since data does not have to arrive at the same receive command
        # since ZMQ buffers data and the DUT can have different time behavior
        self.data_buffer = {}

    def interpret_data(self, data):
        # Data is a list filled with data of the actual readout, since multiple receivers are used
        # the size can be between 0 and n_receivers
        # One entry in the list is a tuple, with the front end address in the first and
        # the data in the second. This allows to distinguish from which FE the data is.
        for actual_device in data:  # loop over all devices of actual received data
            # Loop over the data of the device (is a dict with time_stamp, position keys)
            dev_addrs = actual_device[0]
            dev_data = actual_device[1]

            try:
                values = self.data_buffer[dev_data['time_stamp']]
                print values, dev_data
            except KeyError:
                self.data_buffer[dev_data['time_stamp']] = dev_data['position']
