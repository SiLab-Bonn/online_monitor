from online_monitor.converter.correlator import Correlator
import yaml

from online_monitor import utils


class PositionCorrelator(Correlator):

    def interpret_data(self, data):
#         intepreted_data = []
#         for one_receiver_data in data:
#             intepreted_data.append(yaml.load(one_receiver_data, object_hook=utils.json_numpy_obj_hook))
        return data
