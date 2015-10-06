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


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def get_python_processes():
    n_python = 0
    for proc in psutil.process_iter():
        try:
            if 'python' in proc.name():
                n_python += 1
        except psutil.AccessDenied:
            pass
    return n_python


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_file = create_forwarder_config_yaml(10)
        with open('tmp_cfg_10_converter.yml', 'w') as outfile:
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_10_converter.yml')

    def test_converter_communication(self):  # start 10 forwarder in a chain and do "whisper down the lane"
        n_python = get_python_processes()  # python instances before converter start
        converter_manager_process = subprocess.Popen(["python", r"../online_monitor/start_converter.py", 'tmp_cfg_10_converter.yml'], shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        time.sleep(1.0)  # 10 converter in 10 processes + ZMQ thread take time to start up
        no_data = True  # flag set to False if data is received
        context = zmq.Context()
        # Socket facing last converter
        sender = context.socket(zmq.PUB)  # publish data where first transveiver listens to
        sender.bind(r'tcp://127.0.0.1:5500')
        receiver = context.socket(zmq.SUB)  # subscriber to the last transveiver in the chain
        receiver.connect(r'tcp://127.0.0.1:5510')
        receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        time.sleep(0.5)
        msg = 'This is a test message'
        sender.send_json(msg)
        time.sleep(0.5)
        try:
            ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
            no_data = False
            self.assertEqual(msg, ret_msg)
        except zmq.Again:
            pass

        kill(converter_manager_process.pid)
        time.sleep(0.1)
        n_python_2 = get_python_processes()  # python instances after converter stop
        self.assertFalse(no_data, 'Did not receive any data')
        self.assertEqual(n_python, n_python_2)  # check if all processes are closed


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
