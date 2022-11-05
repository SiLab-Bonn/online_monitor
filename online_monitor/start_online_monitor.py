#!/usr/bin/env python
import sys
import os
import psutil
import subprocess
import logging
from PyQt5 import QtWidgets


from online_monitor.utils import settings
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
    # If no configuration file is provided show a demo of the online monitor
    if sys.argv[1:]:
        args = utils.parse_arguments()
    else:
        class Dummy(object):

            def __init__(self):
                self.config_file = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)) + r'/configuration.yaml'))
                self.log = 'INFO'
        args = Dummy()
        logging.warning('No configuration file provided! Show a demo of the online monitor!')

    utils.setup_logging(args.log)

    # Start the simulation producer to create some fake data
    producer_sim_process = run_script_in_shell('', args.config_file, 'start_producer_sim')

    # Start the converter
    converter_manager_process = run_script_in_shell('', args.config_file, 'start_converter')

# Helper function to run code after OnlineMonitor Application exit
    def appExec():
        app.exec_()
        # Stop other processes
        try:
            kill(producer_sim_process)
        except psutil.NoSuchProcess:  # If the process was never started it cannot be killed
            pass
        try:
            kill(converter_manager_process)
        except psutil.NoSuchProcess:  # If the process was never started it cannot be killed
            pass
    # Start the online monitor
    app = QtWidgets.QApplication(sys.argv)
    win = OnlineMonitorApplication(args.config_file)
    win.show()
    sys.exit(appExec())


if __name__ == '__main__':
    main()
