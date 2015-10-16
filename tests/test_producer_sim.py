''' Script to check the producer simulation of the online monitor.
'''

import unittest
import yaml
import subprocess
import time
import os
import zmq
import psutil

from online_monitor.utils import settings


producer_sim_script_path = r'online_monitor/utils/producer_sim.py'


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_producer_config_yaml(n_producer):
    conf, devices = {}, {}
    for index in range(n_producer):
        devices['DAQ%s' % index] = {
            'send_address': 'tcp://127.0.0.1:55%02d' % index,
        }
    conf['producer'] = devices
    return yaml.dump(conf, default_flow_style=False)


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def get_python_processes():  # return the number of python processes
    n_python = 0
    for proc in psutil.process_iter():
        try:
            if 'python' in proc.name():
                n_python += 1
        except psutil.AccessDenied:  # pragma: no cover
            pass
    return n_python


def run_script_in_shell(script, arguments):
    return subprocess.Popen("python %s %s" % (script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.add_converter_path(r'examples/converter')
        settings.add_receiver_path(r'examples/receiver')
        with open('tmp_cfg_5_producer.yml', 'w') as outfile:  # 10 forwarder converters connected in a chain
            config_file = create_producer_config_yaml(5)
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_5_producer.yml')

    def test_converter_communication(self):  # start 5 producer and check if they send data, then check shutdows
        n_python = get_python_processes()  # python instances before converter start
        # Forward receivers with single in/out
        producer_process = run_script_in_shell(producer_sim_script_path, 'tmp_cfg_5_producer.yml')
        time.sleep(1.5)  # 10 converter in 10 processes + ZMQ thread take time to start up
        have_data = []
        context = zmq.Context()
        for index in range(5):
            receiver = context.socket(zmq.SUB)  # subscriber to the last transveiver in the chain
            receiver.connect(r'tcp://127.0.0.1:55%02d' % index,)
            receiver.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
            time.sleep(0.5)
            try:
                receiver.recv_json(flags=zmq.NOBLOCK)
                have_data.append(True)
            except zmq.Again:
                have_data.append(False)
            receiver.close()

        kill(producer_process)
        time.sleep(1)
        context.term()
        n_python_2 = get_python_processes()  # python instances after converter stop
        self.assertTrue(all(have_data), 'Did not receive any data')
        self.assertEqual(n_python, n_python_2)  # check if all processes are closed, Linux has extra python process (why?)

if __name__ == '__main__':
    producer_sim_script_path = r'../online_monitor/utils/producer_sim.py'
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
