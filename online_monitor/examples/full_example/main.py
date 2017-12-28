''' This script start the online monitor with the example entities (simulation producer, converter, receiver)

Thre online monitor should actually be used from the console und not with a start script like used here!

Go to this folder and type:
start_online_monitor configuration.yaml
'''

import subprocess
import os

import online_monitor
from online_monitor.utils import settings


def run_script_in_shell(script, arguments, command=None):
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)

if __name__ == '__main__':
    package_path = os.path.dirname(online_monitor.__file__)  # Get the absoulte path of the online_monitor installation
    settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/producer_sim')))
    settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/converter')))
    settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(package_path)) + r'/examples/receiver')))
    run_script_in_shell('', 'configuration.yaml', 'start_online_monitor')
