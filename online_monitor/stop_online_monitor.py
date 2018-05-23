#!/usr/bin/env python
import psutil


def main():
    for proc in psutil.process_iter():
        if any(name in proc.name() for name in ['start_producer', 'start_converter', 'start_online']) or any(name in ''.join(proc.cmdline()) for name in ['start_producer', 'start_converter', 'start_online']):
            proc.kill()


if __name__ == '__main__':
    main()
