from typing import List, Optional, Tuple

import matplotlib.colors as mcolor
import napari
import numpy as np
import pandas as pd
from magicgui import magicgui
from magicgui.widgets import ComboBox

from .base import NapariMPLWidget
from .util import Interval

__all__ = ["Line2DBaseWidget", "MetadataLine2DWidget"]


class Line2DBaseWidget(NapariMPLWidget):
    # opacity value for the lines
    _line_alpha = 0.5
    _lines = []

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)

        self.axes = self.canvas.figure.subplots()
        self.update_layers(None)

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


class FeaturesLine2DWidget(Line2DBaseWidget):
    n_layers_input = Interval(1, 1)
    # All layers that have a .features attributes
    input_layer_types = (
        napari.layers.Labels,
    )
    x_axis_features = ['frame', 'time']

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__(napari_viewer)
        self._key_selection_widget = magicgui(
            self._set_axis_keys,
            x_axis_key={"choices": self._get_valid_axis_keys_x},
            y_axis_key={"choices": self._get_valid_axis_keys_y},
            call_button="plot",
        )

        self.layout().addWidget(self._key_selection_widget.native)
        self.layers[0].events.selected_label.connect(self.print_layer_name)

    def print_layer_name(self, event: napari.utils.events.Event) -> None:
        print("data!")
        if self.layers[0].show_selected_label:
            self._draw()

    @property
    def x_axis_key(self) -> Optional[str]:
        """Key to access x axis data from the FeaturesTable"""
        return self._x_axis_key

    @x_axis_key.setter
    def x_axis_key(self, key: Optional[str]) -> None:
        self._x_axis_key = key
        self._draw()

    @property
    def y_axis_key(self) -> Optional[str]:
        """Key to access y axis data from the FeaturesTable"""
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

    def _get_valid_axis_keys_y(
        self, combo_widget: Optional[ComboBox] = None
    ) -> List[str]:
        """
        Get the valid axis keys from the layer FeatureTable.

        Returns
        -------
        axis_keys : List[str]
            The valid axis keys in the FeatureTable. If the table is empty
            or there isn't a table, returns an empty list.
        """
        if len(self.layers) == 0 or not (hasattr(self.layers[0], "features")):
            return []
        else:
            return self.layers[0].features.keys()

    def _get_valid_axis_keys_x(
        self, combo_widget: Optional[ComboBox] = None
    ) -> List[str]:
        """
        Get the valid axis keys from the layer FeatureTable.

        Returns
        -------
        axis_keys : List[str]
            The valid axis keys in the FeatureTable. If the table is empty
            or there isn't a table, returns an empty list.
        """
        if len(self.layers) == 0 or not (hasattr(self.layers[0], "features")):
            return []
        else:
            features = self.layers[0].features
            time_related_column_names_in_features = get_column_names_matching_strings(features, self.x_axis_features)
            return time_related_column_names_in_features

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
        if not hasattr(self.layers[0], "features"):
            # if the selected layer doesn't have a featuretable,
            # skip draw
            return [], "", ""

        feature_table = self.layers[0].features

        if (
            (len(feature_table) == 0)
            or (self.x_axis_key is None)
            or (self.y_axis_key is None)
        ):
            return [], "", ""

        # Sort features by label and x_axis_key
        feature_table = feature_table.sort_values(by=['label', self.x_axis_key])
        labels = feature_table['label'].unique().tolist()

        # Get data for each label (data_x is the same for all labels)
        grouped = feature_table.groupby('label')
        data_x = [list(grouped)[0][1][self.x_axis_key].values]
        data_y = [sub_df[self.y_axis_key].values for label, sub_df in grouped]

        data = [data_x, data_y, labels]

        x_axis_name = self.x_axis_key.replace("_", " ")
        y_axis_name = self.y_axis_key.replace("_", " ")

        return data, x_axis_name, y_axis_name

    def _on_update_layers(self) -> None:
        """
        This is called when the layer selection changes by
        ``self.update_layers()``.
        """
        if hasattr(self, "_key_selection_widget"):
            self._key_selection_widget.reset_choices()

        # reset the axis keys
        self._x_axis_key = None
        self._y_axis_key = None

    def draw(self) -> None:
        """
        Plot the currently selected layers.
        """
        data, x_axis_name, y_axis_name = self._get_data()

        print(data, type(data), len(data))
        if len(data) == 0:
            # don't plot if there isn't data
            return
        self._lines = []
        x_data = data[0]
        y_data = data[1]
        labels = data[2]

        if len(y_data) < len(x_data):
            print("x_data bigger than y_data, plotting only first y_data")
        for i, y in enumerate(y_data):
            # If show_selected_label is True, only plot the selected label
            if self.layers[0].show_selected_label and i != self.layers[0].selected_label - 1:
                continue

            if len(x_data) == 1:
                line = self.axes.plot(x_data[0], y, color=self.layers[0].get_color(labels[i]), alpha=self._line_alpha)
            else:
                line = self.axes.plot(x_data[i], y, color=self.layers[0].get_color(labels[i]), alpha=self._line_alpha)

        self.axes.set_xlabel(x_axis_name)
        self.axes.set_ylabel(y_axis_name)

        self.canvas.draw()


def get_column_names_matching_strings(data, strings_list):
    if isinstance(data, pd.DataFrame):
        columns = data.columns
    elif isinstance(data, dict):
        columns = data.keys()
    else:
        raise ValueError("Invalid input data type. Supported types are DataFrame and dictionary.")

    lowercase_columns = [col.lower() for col in columns]
    lowercase_strings = [string.lower() for string in strings_list]

    matching_elements = []
    for string in lowercase_strings:
        if any(string in col for col in lowercase_columns):
            matching_elements.append(string)

    if matching_elements:
        return matching_elements
    else:
        return None


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
