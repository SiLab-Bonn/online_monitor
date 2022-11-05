# A generic online monitor for real-time plots from independent data acquisition systems
[![Build Status](https://github.com/Silab-Bonn/online_monitor/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/SiLab-Bonn/online_monitor/actions)
[![Coverage Status](https://coveralls.io/repos/SiLab-Bonn/online_monitor/badge.svg?branch=master&service=github)](https://coveralls.io/github/SiLab-Bonn/online_monitor?branch=master)

# Installation

The last stable code is hosted on PyPi. Thus for installation type:
```
pip install --upgrade pip
pip install online_monitor
```

Otherwise download the code and run

```
pip install -e .
```

You can run the unit tests to check the installation

```
pytest online_monitor
```

# Usage
For a demo type into the console:

```
  start_online_monitor
```
To stop all instances of `online_monitor` (e.g. converter, receiver, etc), type
```
stop_online_monitor
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

# Custom receiver
Have a look at [the examples](online_monitor/examples/receiver).
When building your custom receiver, use `pyqtgraph` only for plotting-related tasks e.g. `pg.ImageItem` etc.
Avoid using `pyqtgraph` for building generic widgets (especially the deprecated `QtGui` submodule), instead use `pyqt5` directly:
```
from PyQt5 import QtWidgets, QtCore

my_custom_label = QtWidgets.QLabel("My label")
my_custom_double_spinbox = QtWidgets.QDoubleSpinBox()
my_custom_grid_layout = QtWidgets.QGridLayout()
my_custom_signal = QtCore.pyqtSignal(str)
...
```
# Testing
Everything is tested on Windows and Linux for Python 3.8/9 with coverage.
Have a look at the [tests](online_monitor/testing) as well as the respective [GH actions](https://github.com/SiLab-Bonn/online_monitor/actions) and [coverall.io](https://coveralls.io/github/SiLab-Bonn/online_monitor) pages. 
