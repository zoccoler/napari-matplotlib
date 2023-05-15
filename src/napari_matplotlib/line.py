from typing import List, Optional, Tuple

import matplotlib.colors as mcolor
import napari
import numpy as np
import pandas as pd
from magicgui import magicgui
from magicgui.widgets import ComboBox
import os
from pathlib import Path
from matplotlib.lines import Line2D
from qtpy.QtCore import Qt
from qtpy.QtGui import QGuiApplication

from .base import NapariMPLWidget
from .util import Interval
from matplotlib.widgets import SpanSelector

ICON_ROOT = Path(__file__).parent / "icons"
__all__ = ["Line2DBaseWidget", "MetadataLine2DWidget"]

# Define a custom subclass of Line2D with a custom property


class InteractiveLine2D(Line2D):
    def __init__(self, *args, selected=False, **kwargs, ):
        super().__init__(*args, **kwargs)
        self._selected = None

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        if value == True:
            self.set_linestyle('--')
        elif value == False:
            self.set_linestyle('-')
        self.figure.canvas.draw_idle()


class Line2DBaseWidget(NapariMPLWidget):
    # opacity value for the lines
    _line_alpha = 0.5
    _lines = []

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)

        self.axes = self.canvas.figure.subplots()
        self.update_layers(None)

        # Initial states of interactive tools.
        self.span_selector = None
        self.span_selection_active = False

        self.legend_selection_active = False

        self.pick_event_connection_id = None
        self.mouse_click_event_connection_id = None

    def clear(self) -> None:
        """
        Clear the axes.
        """
        self.axes.clear()

    def draw(self) -> None:
        """
        Plot the currently selected layers.

        Get data and axes names. Plot every y_data vs x_data.
        """
        data, x_axis_name, y_axis_name = self._get_data()

        if len(data) == 0:
            # don't plot if there isn't data
            return
        self._lines = []
        x_data = data[0]
        y_data = data[1]

        if len(y_data) < len(x_data):
            print("x_data bigger than y_data, plotting only first y_data")
        for i, y in enumerate(y_data):
            label_name = y_axis_name
            if len(y_data) > 1:
                label_name += '_' + str(i)
            if len(x_data) == 1:
                line = InteractiveLine2D(
                    x_data=x_data[0], ydata=y, alpha=self._line_alpha, label=label_name, linestyle='-', picker=True, pickradius=5)
                self.axes.add_line(line)
                # line = self.axes.plot(
                #     x_data[0], y, alpha=self._line_alpha, label=label_name)
            else:
                line = InteractiveLine2D(
                    xdata=x_data[i], ydata=y, alpha=self._line_alpha, label=label_name, linestyle='-', picker=True, pickradius=5)
                self.axes.add_line(line)
                # line = self.axes.plot(
                #     x_data[i], y, alpha=self._line_alpha, label=label_name, color='red', linestyle='--')
            self._lines += [line]
        self.axes.set_xlabel(x_axis_name)
        self.axes.set_ylabel(y_axis_name)
        self.axes.autoscale(enable=True, axis='both', tight=True)

        # If legend_selection is enabled, store relation between legend lines and lines
        # and makes legend lines pickable
        if self.legend_selection_active:
            self.legend = self.axes.legend(fancybox=True, shadow=True)
            self.legend2line = {}  # Will map legend lines to original lines.
            for legend_line, original_line in zip(self.legend.get_lines(), self._lines):
                # Enable picking on the legend line.
                legend_line.set_picker(True)
                self.legend2line[legend_line] = original_line

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

    def _on_pick(self, event):
        """Callback function to pick event.

        This must be implemented on the subclass.
        Must filter artists if multiple can be picked by evaluating `event.artist` type.

        """
        raise NotImplementedError

    def _create_span_selector(self, active=False,
                              *args, **kwargs):
        """
        Create span selector.

        Also, define inital state.
        """
        self.span_selector = SpanSelector(**kwargs)
        self.span_selector.active = active
        self.span_selection_active = active

    def _enable_span_selector(self, active=False):
        """
        Enable or disable span selector.

        If span selector was created, enable or disable it.
        """
        if self.span_selector is not None:
            self.span_selector.active = active
            self.span_selection_active = active

    def _on_span_select(self, xmin, xmax):
        """
        This must be implemented on the subclass.

        Get xmin and xmax of selection
        """
        raise NotImplementedError

    def _enable_legend_selector(self, active=False):
        """
        Enable or disable making legend pickable.

        This activates a global 'pick_event' for all artists.
        Filter picked artist in `_on_pick` callback function.
        """
        self.legend_selection_active = active
        if active:
            if self.pick_event_connection_id is None:
                # `_on_pick` callback function must be implemented
                self.pick_event_connection_id = self.canvas.figure.canvas.mpl_connect(
                    'pick_event', self._on_pick)

    def _enable_mouse_clicks(self, active=False):
        """
        Enable/disable mouse clicks.

        Link mouse clicks to `onclick` callback function
        """
        if active:
            if self.mouse_click_event_connection_id is None:
                self.mouse_click_event_connection_id = self.canvas.figure.canvas.mpl_connect(
                    'button_press_event', self._on_click)
        else:
            if self.mouse_click_event_connection_id is not None:
                print('Warning: disabling mouse clicks event')
                self.canvas.figure.canvas.mpl_disconnect(
                    self.mouse_click_event_connection_id)

    def _clear_selections(self):
        """
        This must be implemented on the subclass.

        Clear plot selections.
        """
        raise NotImplementedError

    def _on_click(self, event):
        """
        Callback function from mouse clicks.

        By default, print click info 
        (see https://matplotlib.org/stable/users/explain/event_handling.html#event-connections)
        """
        if event.xdata is not None:
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))


