import sys
import logging

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils, settings
from online_monitor.receiver.receiver import Receiver


class OnlineMonitorApplication(QtWidgets.QMainWindow):
    app_name = 'Online Monitor'

    def __init__(self, config_file, loglevel='INFO'):
        super(OnlineMonitorApplication, self).__init__()
        utils.setup_logging(loglevel)
        logging.debug("Initialize online monitor with configuration in %s", config_file)
        self.configuration = utils.parse_config_file(config_file, expect_receiver=True)
        self.setup_style()
        self.setup_widgets()
        self.receivers = self.start_receivers()
        self.add_refresh_toolbar()

    def add_refresh_toolbar(self):

        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu('Settings')
        
        refresh_toolbar = self.addToolBar('Refresh rates')
        settings_menu.addAction(refresh_toolbar.toggleViewAction())
        refresh_toolbar.addWidget(QtWidgets.QLabel('Receiver refresh rates'))
        refresh_toolbar.addSeparator()
        
        # Loop over receivers and make widgets
        for recv in self.receivers:
            widget_recv = QtWidgets.QWidget()
            layout_recv = QtWidgets.QHBoxLayout()
            widget_recv.setLayout(layout_recv)
            label_recv = QtWidgets.QLabel(f'{recv.name}:')
            spinbox_recv = QtWidgets.QSpinBox()
            spinbox_recv.setRange(0, 100)
            spinbox_recv.setSuffix(' Hz')
            spinbox_recv.setValue(10)
            checkbox_unlock = QtWidgets.QCheckBox('unlocked')
            checkbox_unlock.setToolTip("Unlock refresh rate to match data rate")

            # Connections
            checkbox_unlock.stateChanged.connect(lambda state, spbx=spinbox_recv: spbx.setEnabled(not state))
            checkbox_unlock.stateChanged.connect(lambda state, r=recv, spbx=spinbox_recv:
                                                     setattr(r, 'refresh_rate', None if state else spbx.value()))
            spinbox_recv.valueChanged.connect(lambda val, r=recv: setattr(r, 'refresh_rate', val))
            
            spinbox_recv.valueChanged.emit(spinbox_recv.value())

            layout_recv.addWidget(label_recv)
            layout_recv.addWidget(spinbox_recv)
            layout_recv.addWidget(checkbox_unlock)
            refresh_toolbar.addWidget(widget_recv)
            refresh_toolbar.addSeparator()

    def closeEvent(self, event):
        super(OnlineMonitorApplication, self).closeEvent(event)
        self.stop_receivers()
        settings.set_window_geometry(self.geometry().getRect())

    def setup_style(self):
        self.setWindowTitle(self.app_name)
        stored_windows_geometry = settings.get_window_geometry()
        if stored_windows_geometry:
            self.setGeometry(QtCore.QRect(*stored_windows_geometry))
        # Fore/Background color
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

    def start_receivers(self):
        receivers = []
        try:
            self.configuration['receiver']
        except KeyError:
            return receivers
        if self.configuration['receiver']:
            logging.info('Starting %d receivers', len(self.configuration['receiver']))
            for (receiver_name, receiver_settings) in sorted(self.configuration['receiver'].items()):
                receiver_settings['name'] = receiver_name
                receiver = utils.load_receiver(receiver_settings['kind'], base_class_type=Receiver, *(), **receiver_settings)
                receiver.setup_widgets(self.tab_widget, name=receiver_name)
                receiver.start()
                receivers.append(receiver)
            return receivers

    def on_tab_changed(self, value):
        for index, actual_receiver in enumerate(self.receivers, start=1):  # First index is status tab widget
            actual_receiver.active(True if index == value else False)

    def stop_receivers(self):
        if self.receivers:
            logging.info('Stopping %d receivers', len(self.receivers))
            for receiver in self.receivers:
                receiver.shutdown()

    def setup_widgets(self):
        # Main window with Tab widget
        self.tab_widget = QtWidgets.QTabWidget()
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
        try:
            self.configuration['receiver']
        except KeyError:
            return
        # Create nodes with links from configuration file for converter/receiver
        for receiver_index, (receiver_name, receiver_settings) in enumerate(self.configuration['receiver'].items()):
            # Add receiver info
            view = status_graphics_widget.addViewBox(row=receiver_index, col=5, lockAspect=True, enableMouse=False)
            text = pg.TextItem('Receiver\n%s' % receiver_name, border='b', fill=(0, 0, 255, 100), anchor=(0.5, 0.5), color=(0, 0, 0, 200))
            text.setPos(0.5, 0.5)
            view.addItem(text)
            # Add corresponding producer info
            try:
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
            except KeyError:  # No converter defined in configruation
                pass
            
#             nodes = ['Producer\n%s' % converter_name, 'Converter\n%s' % converter_settings['kind'], 'Receiver\n%s' % converter_settings['kind']]
            
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
#             nodes = ['Producer\n%s' % converter_name, 'Converter\n%s' % converter_settings['kind']]
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

    app = QtWidgets.QApplication(sys.argv)
    win = OnlineMonitorApplication(args.config_file)  # enter remote IP to connect to the other side listening
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()  # pragma: no cover, cannot be tested in unittests due to qt event loop
