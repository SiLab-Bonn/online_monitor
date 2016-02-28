# A generic online monitor for real-time plots from independent data acquisition systems
[![Build Status](https://travis-ci.org/SiLab-Bonn/online_monitor.svg?branch=master)](https://travis-ci.org/SiLab-Bonn/online_monitor)
[![Coverage Status](https://coveralls.io/repos/SiLab-Bonn/online_monitor/badge.svg?branch=master&service=github)](https://coveralls.io/github/SiLab-Bonn/online_monitor?branch=master)
TBD

# Installation

The last stable code is hosted on PyPi. Thus for installation type:
```
pip install online_monitor
```

Otherwise download the code and

```
python setup.py develop
```

You can run the unit tests to check the installation

```
nosetests online_monitor
```

# Usage

For a demo type into the console:

```
  start_online_monitor
```

# Info
This package is a meta package providing all tools to convert data in real time distributed on several PCs and to visulize them in real time (> 20 Hz). The online monitor is based on a concept with these enitites:

- Producer:
  This is your DAQ system that sends data via a ZMQ PUB socket. The data format is your choise. The producer is not part of the online_monitor. For testing / debugging a simulation producer is provided that can generate fake data.

- Converter:
  A converter converts data from one (ore more) producers (e.g. histogramming) and publishes the converted data as a ZMQ PUB socket. Since the converter is specific to your data type you have to define the converter! Take a look at the example folder.

- Receiver:
A receiver connects to a converter and defines the plots to be shown. Since the receiver is specific to your wished / data you have to define the receiver! Take a look at the example folder.

Complex chains are possible with several parallel/interconnected converters, receivers and producers. One configuraion *. yaml file defines your system. Take a look at the example folder or the main folder for a configuration.yaml example.

There are start script to start the online monitor and/or the converters and producers simulating data.

To start the online monitor including simulation producers / converters type into the console:
```
start_online_monitor configuration.yaml
```

To start the converters type:
```
start_converters configuration.yaml
```

Everything is tested with high coverage and supposed to work under Linux/Windows 32/64 bit and Python 2/3.
A more detailed documention will follow the next release.


