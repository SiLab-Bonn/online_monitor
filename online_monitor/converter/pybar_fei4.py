from transceiver import Transceiver
from zmq.utils import jsonapi
import numpy as np

from pybar.analysis.RawDataConverter.data_interpreter import PyDataInterpreter
from pybar.analysis.RawDataConverter.data_histograming import PyDataHistograming

from online_monitor import utils


class PybarFEI4(Transceiver):
    def setup_interpretation(self):
        self.interpreter = PyDataInterpreter()
        self.histograming = PyDataHistograming()
        self.interpreter.set_warning_output(False)
        self.histograming.set_no_scan_parameter()
        self.histograming.create_occupancy_hist(True)
        self.histograming.create_rel_bcid_hist(True)
        self.histograming.create_tot_hist(True)
        self.histograming.create_tdc_hist(True)

    def interpret_data(self, data):
        try:
            self.meta_data = jsonapi.loads(data)
        except ValueError:
            try:
                if self.meta_data:
                    try:
                        raw_data_array = np.frombuffer(buffer(data), dtype=self.meta_data.pop('dtype')).reshape(self.meta_data.pop('shape'))
                        return self.interpret_raw_data(raw_data_array)
                    except (KeyError, ValueError):  # KeyError happens if meta data read is omitted; ValueError if np.frombuffer fails due to wrong shape
                        return None
            except AttributeError:  # happens if first data is not meta data
                return None
        return {'meta_data': self.meta_data}

    def interpret_raw_data(self, raw_data):
        self.interpreter.interpret_raw_data(raw_data)
        self.histograming.reset()
        self.histograming.add_hits(self.interpreter.get_hits())
        interpreted_data = {
            'occupancy': self.histograming.get_occupancy(),
            'tot_hist': self.histograming.get_tot_hist(),
            'tdc_counters': self.interpreter.get_tdc_counters(),
            'error_counters': self.interpreter.get_error_counters(),
            'service_records_counters': self.interpreter.get_service_records_counters(),
            'trigger_error_counters': self.interpreter.get_trigger_error_counters(),
            'rel_bcid_hist': self.histograming.get_rel_bcid_hist()
            }
        return interpreted_data

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
