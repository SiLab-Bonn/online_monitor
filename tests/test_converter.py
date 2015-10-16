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

converter_script_path = r'online_monitor/start_converter.py'


# creates a yaml config describing n_converter of type forwarder that are all connection to each other
def create_forwarder_config_yaml(n_converter, one_io=True):
    conf, devices = {}, {}
    if one_io:  # just one incoming outgoing connection
        for index in range(n_converter):
            devices['DUT%s' % index] = {
                'data_type': 'forwarder',
                'receive_address': 'tcp://127.0.0.1:55%02d' % index,
                'send_address': 'tcp://127.0.0.1:55%02d' % (index + 1),
                'max_cpu_load': None
            }
    else:  # 2 / 2 incoming/outgoing connections
        for index in range(n_converter):
            devices['DUT%s' % index] = {
                'data_type': 'forwarder',
                'receive_address': ['tcp://127.0.0.1:55%02d' % index, 'tcp://127.0.0.1:56%02d' % index],
                'send_address': ['tcp://127.0.0.1:55%02d' % (index + 1), 'tcp://127.0.0.1:56%02d' % (index + 1)],
                'max_cpu_load': None
            }
    conf['converter'] = devices
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


class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tmp_cfg_10_converter.yml', 'w') as outfile:  # 10 forwarder converters connected in a chain
            config_file = create_forwarder_config_yaml(10)
            outfile.write(config_file)
        with open('tmp_cfg_3_converter_multi.yml', 'w') as outfile:  # 3 forwarder converters with 2 in / 2 out connections, connected in a chain
            config_file = create_forwarder_config_yaml(3, one_io=False)
            outfile.write(config_file)

    @classmethod
    def tearDownClass(cls):  # remove created files
        os.remove('tmp_cfg_10_converter.yml')
        os.remove('tmp_cfg_3_converter_multi.yml')

    def test_converter_communication(self):  # start 10 forwarder in a chain and do "whisper down the lane"
        n_python = get_python_processes()  # python instances before converter start
        # Forward receivers with single in/out
        converter_manager_process = run_script_in_shell(converter_script_path, 'tmp_cfg_10_converter.yml')
        time.sleep(1.5)  # 10 converter in 10 processes + ZMQ thread take time to start up
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
        except zmq.Again:  # pragma: no cover
            pass

        kill(converter_manager_process)
        time.sleep(1)
        sender.close()
        receiver.close()
        context.term()
        time.sleep(0.5)
        n_python_2 = get_python_processes()  # python instances after converter stop
        self.assertFalse(no_data, 'Did not receive any data')
        self.assertEqual(n_python, n_python_2)  # check if all processes are closed, Linux has extra python process (why?)

    def test_converter_communication_2(self):  # start 3 forwarder in a chain with 2 i/o each and do "whisper down the lane"
        n_python = get_python_processes()  # python instances before converter start
        # Forward receivers with 2 in/out
        converter_manager_process = run_script_in_shell(converter_script_path, 'tmp_cfg_3_converter_multi.yml')
        time.sleep(1.5)  # 10 converter in 10 processes + ZMQ thread take time to start up
        context = zmq.Context()
        # Sockets facing last converter inputs
        sender = context.socket(zmq.PUB)  # publish data where first transveiver listens to
        sender.bind(r'tcp://127.0.0.1:5500')
        sender_2 = context.socket(zmq.PUB)  # publish data where first transveiver 2nd input listens to
        sender_2.bind(r'tcp://127.0.0.1:5600')
        receiver = context.socket(zmq.SUB)  # subscriber to the last transveiver in the chain
        receiver.connect(r'tcp://127.0.0.1:5503')
        receiver.setsockopt(zmq.SUBSCRIBE, '')
        receiver_2 = context.socket(zmq.SUB)  # subscriber to the last transveiver in the chain
        receiver_2.connect(r'tcp://127.0.0.1:5603')
        receiver_2.setsockopt(zmq.SUBSCRIBE, '')  # do not filter any data
        time.sleep(0.5)
        msg = 'This is a test message'
        msg_2 = 'This is another test message'

        sender.send_json(msg)
        time.sleep(0.5)
        no_data = []
        for _ in range(4):  # forwarder forwards all inputs to all outputs; for 3 forwarder in a chain with 2 i/o each you expect 2**3 times the input message
            no_data_out_1, no_data_out_2 = True, True  # flag set to False if data is received
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
        time.sleep(0.5)
        no_data_2 = []
        for _ in range(4):
            no_data_out_1, no_data_out_2 = True, True  # flag set to False if data is received
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
        time.sleep(1)
        receiver.close()
        receiver_2.close()
        sender.close()
        sender_2.close()
        context.term()

        n_python_2 = get_python_processes()  # python instances after converter stop
        self.assertTrue(all(item is False for item in no_data), 'Did not receive enough data')
        self.assertTrue(all(item is False for item in no_data_2), 'Did not receive enough data')
        self.assertEqual(n_python , n_python_2)  # check if all processes are closed

    @unittest.skipIf(os.name == 'nt', "Test requires to send CRTL event; That is difficult under windows.")
    def test_converter_crtl(self):  # test the setup and close of converter processes handled by the converter manager; initiated by crtl
        n_expected_processes = get_python_processes() + 1  # +1 needed under linux
        for _ in range(5):  # setup and delete 5 times 10 converter processes
            converter_manager_process = run_script_in_process(converter_script_path, 'tmp_cfg_10_converter.yml')  # start script in process that captures SIGINT
            time.sleep(0.5)  # 10 converter in 10 processes + ZMQ thread take time to start up
            converter_manager_process.send_signal(signal.SIGINT)
            time.sleep(0.5)
            self.assertEqual(get_python_processes(), n_expected_processes)

if __name__ == '__main__':
    converter_script_path = r'../online_monitor/start_converter.py'
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)
