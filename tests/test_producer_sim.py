''' Script to check the producer simulation of the online monitor.
'''

import unittest
import yaml
import subprocess
import time
import os
import zmq
import psutil

producer_sim_script_path = r'online_monitor/start_producer_sim.py'


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_producer_config_yaml(n_producer):
    conf, devices = {}, {}
    for index in range(n_producer):
        devices['DAQ%s' % index] = {
            'send_address': 'tcp://127.0.0.1:55%02d' % index,
            'data_type': 'example_producer_sim'
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
        with open('tmp_cfg_5_producer.yml', 'w') as outfile:  # 10 forwarder converters connected in a chain
            config_file = create_producer_config_yaml(5)
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_5_producer.yml')

    def test_converter_communication(self):  # start 5 producer and check if they send data, then check shutdows
        # 5 test producers
        producer_process = run_script_in_shell(producer_sim_script_path, 'tmp_cfg_5_producer.yml')
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
    producer_sim_script_path = r'../online_monitor/start_producer_sim.py'
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
