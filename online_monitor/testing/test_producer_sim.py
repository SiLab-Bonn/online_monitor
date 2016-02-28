''' Script to check the producer simulation of the online monitor.
'''

import unittest
import yaml
import subprocess
import time
import os
import zmq
import psutil

import online_monitor
from online_monitor.utils import settings

# Get package path
package_path = os.path.dirname(online_monitor.__file__)  # Get the absoulte path of the online_monitor installation

# Set the producer script path
producer_sim_script_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/online_monitor/start_producer_sim.py'))


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_producer_config_yaml(n_producer):
    conf, devices = {}, {}
    for index in range(n_producer):
        devices['DAQ%s' % index] = {
            'backend': 'tcp://127.0.0.1:55%02d' % index,
            'kind': 'example_producer_sim',
            'delay': 0.02
        }
    conf['producer_sim'] = devices
    return yaml.dump(conf, default_flow_style=False)


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def run_script_in_shell(script, arguments):
    return subprocess.Popen("python %s %s" % (script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the config file path to the test folder, otherwise they are created where nosetests are called
        cls.config_path = os.path.join(os.path.dirname(__file__), 'tmp_cfg_5_producer.yml')
        
        # Add examples folder to entity search paths
        settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/producer_sim')))
        settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/converter')))
        settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/receiver')))
        
        with open(cls.config_path, 'w') as outfile:  # 10 forwarder converters connected in a chain
            config_file = create_producer_config_yaml(5)
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove(cls.config_path)

    def test_converter_communication(self):  # start 5 producer and check if they send data, then check shutdows
        # 5 test producers
        producer_process = run_script_in_shell(producer_sim_script_path, self.config_path)
        time.sleep(1.5)  # 10 converter in 10 processes + ZMQ thread take time to start up
        have_data = []
        context = zmq.Context()
        for index in range(5):
            receiver = context.socket(zmq.SUB)  # subscriber to the last transveiver in the chain
            receiver.connect(r'tcp://127.0.0.1:55%02d' % index,)
            receiver.setsockopt_string(zmq.SUBSCRIBE, u'')  # do not filter any data
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
        time.sleep(2)
        self.assertTrue(all(have_data), 'Did not receive any data')
        self.assertNotEqual(producer_process.poll(), None)

if __name__ == '__main__':
    producer_sim_script_path = r'../start_producer_sim.py'
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
