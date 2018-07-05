''' Script to check the online converter of the online monitor.
'''

import unittest
import yaml
import subprocess
import time
import os
import zmq
import psutil
import signal

import online_monitor

# Get the absoulte path of the online_monitor installation
package_path = os.path.dirname(online_monitor.__file__)

# Set the converter script path
converter_script_path = os.path.join(package_path, 'start_converter.py')


# Creates a yaml config describing n_converter of type forwarder that are
# all connection to each other
def create_forwarder_config_yaml(n_converter, bidirectional=False, one_io=True):
    conf, devices = {}, {}
    if one_io:  # just one incoming outgoing connection
        for index in range(n_converter):
            devices['DUT%s' % index] = {
                'kind': 'forwarder',
                'frontend': 'tcp://127.0.0.1:55%02d' % index,
                'backend': 'tcp://127.0.0.1:55%02d' % (index + 1),
                'connection': 'bidirectional' if bidirectional else 'unidirectional'
            }
    else:  # 2 / 2 incoming/outgoing connections
        for index in range(n_converter):
            devices['DUT%s' % index] = {
                'kind': 'forwarder',
                'frontend': ['tcp://127.0.0.1:55%02d' % index,
                             'tcp://127.0.0.1:56%02d' % index],
                'backend': ['tcp://127.0.0.1:55%02d' % (index + 1),
                            'tcp://127.0.0.1:56%02d' % (index + 1)],
                'connection': 'bidirectional' if bidirectional else 'unidirectional'
            }
    conf['converter'] = devices
    return yaml.dump(conf, default_flow_style=False)


# kill process by id, including subprocesses; works for linux and windows
def kill(proc):
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def run_script_in_shell(script, arguments):
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        creationflags = 0
    return subprocess.Popen("python %s %s" % (script, arguments), shell=True,
                            creationflags=creationflags)


