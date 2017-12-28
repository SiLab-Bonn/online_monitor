from online_monitor.converter.transceiver import Transceiver


class Forwarder(Transceiver):

    def interpret_data(self, data):
        # A forwarder just forwards data; no interpretation
        return [actual_data[1] for actual_data in data]
