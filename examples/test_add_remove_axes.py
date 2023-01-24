import napari
import numpy as np
from napari_matplotlib.base import NapariMPLWidget
from napari_matplotlib.scatter import ScatterBaseWidget, ScatterWidget
from napari_matplotlib.line import MetadataLine2DWidget
viewer = napari.Viewer()
metadata = {'my_plugin': {'x_data': np.arange(5), 'y_data': np.arange(5)**2}}
viewer.add_image(np.arange(128).reshape(2,8,8), metadata = metadata)

# Call plotter

plotter_widget = MetadataLine2DWidget(viewer)
viewer.window.add_dock_widget(plotter_widget)
# plotter_widget.draw()
# plotter_widget.canvas.draw_idle()
plotter_widget._add_row_axis()

plotter_widget._remove_row_axis()

a=1