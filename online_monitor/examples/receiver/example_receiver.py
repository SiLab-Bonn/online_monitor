from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi

import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils


class ExampleReceiver(Receiver):

    def setup_receiver(self):
        self.plot_data = None

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)

        dock_position = Dock("Position")
        dock_area.addDock(dock_position)

        # Position 2d plot
        position_graphics = pg.GraphicsLayoutWidget()
        position_graphics.show()
        view = position_graphics.addViewBox()
        self.position_img = pg.ImageItem(border='w')
        self.position_img.setLookupTable(utils.lut_from_colormap('plasma'))
        view.addItem(self.position_img)
        dock_position.addWidget(position_graphics)

    def deserialize_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def handle_data(self, data):
        for actual_data_type, actual_data in data.items():
            if 'time_stamp' not in actual_data_type:  # time stamp info is not plotted
                self.plot_data = actual_data[:]
    
    def refresh_data(self):
        if self.plot_data is not None:
            self.position_img.setImage(self.plot_data, autoDownsample=True)