''' Script to check the online converter of the online monitor.
'''

import unittest
import yaml
import os
import numpy as np
import json

from testfixtures import log_capture

import online_monitor
from online_monitor.utils import utils, settings, producer_sim
from online_monitor.converter.transceiver import Transceiver
from online_monitor.converter.forwarder import Forwarder
from online_monitor.receiver.receiver import Receiver


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


class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the config file path to the test folder, otherwise they are created where nosetests are called
        cls.config_path = os.path.join(os.path.dirname(__file__), 'tmp_cfg_10_converter.yml')
        # Add examples folder to entity search paths
        package_path = os.path.dirname(online_monitor.__file__)  # Get the absoulte path of the online_monitor installation
        settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/producer_sim')))
        settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/converter')))
        settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/receiver')))

        cls.configuration = create_forwarder_config_yaml(10)
        with open(cls.config_path, 'w') as outfile:
            outfile.write(cls.configuration)
        cls.configuration = yaml.load(cls.configuration)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove(cls.config_path)

    @log_capture()  # to be able to inspect logging messages
    def test_argument_parser(self, log):
        # FIXME: SystemExit not reliably raised if nosetest is started from console using installed package
        # Function utils.parse_arguments
        # with self.assertRaises(SystemExit):  # no config file specified; thus expect parser error raising SystemExit; this does not work within nosetests
        #             utils.parse_arguments()
        # Function utils.parse_args
        arguments = utils.parse_args(['configfile.yaml', '-l DEBUG'])
        self.assertEqual(arguments.config_file, 'configfile.yaml', 'The non positional argument is parsed wrong')
        self.assertTrue('DEBUG' in arguments.log, 'The logging argument parse fails')
        # Function parse_config_file
        with self.assertRaises(IOError):
            utils.parse_config_file('Does_not_exist')  # open not existin file
        configuration = utils.parse_config_file(self.config_path)  # parse config and check result
        self.assertEqual(configuration, self.configuration)
        utils.parse_config_file(self.config_path, expect_receiver=True)
        log.check(('root', 'WARNING', 'No receiver specified, thus no data can be plotted. Change %s!' % self.config_path))  # check the logging output

    @log_capture()
    def test_numpy_serializer(self):
        # C_CONTIGUOUS : True
        data = {'array': np.ones((100, 101))}
        data_serialized = json.dumps(data, cls=utils.NumpyEncoder)
        data_deserialized = json.loads(data_serialized, object_hook=utils.json_numpy_obj_hook)
        self.assertTrue((data['array'] == data_deserialized['array']).all())
        # C_CONTIGUOUS : False
        data = {'array': np.ones((100, 101)).T}
        data_serialized = json.dumps(data, cls=utils.NumpyEncoder)
        data_deserialized = json.loads(data_serialized, object_hook=utils.json_numpy_obj_hook)
        self.assertTrue((data['array'] == data_deserialized['array']).all())
        # No valid numpy array
        data = {'array', (1, 2, 3)}
        with self.assertRaises(TypeError):
            json.dumps(data, cls=utils.NumpyEncoder)

        # Check for recarray
        data = {'array': np.ones((100, ), dtype=[('event_number', '<i8'),
                                                 ('trigger_number', '<u4')])}
        data_serialized = json.dumps(data, cls=utils.NumpyEncoder)
        data_deserialized = json.loads(data_serialized, object_hook=utils.json_numpy_obj_hook)
        self.assertTrue((data['array'] == data_deserialized['array']).all())

    def test_entity_loader(self):
        utils.load_converter('forwarder', base_class_type=Transceiver, *(), **{'frontend': '0',
                                                                               'backend': '1',
                                                                               'kind': 'forwarder',
                                                                               'name': 'DUT'})
        utils.load_converter('example_converter', base_class_type=Transceiver, *(), **{'frontend': '0',
                                                                                       'backend': '1',
                                                                                       'kind': 'example_converter',
                                                                                       'name': 'DUT'})
        utils.load_receiver('example_receiver', base_class_type=Receiver, *(), **{'frontend': '0',
                                                                                  'kind': 'example_receiver',
                                                                                  'name': 'DUT'})
        utils.load_producer_sim('example_producer_sim', base_class_type=producer_sim.ProducerSim, *(), **{'backend': '0',
                                                                                                          'kind': 'example_producer_sim',
                                                                                                          'name': 'DUT'})

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
