import sys
import time
import numpy as np
import argparse
import logging

from PyQt4 import Qt
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils, settings
from receiver.receiver import Receiver


class OnlineMonitorApplication(pg.Qt.QtGui.QMainWindow):
    app_name = 'Online Monitor'

    def __init__(self, config_file, loglevel='INFO'):
        super(OnlineMonitorApplication, self).__init__()
        utils.setup_logging(loglevel)
        logging.debug("Initialize online monitor with configuration in %s", config_file)
        self.configuration = utils.parse_config_file(config_file, expect_receiver=True)
        self.setup_style()
        self.setup_widgets()
        self.receivers = self.start_receivers()

    def closeEvent(self, event):
        super(OnlineMonitorApplication, self).closeEvent(event)
        self.stop_receivers()
        settings.set_window_geometry(self.geometry().getRect())

    def setup_style(self):
        self.setWindowTitle(self.app_name)
        stored_windows_geometry = settings.get_window_geometry()
        if stored_windows_geometry:
            self.setGeometry(pg.Qt.QtCore.QRect(*stored_windows_geometry))
        # Fore/Background color
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

    def start_receivers(self):
        receivers = []
        if self.configuration['receiver']:
            logging.info('Starting %d receivers', len(self.configuration['receiver']))
            for (receiver_name, receiver_settings) in self.configuration['receiver'].items():
                receiver_settings['name'] = receiver_name
                receiver = utils.load_receiver(receiver_settings['data_type'], base_class_type=Receiver, *(), **receiver_settings)
                receiver.setup_plots(self.tab_widget, name=receiver_name)
                receiver.start()
                receivers.append(receiver)
            return receivers

    def on_tab_changed(self, value):
        if value > 0:  # first index is status tab widget
            for index, actual_receiver in enumerate(self.receivers):
                actual_receiver.active(True if index == value - 1 else False)

    def stop_receivers(self):
        if self.receivers:
            logging.info('Stopping %d receivers', len(self.receivers))
            for receiver in self.receivers:
                receiver.shutdown()

    def setup_widgets(self):
        # Main window with Tab widget
        self.tab_widget = Qt.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.setup_status_widget(self.tab_widget)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

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
        # Create nodes with links from configuration file for converter/receiver
        for receiver_index, (receiver_name, receiver_settings) in enumerate(self.configuration['receiver'].items()):
            # Add receiver info
            view = status_graphics_widget.addViewBox(row=receiver_index, col=5, lockAspect=True, enableMouse=False)
            text = pg.TextItem('Receiver\n%s' % receiver_name, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
            text.setPos(0.5, 0.5)
            view.addItem(text)
            # Add corresponding producer info
            if self.configuration['converter']:
                try:
                    actual_converter = self.configuration['converter'][receiver_name]
                    view = status_graphics_widget.addViewBox(row=receiver_index, col=1, lockAspect=True, enableMouse=False)
                    text = pg.TextItem('Producer\n%s' % receiver_name, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
                    text.setPos(0.5, 0.5)
                    view.addItem(text)
                    view = status_graphics_widget.addViewBox(row=receiver_index, col=3, lockAspect=True, enableMouse=False)
                    text = pg.TextItem('Converter\n%s' % receiver_settings, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
                    text.setPos(0.5, 0.5)
                    view.addItem(text)
                except KeyError:  # no converter for receiver
                    pass
            
#             nodes = ['Producer\n%s' % converter_name, 'Converter\n%s' % converter_settings['data_type'], 'Receiver\n%s' % converter_settings['data_type']]
            
#             links = [converter_settings['receive_address'], converter_settings['send_address']]
#             for node_index, node in enumerate(nodes):
#                 view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2, lockAspect=True, enableMouse=False)
#                 text = pg.TextItem(node, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.5)
#                 view.addItem(text)
# 
#                 if node_index == 0:
#                     text = pg.TextItem('%s' % links[node_index], anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 else:
#                     text = pg.TextItem('%s %s' % (links[node_index - 1], links[node_index]), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.3)
#                 view.addItem(text)
# 
#                 view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2 + 1, lockAspect=True, enableMouse=False)
# #                     # BUG? Position does not not work for arrows?
# #                     arrow = pg.ArrowItem(angle=180, tipAngle=00, baseAngle=00, headLen=50, tailLen=20, tailWidth=2, pen=None, brush=(0, 0, 0, 200))
# #                     arrow.setPos(0.1, 0.2)
# #                     view.addItem(arrow)
#                 text = pg.TextItem('---->', anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.5)
#                 view.addItem(text)
#             
#         # Create nodes with links from configuration file for converter/receiver
#         for receiver_index, (receiver_name, receiver_settings) in enumerate(self.configuration['converter'].items()):
#             nodes = ['Producer\n%s' % converter_name, 'Converter\n%s' % converter_settings['data_type']]
#             links = [converter_settings['receive_address'], converter_settings['send_address']]
#             for node_index, node in enumerate(nodes):
#                 view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2, lockAspect=True, enableMouse=False)
#                 text = pg.TextItem(node, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.5)
#                 view.addItem(text)
# 
#                 if node_index == 0:
#                     text = pg.TextItem('%s' % links[node_index], anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 else:
#                     text = pg.TextItem('%s %s' % (links[node_index - 1], links[node_index]), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.3)
#                 view.addItem(text)
# 
#                 view = status_graphics_widget.addViewBox(row=converter_index, col=node_index * 2 + 1, lockAspect=True, enableMouse=False)
# #                     # BUG? Position does not not work for arrows?
# #                     arrow = pg.ArrowItem(angle=180, tipAngle=00, baseAngle=00, headLen=50, tailLen=20, tailWidth=2, pen=None, brush=(0, 0, 0, 200))
# #                     arrow.setPos(0.1, 0.2)
# #                     view.addItem(arrow)
#                 text = pg.TextItem('---->', anchor=(0.5, 0.5), color=(0, 0, 0, 200))
#                 text.setPos(0.5, 0.5)
#                 view.addItem(text)   

def main():  # pragma: no cover, cannot be tested in unittests due to qt event loop
    args = utils.parse_arguments()
    utils.setup_logging(args.log)

    app = Qt.QApplication(sys.argv) ## r'../examples/full_example/configuration.yaml'
    win = OnlineMonitorApplication(args.config_file)  # enter remote IP to connect to the other side listening
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()  # pragma: no cover, cannot be tested in unittests due to qt event loop
