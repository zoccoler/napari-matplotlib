import napari
import numpy as np
import pandas as pd
from magicgui import magicgui
from napari_matplotlib.line import MetadataLine2DWidget
from napari_matplotlib.scatter import FeaturesScatterWidget

image = np.random.randint(0, 10, (5, 10, 10))

positions = np.random.randint(0, 10, (3, 5))
x_data = np.arange(0, 5)
y_data = x_data**2

x_data2 = np.arange(0, 5)
y_data2 = x_data2**3

data_types = [
    x_data, # 1D np array
    np.asarray([x_data, x_data2]), # 2D array
    [x_data], # list of a single 1D array
    [x_data, x_data2], # list of multiple 1D arrays
    pd.DataFrame(x_data), # pandas series 1D (arranged as columns)
    pd.DataFrame([x_data, x_data2]).T # pandas dataframe 2D (arranged as columns)
]

x_1d_list = [
    x_data, # 1D np array
    [x_data], # list of a single 1D array
    pd.DataFrame(x_data), # pandas series 1D (arranged as columns)
]
x_2d_list = [
    np.asarray([x_data, x_data2]), # 2D array
    [x_data, x_data2], # list of multiple 1D arrays
    pd.DataFrame([x_data, x_data2]).T # pandas dataframe 2D (arranged as columns)
]
y_1d = [y_data]
y_2d = [y_data, y_data2]

viewer = napari.Viewer()



# metadata = {'plugin_name': {'positions': positions,
#                             'x_data': x_data,
#                             'y_data': y_data,
#                             'plugin_version': '0.0.1'},
#             'other_image_metadata': 'image_metadata_value'}

metadata = {}
# Add plugin1 data
metadata['plugin1'] = {}
for i, x_1d in enumerate(x_1d_list):
    metadata['plugin1']['x_data_1d_' + str(i)] = x_1d
metadata['plugin1']['y_data_1d'] = y_1d
# plugin2 data
metadata['plugin2'] = {}
for i, x_1d in enumerate(x_1d_list):
    metadata['plugin2']['x_data_1d_' + str(i)] = x_1d
metadata['plugin2']['y_data2d'] = y_2d
# Add plugin 3 data
metadata['plugin3'] = {}
for i, x_2d in enumerate(x_2d_list):
    metadata['plugin3']['x_data_2d_' + str(i)] = x_2d
metadata['plugin3']['y_data_2d'] = y_2d 


# viewer.add_labels(np.array([[0,1],[2,2]], dtype = int))
viewer.add_image(image, metadata=metadata)

image_time_series = np.arange(150).reshape(6,5,5)
time_step = 10 #ms

metadata2 = {}
metadata2['time-series-plugin'] = {}
metadata2['time-series-plugin']['time'] = np.arange(image_time_series.shape[0])*10
metadata2['time-series-plugin']['average'] = np.mean(image_time_series, axis=(1,2))

viewer.add_image(image_time_series, metadata = metadata2)

plotter_widget = MetadataLine2DWidget(viewer)
# plotter_widget = FeaturesScatterWidget(viewer)
viewer.window.add_dock_widget(plotter_widget)

