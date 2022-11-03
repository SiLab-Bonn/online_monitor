''' Script to check the settings class of the online monitor.
Since the settings change after the online monitor is used, this
unittests only works on a new installation. The OnlineMonitor.ini
should be untouched.
'''

import unittest
import yaml
import os

from online_monitor.utils import settings


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_forwarder_config_yaml(n_converter):
    conf, devices = {}, {}
    for index in range(n_converter):
        devices['DUT%s' % index] = {
            'kind': 'forwarder',
            'frontend': 'tcp://127.0.0.1:55%02d' % index,
            'backend': 'tcp://127.0.0.1:55%02d' % (index + 1)
        }
    conf['converter'] = devices
    return yaml.dump(conf, default_flow_style=False)


class TestSettings(unittest.TestCase):

    def test_entities_settings(self):
        settings.add_converter_path(r'C:\\test\\converter\\path')
        settings.add_receiver_path(r'/home/receiver/path')
        settings.add_producer_sim_path(r'test/producer_sim/path')

        self.assertTrue(r'C:\\test\\converter\\path' in settings.get_converter_path())
        self.assertTrue(r'/home/receiver/path' in settings.get_receiver_path())
        self.assertTrue(r'test/producer_sim/path' in settings.get_producer_sim_path())

        settings.delete_converter_path(r'C:\\test\\converter\\path')
        settings.delete_receiver_path(r'/home/receiver/path')
        settings.delete_producer_sim_path(r'test/producer_sim/path')

        self.assertFalse(r'C:\\test\\converter\\path' in settings.get_converter_path())
        self.assertFalse(r'/home/receiver/path' in settings.get_receiver_path())
        self.assertFalse(r'test/producer_sim/path' in settings.get_producer_sim_path())

    @unittest.skipIf(os.name == 'nt' or not os.environ.get("CI"), "This tests is only true on virtual linux x-server systems. Otherwise result value depends on test environment.")
    def test_interface_settings(self):
        self.assertTupleEqual(settings.get_window_geometry(), (100, 100, 1024, 768), 'This can fail if you started the online monitor once and changed the windows size')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSettings)
    unittest.TextTestRunner(verbosity=2).run(suite)
