from transceiver import Transceiver


class Forwarder(Transceiver):

    def interpret_data(self, data):
        return data
