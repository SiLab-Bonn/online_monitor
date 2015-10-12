import subprocess
import time
import psutil
import os

from online_monitor.utils import settings
from examples.full_example.producer import Producer


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=True if os.name == 'nt' else False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()

if __name__ == '__main__':
    # Start a producer that creates fake DAQ data
    producer_addresses = [r'tcp://127.0.0.1:5500', r'tcp://127.0.0.1:5501']
    daqs = []
    for producer_address in producer_addresses:
        daq = Producer(producer_address, name='DAQ', loglevel='DEBUG')
        daq.start()
        daqs.append(daq)

    # Start the converter
    converter_manager_process = run_script_in_process(r'../../online_monitor/start_converter.py', r'configuration.yaml')
    settings.add_converter_path(r'examples/converter')  # needed to find the converter
    settings.add_receiver_path(r'examples/receiver')  # needed to find the receiver
    
    
    
    time.sleep(5)
    
    # Stop other threads
    for daq in daqs:
        daq.shutdown()
    kill(converter_manager_process)