class MetadataLine2DWidget(Line2DBaseWidget):
    n_layers_input = Interval(1, 1)

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)
        self.setMinimumSize(200, 200)
        self._plugin_name_widget = magicgui(
            self._set_plugin_name,
            plugin_name={"choices": self._get_plugin_metadata_key},
            auto_call=True,
        )
        self._key_selection_widget = magicgui(
            self._set_axis_keys,
            x_axis_key={"choices": self._get_valid_axis_keys},
            y_axis_key={"choices": self._get_valid_axis_keys},
            call_button="plot",
        )

        self.layout().insertWidget(0, self._plugin_name_widget.native)
        self.layout().addWidget(self._key_selection_widget.native)

        # Add span selection button to toolbar
        image_file_path = os.path.join(ICON_ROOT, "Select.png")
        self.toolbar._add_new_button(
            'Select', 'Span Selection', image_file_path, self.enable_span_selector, True)
        # Cache lists
        self._selected_span_intervals = []
        self._selected_lines = []

        # Create horizontal Span Selector
        self._create_span_selector(ax=self.axes,
                                   onselect=self._on_span_select,
                                   direction="horizontal",
                                   useblit=True,
                                   props=dict(
                                       alpha=0.5, facecolor="tab:orange"),
                                   interactive=False,
                                   button=1,
                                   drag_from_anywhere=True)

        # Enable legend selection
        self._enable_legend_selector(True)
        # Enable mouse clicks
        self._enable_mouse_clicks(active=True)

    def _on_click(self, event):
        # Right click clears selections
        if event.button == 3:
            self._clear_selections()

    def _clear_selections(self):
        # Clear legend line selection
        if self.legend_selection_active:
            self._selected_lines = []
            for line, legend_line in zip(self._lines, self.legend.get_lines()):
                # Restore the alpha on the line in the legend
                legend_line.set_alpha(self._line_alpha)
                # Restore line visibility
                line.set_visible(True)
        # Clear span selections if span selector exists
        if self.span_selector is not None:
            self._on_span_select(0, 0)
        self.canvas.figure.canvas.draw()

    # Callback function from toolbar span selection toggle button
    def enable_span_selector(self):
        self.toolbar._update_buttons_checked(button_name='Select')
        self._enable_span_selector(active=self.toolbar.button_state)

    # def _on_legend_selection(self, selected_artist):
    #     modifiers = QGuiApplication.keyboardModifiers()
    #     # If 'shift' holded, do not clear previously selected lines
    #     if modifiers == Qt.ShiftModifier:
    #         pass
    #     else:
    #         self._selected_lines = []
    #     # On the pick event, find the original line corresponding to the legend
    #     # proxy line, and make it visible, while other become invisible.
    #     selected_legend_line = selected_artist
    #     selected_original_line = self.legend2line[selected_legend_line]

    #     for line, legend_line in zip(self._lines, self.legend.get_lines()):
    #         if line == selected_original_line:
    #             # Change the alpha on the line in the legend
    #             legend_line.set_alpha(1.0)
    #             line.set_visible(True)
    #             # Add line to selected lines
    #             if line not in self._selected_lines:
    #                 self._selected_lines.append(line)
    #         else:
    #             # only hide if line was not pre-selected
    #             if line not in self._selected_lines:
    #                 legend_line.set_alpha(0.2)
    #                 line.set_visible(False)
    #     self.canvas.figure.canvas.draw()

    def _on_pick(self, event):
        artist = event.artist
        legend_line = None
        if isinstance(artist, Line2D):
            # Checks that picked line is in legend
            # https://stackoverflow.com/a/71818208/11885372
            if artist not in artist.axes.get_children():
                legend_line = artist
                line = self.legend2line[artist]

                # self._on_legend_selection(artist)
            else:
                line = artist
                if self.legend_selection_active:
                    legend_line = self.legend.get_lines()[
                        self._lines.index(line)]

            # Then line was directly picked
            if line.selected == True:
                line.selected = False
                # Remove line to selected lines
                if line in self._selected_lines:
                    self._selected_lines.remove(line)
                # If legend, restore continuous line style
                if legend_line is not None:
                    legend_line.set_linestyle('-')

            else:
                line.selected = True
                # Add line to selected lines
                if line not in self._selected_lines:
                    self._selected_lines.append(line)
                # If legend, change legend line style
                if legend_line is not None:
                    legend_line.set_linestyle('--')

        print('Selected lines: ', self._selected_lines)
        self.canvas.figure.canvas.draw_idle()

    def _on_span_select(self, xmin, xmax):
        self.clear()
        self.draw()
        modifiers = QGuiApplication.keyboardModifiers()

        # If lines were drawn
        if len(self._lines) > 0:
            # If 'shift' holded, do not clear previously selected intervals
            if modifiers == Qt.ShiftModifier:
                pass
            else:
                self._selected_span_intervals = []

            # Get regions for each line
            for i, line in enumerate(self._lines):
                x = line.get_xdata()
                indmin, indmax = np.searchsorted(x, (xmin, xmax))
                indmax = min(len(x) - 1, indmax)

                region_x = x[indmin:indmax]

                # If at least 2 points in interval
                if len(region_x) >= 2:
                    y = line.get_ydata()
                    region_y = y[indmin:indmax]

                    # If 'shift' holded, concatenate to previous array
                    # TO DO: test if data is not a numpy array
                    if (modifiers == Qt.ShiftModifier) and (len(self._selected_span_intervals) == len(self._lines)):
                        # Plot and store selected points/line
                        # interval = InteractiveLineInterval2D(xdata=self.axes.plot(np.concatenate((self._selected_span_intervals[i].get_xdata(), region_x)),
                        #                         ydata=np.concatenate((self._selected_span_intervals[i].get_ydata(), region_y)),
                        #                         alpha=self._line_alpha, markerstyle='o', picker=True, pickradius=5)
                        # self.axes.add_line(line)
                        selected_interval = self.axes.plot(np.concatenate((self._selected_span_intervals[i].get_xdata(), region_x)),
                                                           np.concatenate((self._selected_span_intervals[i].get_ydata(), region_y)), 'o')
                        # it needs index 0, otherwise inserts unitary list
                        self._selected_span_intervals[i] = selected_interval[0]
                    else:
                        selected_interval = self.axes.plot(
                            region_x, region_y, 'o')
                        self._selected_span_intervals += selected_interval
            self.canvas.draw_idle()

            # Store selected regions in new metadata key
            self.layers[0].metadata[self.plugin_name_key]['selected_interval_' +
                                                          self.x_axis_key] = [line.get_xdata() for line in self._selected_span_intervals]
            self.layers[0].metadata[self.plugin_name_key]['selected_interval_' +
                                                          self.y_axis_key] = [line.get_ydata() for line in self._selected_span_intervals]

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
            data = data[np.newaxis, :]
        data = data.tolist()
    # If pandas dataframe, make a list from columns
    if isinstance(data, pd.DataFrame):
        data = data.T.values.tolist()
    return data
