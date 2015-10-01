from transceiver import Transceiver


class Forwarder(Transceiver):

    def setup_interpretation(self):
        pass

    def interpret_data(self, data):
        return data
