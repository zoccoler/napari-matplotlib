from typing import List, Optional, Tuple

import matplotlib.colors as mcolor
import napari
import numpy as np
import pandas as pd
from magicgui import magicgui
from magicgui.widgets import ComboBox
import os
from pathlib import Path

from .base import NapariMPLWidget
from .util import Interval
from matplotlib.widgets import SpanSelector

ICON_ROOT = Path(__file__).parent / "icons"
__all__ = ["Line2DBaseWidget", "MetadataLine2DWidget"]


class Line2DBaseWidget(NapariMPLWidget):
    # opacity value for the lines
    _line_alpha = 0.5
    _lines = []

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)

        self.axes = self.canvas.figure.subplots()
        self.update_layers(None)

        # Create span selector
        self.span_selector = SpanSelector(
            self.axes,
            self._on_span_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.5, facecolor="tab:orange"),
            interactive=True,
            drag_from_anywhere=True
        )
        # Not working, span activated by default
        # self.canvas.mpl_connect('key_press_event', self._toggle_span_selector)



    def clear(self) -> None:
        """
        Clear the axes.
        """
        self.axes.clear()

    def draw(self) -> None:
        """
        Plot the currently selected layers.
        """
        data, x_axis_name, y_axis_name = self._get_data()
        ################
        # Somewhere here I must get to which axes to plot
        ###############
        if len(data) == 0:
            # don't plot if there isn't data
            return
        self._lines = []
        x_data = data[0]
        y_data = data[1]

        if len(y_data) < len(x_data):
            print("x_data bigger than y_data, plotting only first y_data")
        for i, y in enumerate(y_data):
            if len(x_data) == 1:
                line = self.axes.plot(x_data[0], y, alpha=self._line_alpha)
            else:
                line = self.axes.plot(x_data[i], y, alpha=self._line_alpha)
            self._lines += line

        self.axes.set_xlabel(x_axis_name)
        self.axes.set_ylabel(y_axis_name)

    def _get_data(self) -> Tuple[List[np.ndarray], str, str]:
        """Get the plot data.

        This must be implemented on the subclass.

        Returns
        -------
        data : np.ndarray
            The list containing the line plot data.
        x_axis_name : str
            The label to display on the x axis
        y_axis_name: str
            The label to display on the y axis
        """
        raise NotImplementedError

    def _on_span_select(self, xmin, xmax):
        """
        Get xmin and xmax of selection
        """
        print(xmin, xmax)
        raise NotImplementedError

    def my_selection(self, *args):
        if self.span_selector.active:
            print('Span deactivated.')
            self.span_selector.set_active(False)
        else:
            print('Span activated.')
            self.span_selector.set_active(True)

class MetadataLine2DWidget(Line2DBaseWidget):
    n_layers_input = Interval(1, 1)

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)
        self.setMinimumSize(200, 200)
        self._plugin_name_widget = magicgui(
            self._set_plugin_name,
            plugin_name={"choices": self._get_plugin_metadata_key},
            auto_call = True,
        )
        self._key_selection_widget = magicgui(
            self._set_axis_keys,
            x_axis_key={"choices": self._get_valid_axis_keys},
            y_axis_key={"choices": self._get_valid_axis_keys},
            call_button="plot",
        )
        
        # self.ray_index = 0
        # self.dot_index = 0
        self.layout().insertWidget(0, self._plugin_name_widget.native)
        self.layout().addWidget(self._key_selection_widget.native)

        image_file_path = os.path.join(ICON_ROOT, "Select.png")
        self.toolbar._add_new_button('Select', 'Span Selection', image_file_path, self.my_selection2)

        # print('TOOLITEMS = ', self.toolbar.toolitems)

        # self.toolbar._add_new_button('Select', 'Span Selection', 'select', 'my_selection')

    def my_selection2(self):
        print('I am myselection2!!')

    @property
    def x_axis_key(self) -> Optional[str]:
        """Key to access x axis data from the Metadata"""
        return self._x_axis_key

    @x_axis_key.setter
    def x_axis_key(self, key: Optional[str]) -> None:
        self._x_axis_key = key
        self._draw()

    @property
    def y_axis_key(self) -> Optional[str]:
        """Key to access y axis data from the Metadata"""
        return self._y_axis_key

    @y_axis_key.setter
    def y_axis_key(self, key: Optional[str]) -> None:
        self._y_axis_key = key
        self._draw()

    def _set_axis_keys(self, x_axis_key: str, y_axis_key: str) -> None:
        """Set both axis keys and then redraw the plot"""
        self._x_axis_key = x_axis_key
        self._y_axis_key = y_axis_key
        self._draw()
        
    @property
    def plugin_name_key(self) -> Optional[str]:
        """Key to plugin dictionary in the Metadata"""
        return self._plugin_name_key

    @plugin_name_key.setter
    def plugin_name_key(self, key: Optional[str]) -> None:
        self._plugin_name_key = key
        
    def _set_plugin_name(self, plugin_name: str) -> None:
        """Set plugin name from layer metadata"""
        self._plugin_name_key = plugin_name
        self._key_selection_widget.reset_choices()
    
    def _get_plugin_metadata_key(
            self, combo_widget: Optional[ComboBox] = None
        ) -> List[str]:
        """Get plugin key from layer metadata"""
        if len(self.layers) == 0:
            return []
        else:
            return self._get_valid_metadata_keys() 

    def _get_valid_metadata_keys(
            self) -> List[str]:
        """Get metadata keys if nested dictionaries"""
        if len(self.layers) == 0:
            return []
        else:
            metadata = self.layers[0].metadata
            keys_with_nested_dicts = []
            for key, value in metadata.items():
                if isinstance(value, dict):
                    keys_with_nested_dicts.append(key)
            return keys_with_nested_dicts

    def _get_valid_axis_keys(
        self, combo_widget: Optional[ComboBox] = None
    ) -> List[str]:
        """
        Get the valid axis keys from the layer Metadata.
        Returns
        -------
        axis_keys : List[str]
            The valid axis keys in the Metadata. If the table is empty
            or there isn't a table, returns an empty list.
        """
        
        if len(self.layers) == 0:
            return []
        else:
            valid_metadata = self._get_valid_metadata_keys()
            if not valid_metadata:
                return []
            else:
                if not hasattr(self, "plugin_name_key"):
                    self.plugin_name_key = self._get_valid_metadata_keys()[0]
                return self.layers[0].metadata[self.plugin_name_key].keys()

    def _get_data(self) -> Tuple[List[np.ndarray], str, str]:
        """Get the plot data.
        Returns
        -------
        data : List[np.ndarray]
            List contains X and Y columns from the FeatureTable. Returns
            an empty array if nothing to plot.
        x_axis_name : str
            The title to display on the x axis. Returns
            an empty string if nothing to plot.
        y_axis_name: str
            The title to display on the y axis. Returns
            an empty string if nothing to plot.
        """
        valid_metadata = self._get_valid_metadata_keys()
        
        if (
            (not valid_metadata)
            or (self.x_axis_key is None)
            or (self.y_axis_key is None)
        ):
            return [], "", ""
        
        if not hasattr(self, "plugin_name_key"):
            self.plugin_name_key = valid_metadata[0]

        plugin_metadata_dict = self.layers[0].metadata[self.plugin_name_key]

        data_x = warp_to_list(plugin_metadata_dict[self.x_axis_key])
        data_y = warp_to_list(plugin_metadata_dict[self.y_axis_key])
        data = [data_x, data_y]

        x_axis_name = self.x_axis_key.replace("_", " ")
        y_axis_name = self.y_axis_key.replace("_", " ")

        return data, x_axis_name, y_axis_name

    def _on_update_layers(self) -> None:
        """
        This is called when the layer selection changes by
        ``self.update_layers()``.
        """
        if hasattr(self, "_key_selection_widget"):
            self._plugin_name_widget.reset_choices()
            self._key_selection_widget.reset_choices()
        
        # reset the axis keys
        self._x_axis_key = None
        self._y_axis_key = None
        
