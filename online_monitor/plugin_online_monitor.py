#!/usr/bin/env python
import sys
import os

from online_monitor.utils import settings


def main():
    """
    Function allowing to add online monitor paths to search for converters/receivers/producer_sims

    Call 'plugin_online_monitor /path/to/my/online/monitor/plugins' to add them
    """

    # No path has been given, add current path
    if len(sys.argv) == 1:
        plugin_paths = [os.getcwd()]
    else:
        plugin_paths = sys.argv[1:]

    kinds = ('converter', 'receiver', 'producer_sim')

    # Loop over plugin paths
    for plug in plugin_paths:
        
        # Get paths to plugin online monitor
        abs_plug = os.path.abspath(plug)
        
        # Add this path for converter/receiver/producer_sim
        for kind in kinds:
            
            getattr(settings, f'add_{kind}_path')(abs_plug)

            # Check whether inside this path converter/receiver/producer_sim directories are defined
            # If so, add these paths also
            abs_plug_dir = os.path.join(abs_plug, kind)
            if os.path.isdir(abs_plug_dir):
                getattr(settings, f'add_{kind}_path')(abs_plug_dir)
            

if __name__ == '__main__':
    main()
