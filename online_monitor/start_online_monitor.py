#!/usr/bin/env python
import sys
import psutil
import subprocess
import os
from PyQt4 import Qt

from online_monitor.OnlineMonitor import OnlineMonitorApplication
from online_monitor.utils import utils


def kill(proc):  # kill process by id, including subprocesses; works for linux and windows
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def run_script_in_shell(script, arguments, command=None):
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


def main():
    args = utils.parse_arguments()
    utils.setup_logging(args.log)

    # Start the simulation producer to create some fake data
    producer_process = run_script_in_shell('', args.config_file, 'start_producer_sim')

    # Start the converter
    converter_manager_process = run_script_in_shell('', args.config_file, 'start_converter')

#     # Helper function to run code after OnlineMonitor Application exit
    def appExec():
        app.exec_()
        # Stop other processes
        kill(converter_manager_process)
        kill(producer_process)
 
    # Start the online monitor
    app = Qt.QApplication(sys.argv)
    win = OnlineMonitorApplication(args.config_file)
    win.show()
    sys.exit(appExec())

if __name__ == '__main__':
    main()
