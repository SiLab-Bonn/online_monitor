import subprocess
import psutil
import os
import sys
from PyQt4 import Qt

from online_monitor.utils import settings
from online_monitor.OnlineMonitor import OnlineMonitorApplication


def run_script_in_shell(script, arguments):
    return subprocess.Popen("python %s %s" % (script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()

if __name__ == '__main__':
    # Start the simulation producer to create some fake data
    producer_process = run_script_in_shell(r'../../online_monitor/utils/producer_sim.py', 'configuration.yaml')

    # Start the converter
    settings.add_converter_path(r'examples/converter')  # needed to find the converter
    settings.add_receiver_path(r'examples/receiver')  # needed to find the receiver
    converter_manager_process = run_script_in_shell(r'../../online_monitor/start_converter.py', r'configuration.yaml')

    # Helper function to run code after OnlineMonitor Application exit
    def appExec():
        app.exec_()
        # Stop other processes
        kill(converter_manager_process)
        kill(producer_process)

    # Start the online monitor
    app = Qt.QApplication(sys.argv)
    win = OnlineMonitorApplication(r'configuration.yaml')
    win.show()
    sys.exit(appExec())