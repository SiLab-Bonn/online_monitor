import sys
import time
import numpy as np
import argparse
import logging

from optparse import OptionParser

from PyQt4 import Qt
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import pyqtgraph.ptime as ptime

from online_monitor import utils
from receiver.receiver import Receiver


class OnlineMonitorApplication(pg.Qt.QtGui.QMainWindow):
    app_name = 'Online Monitor'

    def __init__(self, config_file, loglevel='INFO'):
        super(OnlineMonitorApplication, self).__init__()
        utils.setup_logging(loglevel)
        logging.debug("Initialize online monitor with configuration in %s", config_file)
        self.configuration = utils.parse_config_file(config_file)
        self.setup_style()
        self.setup_widgets()
        self.setup_receivers()

    def setup_style(self):
        # Fore/Background color
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

    def setup_receivers(self):
        for (receiver_name, receiver_settings) in self.configuration['receiver'].items():
            receiver = utils.factory('receiver.%s' % receiver_settings['data_type'], base_class_type=Receiver, *(), **receiver_settings)
            receiver.setup_plots(self.tab_widget, name=receiver_name)

    def setup_widgets(self):
        # Main window with Tab widget
        self.tab_widget = Qt.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.setup_status_widget(self.tab_widget)

    def setup_status_widget(self, parent):  # Visualizes the nodes + their connections + CPU usage
        # Status dock area showing setup
        dock_area = DockArea()
        parent.addTab(dock_area, 'Status')
        self.status_dock = Dock("Status")
        dock_area.addDock(self.status_dock)
        # GraphicsLayout to align graphics
        status_graphics_widget = pg.GraphicsLayoutWidget()
        status_graphics_widget.show()
        self.status_dock.addWidget(status_graphics_widget)
        # Create nodes with links from configuration file
        for converter_index, (converter_name, converter_settings) in enumerate(self.configuration['converter'].items()):
            nodes = ['Producer\n%s' % converter_name, 'Converter\n%s' % converter_settings['data_type'], 'Receiver\n%s' % converter_settings['data_type']]
            links = [converter_settings['receive_address'], converter_settings['send_address']]
            for node_index, node in enumerate(nodes):
                view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2, lockAspect=True, enableMouse=False)
                text = pg.TextItem(node, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
                text.setPos(0.5, 0.5)
                view.addItem(text)
                if node_index < 2:
                    view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2 + 1, lockAspect=True, enableMouse=False)
#                     # BUG? Position does not not work for arrows?
#                     arrow = pg.ArrowItem(angle=180, tipAngle=00, baseAngle=00, headLen=50, tailLen=20, tailWidth=2, pen=None, brush=(0, 0, 0, 200))
#                     arrow.setPos(0.1, 0.2)
#                     view.addItem(arrow)
                    text = pg.TextItem('     --------------->\n%s' % links[node_index], anchor=(0.5, 0.5), color=(0, 0, 0, 200))
                    text.setPos(0.5, 0.5)
                    view.addItem(text)


if __name__ == '__main__':
#     args = utils.parse_arguments()
#     utils.setup_logging(args.log)

    app = Qt.QApplication(sys.argv)
    win = OnlineMonitorApplication('configuration.yaml')#args.config_file)  # enter remote IP to connect to the other side listening
    win.resize(800, 840)
    win.setWindowTitle(win.app_name)
    win.show()
    sys.exit(app.exec_())
