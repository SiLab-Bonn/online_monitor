''' Script to check the settings class of the online monitor.
Since the settings change after the online monitor is used, this
unittests only works on a new installation. The OnlineMonitor.ini
should be untouched.
'''

import unittest
import yaml

from online_monitor.utils import settings


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_forwarder_config_yaml(n_converter):
    conf, devices = {}, {}
    for index in range(n_converter):
        devices['DUT%s' % index] = {
            'data_type': 'forwarder',
            'receive_address': 'tcp://127.0.0.1:55%02d' % index,
            'send_address': 'tcp://127.0.0.1:55%02d' % (index + 1)
        }
    conf['converter'] = devices
    return yaml.dump(conf, default_flow_style=False)


class TestSettings(unittest.TestCase):

    def test_settings_set(self):
        self.assertListEqual(settings.get_receiver_path(), ['online_monitor.receiver'])
        self.assertListEqual(settings.get_converter_path(), ['online_monitor.converter'])

        settings.add_converter_path(r'test/converter/path')
        settings.add_receiver_path(r'test/receiver/path')
        settings.add_receiver_path(r'test/receiver/path')

        self.assertTrue(r'test/converter/path' in settings.get_converter_path())
        self.assertTrue(r'test/receiver/path' in settings.get_receiver_path())

        settings.delete_converter_path(r'test/converter/path')
        settings.delete_receiver_path(r'test/receiver/path')

        self.assertFalse(r'test/converter/path' in settings.get_converter_path())
        self.assertFalse(r'test/receiver/path' in settings.get_receiver_path())

        self.assertTupleEqual(settings.get_window_geometry(), (100, 100, 1024, 768), 'This can fail if you started the online monitor once and changed the windows size')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSettings)
    unittest.TextTestRunner(verbosity=2).run(suite)
