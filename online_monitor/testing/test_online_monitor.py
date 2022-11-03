''' Script to check the online monitor.
'''

import sys
import unittest
import yaml
import subprocess
import time
import os
import psutil
from PyQt5 import QtWidgets

import online_monitor
from online_monitor import OnlineMonitor

# Get package path
# Get the absoulte path of the online_monitor installation
package_path = os.path.dirname(online_monitor.__file__)

# Set the script paths
converter_manager_path = os.path.join(package_path, 'start_converter.py')
producer_manager_path = os.path.join(package_path, 'start_producer_sim.py')


# creates a yaml config describing n_converter of type forwarder that are
# all connection to each other
def create_config_yaml():
    conf = {}
    # Add producer
    devices = {}
    devices['DAQ0'] = {'backend': 'tcp://127.0.0.1:6500',
                       'kind': 'example_producer_sim',
                       'delay': 0.02}
    devices['DAQ1'] = {'backend': 'tcp://127.0.0.1:6501',
                       'kind': 'example_producer_sim',
                       'delay': 0.02}
    conf['producer_sim'] = devices
    # Add converter
    devices = {}
    devices['DUT0'] = {
        'kind': 'example_converter',
        'frontend': 'tcp://127.0.0.1:6500',
        'backend': 'tcp://127.0.0.1:6600',
        'threshold': 8
    }
    devices['DUT1'] = {
        'kind': 'forwarder',
        'frontend': 'tcp://127.0.0.1:6600',
        'backend': 'tcp://127.0.0.1:6601',
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
        'frontend': 'tcp://127.0.0.1:6601'
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
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments),
                            shell=True,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestOnlineMonitor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the config file path to the test folder, otherwise they are
        # created where nosetests are called
        cls.config_path = os.path.join(
            os.path.dirname(__file__), 'tmp_cfg.yml')

        with open(cls.config_path, 'w') as outfile:
            config_file = create_config_yaml()
            outfile.write(config_file)
        # linux CI travis runs headless, thus virtual x server is needed for
        # Start the simulation producer to create some fake data
        cls.producer_process = run_script_in_shell(
            producer_manager_path, cls.config_path)
        # Start converter
        cls.converter_manager_process = run_script_in_shell(
            converter_manager_path, cls.config_path)
        # Create Gui
        time.sleep(2)
        cls.app = QtWidgets.QApplication(sys.argv)
        cls.online_monitor = OnlineMonitor.OnlineMonitorApplication(
            cls.config_path)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):  # remove created files
        time.sleep(1)
        kill(cls.producer_process)
        kill(cls.converter_manager_process)
        time.sleep(1)
        os.remove(cls.config_path)
        cls.online_monitor.close()
        time.sleep(1)

    def test_receiver(self):
        self.app.processEvents()
        self.assertEqual(len(self.online_monitor.receivers),
                         2, 'Number of frontends wrong')
        self.app.processEvents()  # clear event queue
        # activate status widget, no data should be received
        self.online_monitor.tab_widget.setCurrentIndex(0)
        # event loop does not run in testss, thus we have to trigger the event
        # queue manually
        self.app.processEvents()
        time.sleep(3)
        self.app.processEvents()
        time.sleep(0.2)
        data_received_0 = []
        self.app.processEvents()
        for receiver in self.online_monitor.receivers:
            data_received_0.append(receiver.position_img.getHistogram())
        self.online_monitor.tab_widget.setCurrentIndex(1)
        self.app.processEvents()
        time.sleep(3)
        self.app.processEvents()
        time.sleep(0.2)
        data_received_1 = []
        for receiver in self.online_monitor.receivers:
            data_received_1.append(receiver.position_img.getHistogram(step=1))
        # activate DUT widget, receiver 2 should show data
        self.online_monitor.tab_widget.setCurrentIndex(2)
        self.app.processEvents()
        time.sleep(3)
        self.app.processEvents()
        time.sleep(0.2)
        data_received_2 = []
        for receiver in self.online_monitor.receivers:
            # Step has to be given to preven issue
            # https://github.com/pyqtgraph/pyqtgraph/issues/469
            data_received_2.append(receiver.position_img.getHistogram(step=1))

        self.assertListEqual(data_received_0, [(None, None), (None, None)])
        self.assertTrue(data_received_1[0][0] is not None)
        self.assertTupleEqual(data_received_0[1], (None, None))
        self.assertTrue(data_received_2[1][0] is not None)

    # start 10 forwarder in a chain and do "whisper down the lane"
    def test_ui(self):
        self.assertEqual(self.online_monitor.tab_widget.count(),
                         3, 'Number of tab widgets wrong')  # 2 receiver + status widget expected


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOnlineMonitor)
    unittest.TextTestRunner(verbosity=2).run(suite)
