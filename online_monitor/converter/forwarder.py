from online_monitor.converter.transceiver import Transceiver


class Forwarder(Transceiver):

    def interpret_data(self, data):
        return data  # a forwarder just forwards data; no interpretation
