#!/usr/bin/env python
from online_monitor.utils import utils
from online_monitor.utils.producer_sim_manager import ProducerSimManager


def main():
    args = utils.parse_arguments()
    utils.setup_logging(args.log)

    cm = ProducerSimManager(args.config_file)
    cm.start()  # blocking function, returns on SIGTERM signal

if __name__ == '__main__':
    main()