def warp_to_list(data):
    if isinstance(data, list):
        return data
    # If numpy array, make a list from axis=0
    if isinstance(data, np.ndarray):
        if len(data.shape) == 1:
            data = data[np.newaxis,:]
        data = data.tolist()
    # If pandas dataframe, make a list from columns
    if isinstance(data, pd.DataFrame):
        data = data.T.values.tolist()
    return data


## TO DO: Add method to add/remove axes subplots (and add new dropdowns for y axis)
    
# class My_Line:
#     '''Custom line class to store line data when axes are re-created'''
#     def __init__(self,x,y,color):
#         self.x = x
#         self.y = y
#         self.color = color
# class My_Axes(My_Line):
#     '''Custom axes class to store axes info when axes are re-created'''
#     def __init__(self):
#         self.lines = []
#     def _add_line(self,line):
#         self.lines.append(line)

# class MplCanvas(FigureCanvas):
#     """
#     Defines the canvas of the matplotlib window
#     """
#     def __init__(self):
#         self.fig = Figure()                         # create figure
#         self.previous_axes_list = []
#         self._add_axes(1)
#         FigureCanvas.__init__(self, self.fig)       # initialize canvas
#         FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,
#                                     QtWidgets.QSizePolicy.Expanding)
#         FigureCanvas.updateGeometry(self)
#         self.previous_axes_list = []

#     def _match_napari_layout(self, idx,color='white'):
#         self.fig.set_facecolor('#00000000')
#         # changing color of plot background to napari main window color
#         self.fig.axes[idx].set_facecolor('#00000000')

#         # changing colors of all axis
#         self.fig.axes[idx].spines['bottom'].set_color(color)
#         self.fig.axes[idx].spines['top'].set_color(color)
#         self.fig.axes[idx].spines['right'].set_color(color)
#         self.fig.axes[idx].spines['left'].set_color(color)

#         self.fig.axes[idx].xaxis.label.set_color(color)
#         self.fig.axes[idx].yaxis.label.set_color(color)

#         # changing colors of axis labels
#         self.fig.axes[idx].tick_params(axis='x', colors=color)
#         self.fig.axes[idx].tick_params(axis='y', colors=color)

#     def _add_axes(self,N):
#         '''adds (or removes) axes and replots previous data'''
#         if len(self.fig.axes)>0:
#             self.previous_axes_list = []
#             for ax in self.fig.axes:
#                 previous_axes = My_Axes()
#                 for line in ax.lines:
#                     previous_line = My_Line(x = line.get_xdata(),
#                                             y = line.get_ydata(),
#                                             color = line.get_color())
#                     previous_axes._add_line(previous_line)
#                 self.previous_axes_list.append(previous_axes)
#                 ax.remove()

#         gs = self.fig.add_gridspec(N, 1,hspace=0)
#         for i in range(N):
#             ax1 = self.fig.add_subplot(gs[i])
#             ax1.set_picker(True)
#             try:
#                 for line in self.previous_axes_list[i].lines:
#                     ax1.plot(line.x,line.y,color=line.color)
#             except IndexError:
#                 pass
#             self._match_napari_layout(i)