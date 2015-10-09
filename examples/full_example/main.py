import subprocess
import time
import psutil
import os


def run_script_in_process(script, arguments):
    return subprocess.Popen(["python", script, arguments], shell=True if os.name == 'nt' else False, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()

if __name__ == '__main__':
    converter_manager_process = run_script_in_process(r'../../online_monitor/start_converter.py', r'../examples/full_example/configuration.yaml')
    time.sleep(2)
    kill(converter_manager_process)