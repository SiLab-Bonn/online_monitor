''' Script to check the online converter of the online monitor.
'''

import unittest
import yaml
import subprocess
import time
import os
import signal
import zmq

import psutil

from online_monitor.converter.converter_manager import ConverterManager


# creates a yaml config describing n_converter of type forwarder
def create_config_yaml(n_converter):
    conf, devices = {}, {}
    for index in range(n_converter):
        devices['DUT%s' % index] = {
            'data_type': 'forwarder',
            'receive_address': 'tcp://127.0.0.1:55%02d' % index,
            'send_address': 'tcp://127.0.0.1:55%02d' % (index + 1)
        }
    conf['converter'] = devices
    return yaml.dump(conf, default_flow_style=True)


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_file = create_config_yaml(2)
        with open('tmp_cfg_10_converter.yml', 'w') as outfile:
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        pass

    def test_converter_communication(self):  # start 10 forwarder in a chain a do "whisper down the lane"
        n_python = sum(1 for i in psutil.process_iter() if 'python' in i.name())  # number of python instances before multi threading
        converter_manager_process = subprocess.Popen(["python", r"../online_monitor/start_converter.py", 'tmp_cfg_10_converter.yml'], shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        no_data = True
        context = zmq.Context()
        # Socket facing last converter
        sender = context.socket(zmq.PUB)
        sender.bind(r'tcp://127.0.0.1:5500')
        receiver = context.socket(zmq.SUB)  # subscriber
        receiver.connect(r'tcp://127.0.0.1:5502')
        receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        time.sleep(1.1)
        msg = 'This is a test message'
        sender.send_json(msg)
        time.sleep(1.1)
        try:
            ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
            no_data = False
            self.assertEqual(msg, ret_msg)
        except zmq.Again:
            pass

        self.assertFalse(no_data, 'Did not receive any data') 
#         os.kill(converter_manager_process.pid, signal.SIGTERM)
        kill(converter_manager_process.pid)
        n_python_2 = sum(1 for i in psutil.process_iter() if 'python' in i.name())
        self.assertEqual(n_python, n_python_2)  # check if all processes are closed


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