def run_script_in_process(script, arguments):
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        creationflags = 0
    return subprocess.Popen(["python", script, arguments], shell=False,
                            creationflags=creationflags)


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the config file path to the test folder, otherwise they are
        # created where nosetests are called
        cls.configs_path = [os.path.join(os.path.dirname(__file__), path) for path in ('tmp_cfg_10_converter.yml',
                                                                                       'tmp_cfg_3_converter_multi.yml',
                                                                                       'tmp_cfg_3_converter_multi_bi.yml')]

        # 10 forwarder converters connected in a chain
        with open(cls.configs_path[0], 'w') as outfile:
            config_file = create_forwarder_config_yaml(10)
            outfile.write(config_file)
        # 3 forwarder converters with 2 in / 2 out connections, connected in a
        # chain
        with open(cls.configs_path[1], 'w') as outfile:
            config_file = create_forwarder_config_yaml(3, one_io=False)
            outfile.write(config_file)
        # 3 forwarder converters with 2 in / 2 out connections, connected in a
        # chain
        with open(cls.configs_path[2], 'w') as outfile:
            config_file = create_forwarder_config_yaml(
                3, one_io=False, bidirectional=True)
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        for config_path in cls.configs_path:
            os.remove(config_path)

    def test_converter_communication(self):
        ''' Start 10 forwarder in a chain and do "whisper down the lane '''
        # Forward receivers with single in/out
        converter_manager_process = run_script_in_shell(
            converter_script_path, self.configs_path[0])
        # 10 converter in 10 processes + ZMQ thread take time to start up
        time.sleep(4.5)
        no_data = True  # flag set to False if data is received
        context = zmq.Context()
        # Socket facing last converter
        # publish data where first transveiver listens to
        sender = context.socket(zmq.PUB)
        sender.bind(r'tcp://127.0.0.1:5500')
        # subscriber to the last transveiver in the chain
        receiver = context.socket(zmq.SUB)
        receiver.connect(r'tcp://127.0.0.1:5510')
        # do not filter any data
        receiver.setsockopt_string(zmq.SUBSCRIBE, u'')
        time.sleep(4.5)
        msg = 'This is a test message'
        sender.send_json(msg)
        time.sleep(4.5)
        try:
            ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
            no_data = False
            self.assertEqual(msg, ret_msg)
        except zmq.Again:  # pragma: no cover
            pass

        kill(converter_manager_process)
        sender.close()
        receiver.close()
        context.term()
        time.sleep(0.5)
        self.assertFalse(no_data, 'Did not receive any data')
        self.assertNotEqual(converter_manager_process.poll(), None)

    def test_converter_communication_2(self):
        ''' Start 3 forwarder in a chain with 2 i/o each and do "whisper down the lane" '''
        # Forward receivers with 2 in/out
        converter_manager_process = run_script_in_shell(
            converter_script_path, self.configs_path[1])
        # 10 converter in 10 processes + ZMQ thread take time to start up
        time.sleep(4.5)
        context = zmq.Context()
        # Sockets facing last converter inputs
        # publish data where first transveiver listens to
        sender = context.socket(zmq.PUB)
        sender.bind(r'tcp://127.0.0.1:5500')
        # publish data where first transveiver 2nd input listens to
        sender_2 = context.socket(zmq.PUB)
        sender_2.bind(r'tcp://127.0.0.1:5600')
        # subscriber to the last transveiver in the chain
        receiver = context.socket(zmq.SUB)
        receiver.connect(r'tcp://127.0.0.1:5503')
        receiver.setsockopt_string(zmq.SUBSCRIBE, u'')
        # subscriber to the last transveiver in the chain
        receiver_2 = context.socket(zmq.SUB)
        receiver_2.connect(r'tcp://127.0.0.1:5603')
        # do not filter any data
        receiver_2.setsockopt_string(zmq.SUBSCRIBE, u'')
        time.sleep(4.5)
        msg = 'This is a test message'
        msg_2 = 'This is another test message'

        sender.send_json(msg)
        time.sleep(1.5)
        no_data = []
        # forwarder forwards all inputs to all outputs; for 3 forwarder in a
        # chain with 2 i/o each you expect 2**3 times the input message
        for _ in range(4):
            # flag set to False if data is received
            no_data_out_1, no_data_out_2 = True, True
            try:
                ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
                no_data_out_1 = False
                self.assertEqual(msg, ret_msg)
            except zmq.Again:
                pass
            try:
                ret_msg = receiver_2.recv_json(flags=zmq.NOBLOCK)
                no_data_out_2 = False
                self.assertEqual(msg, ret_msg)
            except zmq.Again:
                pass
            no_data.append(no_data_out_1)
            no_data.append(no_data_out_2)

        with self.assertRaises(zmq.Again):  # should have no data
            ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
        with self.assertRaises(zmq.Again):  # should have no data
            ret_msg = receiver_2.recv_json(flags=zmq.NOBLOCK)

        sender_2.send_json(msg_2)
        time.sleep(4.5)
        no_data_2 = []
        for _ in range(4):
            # flag set to False if data is received
            no_data_out_1, no_data_out_2 = True, True
            try:
                ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
                no_data_out_1 = False
                self.assertEqual(msg_2, ret_msg)
            except zmq.Again:  # pragma: no cover
                pass
            try:
                ret_msg = receiver_2.recv_json(flags=zmq.NOBLOCK)
                no_data_out_2 = False
                self.assertEqual(msg_2, ret_msg)
            except zmq.Again:  # pragma: no cover
                pass
            no_data_2.append(no_data_out_1)
            no_data_2.append(no_data_out_2)

        with self.assertRaises(zmq.Again):  # should have no data
            ret_msg = receiver.recv_json(flags=zmq.NOBLOCK)
        with self.assertRaises(zmq.Again):  # should have no data
            ret_msg = receiver_2.recv_json(flags=zmq.NOBLOCK)

        kill(converter_manager_process)
        time.sleep(0.5)
        receiver.close()
        receiver_2.close()
        sender.close()
        sender_2.close()
        context.term()

        self.assertTrue(
            all(item is False for item in no_data), 'Did not receive enough data')
        self.assertTrue(
            all(item is False for item in no_data_2), 'Did not receive enough data')
        # check if all processes are closed
        self.assertNotEqual(converter_manager_process.poll(), None)

    @unittest.skip('Not implemented yet')
    def test_converter_bidirectional_communication(self):
        pass

    @unittest.skipIf(os.name == 'nt', "Test requires to send CRTL event; That is difficult under windows.")
    # test the setup and close of converter processes handled by the converter
    # manager; initiated by crtl
    def test_converter_crtl(self):
        for _ in range(5):  # setup and delete 5 times 10 converter processes
            converter_manager_process = run_script_in_process(
                converter_script_path, self.configs_path[0])  # start script in process that captures SIGINT
            # 10 converter in 10 processes + ZMQ thread take time to start up
            time.sleep(1.0)
            converter_manager_process.send_signal(signal.SIGINT)
            time.sleep(2.0)
            # check if all processes are closed
            self.assertNotEqual(converter_manager_process.poll(), None)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
