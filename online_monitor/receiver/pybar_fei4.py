from receiver import Receiver
from zmq.utils import jsonapi
import numpy as np

from PyQt4 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor import utils


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

    def deserialze_data(self, data):
        f = jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        return f

    def handle_data(self, data):
#         for (i,k) in data.items():
#             print i,type(k)
#         occupancy, tot_hist, tdc_counters, error_counters, service_records_counters, trigger_error_counters, rel_bcid_hist = **data
        if 'meta_data' not in data:
            self.occupancy_img.setImage(data['occupancy'][:, ::-1, 0], autoDownsample=True)
            self.tot_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'], fillLevel=0, brush=(0, 0, 255, 150))
            self.event_status_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.service_record_plot.setData(x=np.linspace(-0.5, 31.5, 33), y=data['service_records_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.trigger_status_plot.setData(x=np.linspace(-0.5, 7.5, 9), y=data['trigger_error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.hit_timing_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['rel_bcid_hist'][:16], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
        
    