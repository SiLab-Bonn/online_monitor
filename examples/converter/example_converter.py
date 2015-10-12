import json
from online_monitor.utils import utils
from online_monitor.converter.transceiver import Transceiver


class ExampleConverter(Transceiver):

    def interpret_data(self, data):  # apply a threshold to the data
        data_interpreted = json.loads(data[0], object_hook=utils.json_numpy_obj_hook)['position'].copy()
        data_interpreted[data_interpreted < self.config['threshold']] = 0
        return {'position_with_threshold': data_interpreted}

    def serialze_data(self, data):
        return [json.dumps(data, cls=utils.NumpyEncoder)]
