''' Script to check the online monitor.
'''

import sys
import unittest
import yaml
import subprocess
import time
import os
import zmq
import psutil
import signal
from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt

from online_monitor import OnlineMonitor

producer_path = r'online_monitor/utils/producer_sim.py'
converter_manager_path = r'online_monitor/start_converter.py'

app = QApplication(sys.argv)


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_config_yaml():
    conf = {}
    # Add producer
    devices = {}
    devices['DAQ0'] = {'send_address': 'tcp://127.0.0.1:5500'}
    devices['DAQ1'] = {'send_address': 'tcp://127.0.0.1:5501'}
    conf['producer'] = devices
    # Add converter
    devices = {}
    devices['DUT0'] = {
        'data_type': 'forwarder',
        'receive_address': 'tcp://127.0.0.1:5500',
        'send_address': 'tcp://127.0.0.1:5600',
        'max_cpu_load': None
    }
    devices['DUT1'] = {
        'data_type': 'forwarder',
        'receive_address': 'tcp://127.0.0.1:5501',
        'send_address': 'tcp://127.0.0.1:5601',
        'max_cpu_load': None
    }
    conf['converter'] = devices
    # Add receiver
    devices = {}
    devices['DUT0'] = {
        'data_type': 'example_receiver',
        'receive_address': 'tcp://127.0.0.1:5600'
    }
    devices['DUT1'] = {
        'data_type': 'example_receiver',
        'receive_address': 'tcp://127.0.0.1:5601'
    }
    conf['receiver'] = devices
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
        except psutil.AccessDenied:
            pass
    return n_python


def run_script_in_shell(script, arguments):
    return subprocess.Popen("python %s %s" % (script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestOnlineMonitor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tmp_cfg.yml', 'w') as outfile:
            config_file = create_config_yaml()
            outfile.write(config_file)
        # Start the simulation producer to create some fake data
        cls.producer_process = run_script_in_shell(producer_path, 'tmp_cfg.yml')
        # Start converter
        cls.converter_manager_process = run_script_in_shell(converter_manager_path, 'tmp_cfg.yml')
        # Create Gui
        cls.online_monitor = OnlineMonitor.OnlineMonitorApplication('tmp_cfg.yml')
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):  # remove created files
        kill(cls.producer_process)
        kill(cls.converter_manager_process)
        os.remove('tmp_cfg.yml')

    def test_receiver(self):
        self.assertEqual(len(self.online_monitor.receivers), 2, 'Number of receivers wrong')
        for receiver in self.online_monitor.receivers:
            print receiver.position_img.getHistogram()

    def test_ui(self):  # start 10 forwarder in a chain and do "whisper down the lane"
        self.assertEqual(self.online_monitor.tab_widget.count(), 3, 'Number of tab widgets wrong')  # 2 receiver + status widget expected
        self.assertEqual(self.online_monitor.tab_widget.currentIndex(), 0)

if __name__ == '__main__':
    producer_path = r'../online_monitor/utils/producer_sim.py'
    converter_manager_path = r'../online_monitor/start_converter.py'
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOnlineMonitor)
    unittest.TextTestRunner(verbosity=2).run(suite)
