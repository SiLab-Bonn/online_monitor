''' Script to check the online converter of the online monitor.
'''

import unittest
import yaml
import subprocess
import os
import numpy as np
import json

from testfixtures import log_capture

import psutil

from online_monitor import utils
from online_monitor.converter.forwarder import Forwarder


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


def kill(proc_pid):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def get_python_processes():  # return the number of python processes
    n_python = 0
    for proc in psutil.process_iter():
        try:
            if 'python' in proc.name():
                n_python += 1
        except psutil.AccessDenied:
            pass
    return n_python


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=True if os.name == 'nt' else False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.configuration = create_forwarder_config_yaml(10)
        with open('tmp_cfg_10_converter.yml', 'w') as outfile:
            outfile.write(cls.configuration)
        cls.configuration = yaml.load(cls.configuration)
        cls.config_file = 'tmp_cfg_10_converter.yml'

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_10_converter.yml')

    @log_capture()  # to be able to inspect logging messages
    def test_argument_parser(self, log):
        # Function utils.parse_arguments
        with self.assertRaises(SystemExit):  # no config file specified; thus expect parser error
            utils.parse_arguments()
        # Function utils.parse_args
        arguments = utils.parse_args(['configfile.yaml', '-l DEBUG'])
        self.assertEqual(arguments.config_file, 'configfile.yaml', 'The non positional argument is parsed wrong')
        self.assertTrue('DEBUG' in arguments.log, 'The logging argument parse fails')
        # Function parse_config_file
        utils.parse_config_file('Does_not_exist')  # open not existin file
        configuration = utils.parse_config_file(self.config_file)  # parse config and check result
        self.assertEqual(configuration, self.configuration)
        utils.parse_config_file(self.config_file, expect_receiver=True)
        log.check(('root', 'ERROR', 'Cannot open configuration file'),  # check the logging output
                  ('root', 'WARNING', 'No receiver specified, thus no data can be plotted. Change tmp_cfg_10_converter.yml!'))

    @log_capture()
    def test_numpy_serializer(self):
        data = {'array': np.ones((100, 101))}
        data_serialized = json.dumps(data, cls=utils.NumpyEncoder)
        data_deserialized = json.loads(data_serialized, object_hook=utils.json_numpy_obj_hook)
        self.assertTrue((data['array'] == data_deserialized['array']).all())

    def test_factory(self):
        receiver = utils.factory('online_monitor.converter.forwarder', base_class_type=Forwarder, *(), **{'receive_address': '0',
                                                                                                          'send_address': '1',
                                                                                                          'data_type': 'forwarder',
                                                                                                          'name': 'DUT'})
        self.assertEqual(receiver.__str__(), '<Forwarder(DUT, initial)>')
        with self.assertRaises(ImportError):
            utils.factory('online_monitor.converter.notexisting', base_class_type=Forwarder, *(), **{})

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)