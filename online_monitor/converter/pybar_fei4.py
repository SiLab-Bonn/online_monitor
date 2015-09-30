from transceiver import Transceiver
from zmq.utils import jsonapi
import numpy as np

from pybar.analysis.RawDataConverter.data_interpreter import PyDataInterpreter
from pybar.analysis.RawDataConverter.data_histograming import PyDataHistograming


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
                    raw_data_array = np.frombuffer(buffer(data), dtype=self.meta_data.pop('dtype')).reshape(self.meta_data.pop('shape'))
                    self.analyze_raw_data(raw_data_array)
                    print self.histograming.get_occupancy().shape
                    return self.interpreter.get_hits()
            except AttributeError:  # happens if first data is not meta data
                return None
        return jsonapi.dumps(self.meta_data)

    def analyze_raw_data(self, raw_data):
        self.interpreter.interpret_raw_data(raw_data)
        self.histograming.add_hits(self.interpreter.get_hits())
