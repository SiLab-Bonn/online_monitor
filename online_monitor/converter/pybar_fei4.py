from transceiver import Transceiver


from pybar.analysis.RawDataConverter.data_interpreter import PyDataInterpreter
from pybar.analysis.RawDataConverter.data_histograming import PyDataHistograming


class PybarFEI4(Transceiver):

    def interpret_data(self, data):
        print('RUN PybarFEI4 INTERPRET')
        return data
