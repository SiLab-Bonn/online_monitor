from receiver import Receiver
from zmq.utils import jsonapi
import numpy as np

from PyQt4 import Qt
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import DockArea, Dock
import pyqtgraph.ptime as ptime
from threading import Event, Lock


class PybarFEI4(Receiver):
    def setup_connections(self, main):
        pass
    def setup_plots(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)

        dock_occcupancy = Dock("Occupancy", size=(400, 400))
        dock_run_config = Dock("Run configuration", size=(400, 400))
        dock_global_config = Dock("Global configuration", size=(400, 400))
        dock_tot = Dock("Time over threshold values (TOT)", size=(400, 400))
        dock_tdc = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_event_status = Dock("Event status", size=(400, 400))
        dock_trigger_status = Dock("Trigger status", size=(400, 400))
        dock_service_records = Dock("Service records", size=(400, 400))
        dock_hit_timing = Dock("Hit timing (rel. BCID)", size=(400, 400))

        dock_area.addDock(dock_global_config, 'left')
        dock_area.addDock(dock_run_config, 'above', dock_global_config)
        dock_area.addDock(dock_occcupancy, 'above', dock_run_config)
        dock_area.addDock(dock_tdc, 'right', dock_occcupancy)
        dock_area.addDock(dock_tot, 'above', dock_tdc)
        dock_area.addDock(dock_service_records, 'bottom', dock_occcupancy)
        dock_area.addDock(dock_trigger_status, 'above', dock_service_records)
        dock_area.addDock(dock_event_status, 'above', dock_trigger_status)
        dock_area.addDock(dock_hit_timing, 'bottom', dock_tot)

        # Run config dock
        self.run_conf_list_widget = Qt.QListWidget()
        dock_run_config.addWidget(self.run_conf_list_widget)

        # Global config dock
        self.global_conf_list_widget = Qt.QListWidget()
        dock_global_config.addWidget(self.global_conf_list_widget)

        # Different plot docks
        occupancy_graphics = pg.GraphicsLayoutWidget()
        occupancy_graphics.show()
        view = occupancy_graphics.addViewBox()
        self.occupancy_img = pg.ImageItem(border='w')
        view.addItem(self.occupancy_img)
        view.setRange(QtCore.QRectF(0, 0, 80, 336))
        dock_occcupancy.addWidget(occupancy_graphics)

        tot_plot_widget = pg.PlotWidget(background="w")
        self.tot_plot = tot_plot_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget.showGrid(y=True)
        dock_tot.addWidget(tot_plot_widget)

        tdc_plot_widget = pg.PlotWidget(background="w")
        self.tdc_plot = tdc_plot_widget.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget.showGrid(y=True)
        tdc_plot_widget.setXRange(0, 800, update=True)
        dock_tdc.addWidget(tdc_plot_widget)

        event_status_widget = pg.PlotWidget()
        self.event_status_plot = event_status_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        event_status_widget.showGrid(y=True)
        dock_event_status.addWidget(event_status_widget)

        trigger_status_widget = pg.PlotWidget()
        self.trigger_status_plot = trigger_status_widget.plot(np.linspace(-0.5, 7.5, 9), np.zeros((8)), stepMode=True)
        trigger_status_widget.showGrid(y=True)
        dock_trigger_status.addWidget(trigger_status_widget)

        service_record_widget = pg.PlotWidget()
        self.service_record_plot = service_record_widget.plot(np.linspace(-0.5, 31.5, 33), np.zeros((32)), stepMode=True)
        service_record_widget.showGrid(y=True)
        dock_service_records.addWidget(service_record_widget)

        hit_timing_widget = pg.PlotWidget()
        self.hit_timing_plot = hit_timing_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        hit_timing_widget.showGrid(y=True)
        dock_hit_timing.addWidget(hit_timing_widget)