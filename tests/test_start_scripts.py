''' Script to check the online monitor.
'''

import sys
import unittest
import yaml
import subprocess
import time
import os
import psutil
from PyQt4.QtGui import QApplication

from online_monitor.utils import settings


# creates a yaml config
def create_config_yaml():
    conf = {}
    # Add producer
    devices = {}
    devices['DAQ0'] = {'backend': 'tcp://127.0.0.1:6500',
                       'kind': 'example_producer_sim',
                       'delay': 1}
    devices['DAQ1'] = {'backend': 'tcp://127.0.0.1:6501',
                       'kind': 'example_producer_sim',
                       'delay': 1}
    conf['producer_sim'] = devices
    # Add converter
    devices = {}
    devices['DUT0'] = {
        'kind': 'example_converter',
        'frontend': 'tcp://127.0.0.1:6500',
        'backend': 'tcp://127.0.0.1:6600',
        'max_cpu_load': None,
        'threshold': 8
    }
    devices['DUT1'] = {
        'kind': 'forwarder',
        'frontend': 'tcp://127.0.0.1:6600',
        'backend': 'tcp://127.0.0.1:6601',
        'max_cpu_load': None
    }
    conf['converter'] = devices
    # Add receiver
    devices = {}
    devices['DUT0'] = {
        'kind': 'example_receiver',
        'frontend': 'tcp://127.0.0.1:6600'
    }
    devices['DUT1'] = {
        'kind': 'example_receiver',
        'frontend': 'tcp://127.0.0.1:6600'
    }
    conf['receiver'] = devices
    return yaml.dump(conf, default_flow_style=False)


# kill process by id, including subprocesses; works for linux and windows
def kill(proc):
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def run_script_in_shell(script, arguments, command=None):
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestStartScripts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tmp_cfg_2.yml', 'w') as outfile:
            config_file = create_config_yaml()
            outfile.write(config_file)
        # linux CIs run usually headless, thus virtual x server is needed for gui testing
        if os.name != 'nt':
            from xvfbwrapper import Xvfb
            cls.vdisplay = Xvfb()
            cls.vdisplay.start()

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_2.yml')
        time.sleep(1)

#     def test_start_converter(self):
#         converter_process = run_script_in_shell('', 'tmp_cfg_2.yml', 'start_converter')
#         time.sleep(0.5)
#         kill(converter_process)
#         time.sleep(0.5)
#         self.assertNotEqual(converter_process.poll(), None)
 
#     def test_start_producer_sim(self):
#         producer_sim_process = run_script_in_shell('', 'tmp_cfg_2.yml', 'start_producer_sim')
#         time.sleep(0.5)
#         kill(producer_sim_process)
#         time.sleep(0.5)
#         self.assertNotEqual(producer_sim_process.poll(), None)

    def test_start_online_monitor(self):
        online_monitor_process = run_script_in_shell('', 'tmp_cfg_2.yml', 'start_online_monitor')
        time.sleep(1)
        kill(online_monitor_process)
        time.sleep(1)
        self.assertNotEqual(online_monitor_process.poll(), None)
 
#     def test_online_monitor(self):
#         online_monitor_process = run_script_in_shell('', 'tmp_cfg_2.yml', 'online_monitor')
#         time.sleep(0.5)
#         kill(online_monitor_process)
#         time.sleep(0.5)
#         self.assertNotEqual(online_monitor_process.poll(), None)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStartScripts)
    unittest.TextTestRunner(verbosity=2).run(suite)
