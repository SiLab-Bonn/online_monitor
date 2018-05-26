''' This script starts the online monitor with the example entities

    The entities are: simulation producer, converter, receiver

    The online monitor should actually be used with its entry point
    from the terminal und not with a start script like used here!

    To use the entry point in a terminal go to this folder and type:
    start_online_monitor configuration.yaml
'''

import subprocess
import os

import online_monitor
from online_monitor.utils import settings


def run_script_in_shell(script, arguments, command=None):
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        creationflags = 0
    return subprocess.Popen("%s %s %s" % ('python' if not command else command,
                                          script, arguments), shell=True,
                            creationflags=creationflags)

if __name__ == '__main__':
    # Get the absoulte path of the online_monitor installation
    package_path = os.path.dirname(online_monitor.__file__)
    # Add examples folder to entity search paths
    settings.add_producer_sim_path(os.path.join(package_path,
                                                'examples',
                                                'producer_sim'))
    settings.add_converter_path(os.path.join(package_path,
                                             'examples',
                                             'converter'))
    settings.add_receiver_path(os.path.join(package_path,
                                            'examples',
                                            'receiver'))
    run_script_in_shell('', 'configuration.yaml', 'start_online_monitor')
