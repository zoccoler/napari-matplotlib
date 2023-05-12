import napari
import numpy as np
import pandas as pd
from magicgui import magicgui
from napari_matplotlib.line import MetadataLine2DWidget
from skimage.io import imread
import matplotlib.pyplot as plt

# Read video

url_data = r"C:\Users\mazo260d\Documents\GitHub\metroid\Data\Cell1\videos_AP\vid1.tif"
# url_data = r"Z:\Programming\metroid-master\Data\Cell1\videos_AP\vid1.tif"
video_AP1 = imread(url_data)
video_AP1 = video_AP1[:, np.newaxis]
frame_rate_AP1 = 55.78

url_data = r"C:\Users\mazo260d\Documents\GitHub\metroid\Data\Cell1\video_EP\cellmask.tif"
# url_data = r"Z:\Programming\metroid-master\Data\Cell1\video_EP\cellmask.tif"
mask = imread(url_data).astype(bool)

frame_rate = 60  # Hz or fps

# Get signal and time array


def get_masked_mean_over_time(timelapse_image, binary_mask):
    '''
    timelapse_image: timelapse image (can be uint)
    binary_mask: must be bool
    '''
    # Remove extra Z dimension
    timelapse_image = timelapse_image.squeeze()
    # If mask is 2D, broadcast it to same shape as timelapse_image
    mask_broadcasted = np.broadcast_to(binary_mask, timelapse_image.shape)
    # Create masked array
    timelapse_image_masked = np.ma.array(
        timelapse_image, mask=~mask_broadcasted)
    # Get mean over time of masked array
    signal = timelapse_image_masked.mean(axis=(-2, -1)).data
    return signal


time_array_AP1 = np.arange(video_AP1.shape[0])/frame_rate_AP1
AP_signal = get_masked_mean_over_time(video_AP1, mask)

# Add extra signal
time_array_AP2 = time_array_AP1 * 1.1
AP_signal2 = AP_signal * 1.005

time_array_AP1 = np.stack((time_array_AP1, time_array_AP2), axis=0)
AP_signal = np.stack((AP_signal, AP_signal2), axis=0)

# Open napari viewer with video

viewer = napari.Viewer()
image_layer_AP = viewer.add_image(video_AP1)

# Append metadata to layer containing signal

# Example:
# metadata = {'plugin_name': {'positions': positions,
#                             'x_data': x_data,
#                             'y_data': y_data,
#                             'plugin_version': '0.0.1'},
#             'other_image_metadata': 'image_metadata_value'}
metadata_AP1 = {}
# Add plugin1 data
metadata_AP1['plugin1'] = {}
metadata_AP1['plugin1']['signal'] = AP_signal
metadata_AP1['plugin1']['time'] = time_array_AP1


image_layer_AP.metadata = metadata_AP1

# Call plotter

plotter_widget = MetadataLine2DWidget(viewer)
viewer.window.add_dock_widget(plotter_widget)

napari.run()
