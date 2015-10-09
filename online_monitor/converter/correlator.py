from online_monitor.converter.transceiver import Transceiver


class Correlator(Transceiver):
    def __init__(self, *args, **kwargs):
        Transceiver.__init__(self, *args, **kwargs)
        if self.n_receivers < 2:
            raise ValueError('A correlator needs at least two receivers! Specify the receive adresses in the config file.')

    def setup_interpretation(self):
        pass

    def interpret_data(self, data):
        return data
