import subprocess
import os

from online_monitor.utils import settings

def run_script_in_shell(script, arguments, command=None):
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


if __name__ == '__main__':
    settings.add_converter_path(r'examples/converter')  # needed to find the converter
    settings.add_receiver_path(r'examples/receiver')  # needed to find the receivers
    run_script_in_shell('', 'configuration.yaml', 'start_online_monitor')
