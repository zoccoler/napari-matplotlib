import os
from pathlib import Path
from typing import List, Tuple

import matplotlib as mpl
import napari
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QVBoxLayout, QWidget
import warnings

from .util import Interval

mpl.rc("axes", edgecolor="white")
mpl.rc("axes", facecolor="#262930")
mpl.rc("axes", labelcolor="white")
mpl.rc("savefig", facecolor="#262930")
mpl.rc("text", color="white")

mpl.rc("xtick", color="white")
mpl.rc("ytick", color="white")

# Icons modified from
# https://github.com/matplotlib/matplotlib/tree/main/lib/matplotlib/mpl-data/images
ICON_ROOT = Path(__file__).parent / "icons"
__all__ = ["NapariMPLWidget"]


class NapariMPLWidget(QWidget):
    """
    Base widget that can be embedded as a napari widget and contains a
    Matplotlib canvas.

    This creates a single FigureCanvas, which contains a single Figure.

    This class also handles callbacks to automatically update figures when
    the layer selection or z-step is changed in the napari viewer. To take
    advantage of this sub-classes should implement the ``clear()`` and
    ``draw()`` methods.

    Attributes
    ----------
    viewer : `napari.Viewer`
        Main napari viewer.
    figure : `matplotlib.figure.Figure`
        Matplotlib figure.
    canvas : matplotlib.backends.backend_qt5agg.FigureCanvas
        Matplotlib canvas.
    layers : `list`
        List of currently selected napari layers.
    """

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()

        self.viewer = napari_viewer
        self.canvas = FigureCanvas()
        self.canvas.figure.set_tight_layout(True)
        self.canvas.figure.patch.set_facecolor("#262930")
        self.toolbar = NapariNavigationToolbar(self.canvas, self)
        self._replace_toolbar_icons()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

        self.setup_callbacks()
        self.layers: List[napari.layers.Layer] = []

        # List of cached axes
        self.previous_axes_list = []

    # Accept any number of input layers by default
    n_layers_input = Interval(None, None)
    # Accept any type of input layer by default
    input_layer_types: Tuple[napari.layers.Layer, ...] = (napari.layers.Layer,)

    @property
    def n_selected_layers(self) -> int:
        """
        Number of currently selected layers.
        """
        return len(self.layers)

    @property
    def current_z(self) -> int:
        """
        Current z-step of the viewer.
        """
        return self.viewer.dims.current_step[0]

    def setup_callbacks(self) -> None:
        """
        Setup callbacks for:
        - Layer selection changing
        - z-step changing
        """
        # z-step changed in viewer
        self.viewer.dims.events.current_step.connect(self._draw)
        # Layer selection changed in viewer
        self.viewer.layers.selection.events.changed.connect(self.update_layers)

    def update_layers(self, event: napari.utils.events.Event) -> None:
        """
        Update the layers attribute with currently selected layers and re-draw.
        """
        self.layers = list(self.viewer.layers.selection)
        self._on_update_layers()
        self._draw()

    def _draw(self) -> None:
        """
        Clear current figure, check selected layers are correct, and draw new
        figure if so.
        """
        self.clear()
        if self.n_selected_layers in self.n_layers_input and all(
            isinstance(layer, self.input_layer_types) for layer in self.layers
        ):
            self.draw()
        self.canvas.draw()

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """

    def draw(self) -> None:
        """
        Re-draw any figures.

        This is a no-op, and is intended for derived classes to override.
        """

    def _on_update_layers(self) -> None:
        """
        This function is called when self.layers is updated via
        ``self.update_layers()``.

        This is a no-op, and is intended for derived classes to override.
        """

    # def _change_grid_axes(self, new_rows=1, new_cols=1):
    #     # Get current gridspec and number of rows
    #     gs = self.canvas.figure.axes[0].get_gridspec()
    #     rows = gs.get_geometry()[0]
    #     cols = gs.get_geometry()[1]


    #     if (new_rows < 1) or (new_cols < 1):
    #         print('Cannot remove first row or column axis.')
    #         return
    #     rows_diff = new_rows - rows
    #     cols_diff = new_cols - cols
    #     # Create a new gridspec, with an increment to the number of rows
    #     new_gs = self.canvas.figure.add_gridspec(new_rows, new_cols)
    #     # Work in progress...


    def _remove_row_axis(self):
        '''adds (or removes) axes and replots previous data'''
        
        # Get current gridspec and number of rows
        gs = self.canvas.figure.axes[0].get_gridspec()
        nrows = gs.get_geometry()[0]    
        if nrows == 1:
            print('Cannot remove first row axis.')
            return 

        # Create a new gridspec, with an increment to the number of rows
        new_gs = self.canvas.figure.add_gridspec(gs.get_geometry()[0] - 1, gs.get_geometry()[1])

        # Previous axes must be removed before adding new axes
        # A copy of previous axes (and artists, like lines) is stored
        # TO DO: store other artists besides lines (filter ax.get_children())
        if len(self.canvas.figure.axes)>0:
            self.previous_axes_list = []
            for ax in self.canvas.figure.axes:
                previous_axes = Cached_Axes()
                for line in ax.lines:
                    previous_line = Cached_Line(x = line.get_xdata(),
                                            y = line.get_ydata(),
                                            color = line.get_color())
                    previous_axes._add_line(previous_line)
                self.previous_axes_list.append(previous_axes)
                ax.remove()
        
        # Add new axes and re-introduce previous lines (if any)
        for i in range(nrows-1):
            new_ax = self.canvas.figure.add_subplot(new_gs[i])
            # new_ax.set_picker(True) # option for axis to be clickable/pickable
            try:
                for line in self.previous_axes_list[i].lines:
                    new_ax.plot(line.x, line.y, color=line.color)
            except IndexError:
                pass
        self.canvas.draw_idle()


    def _add_row_axis(self):
        '''adds (or removes) axes and replots previous data'''
        print('Axes added')
        # Get current gridspec and number of rows
        gs = self.canvas.figure.axes[0].get_gridspec()
        nrows = gs.get_geometry()[0]    

        # Create a new gridspec, with an increment to the number of rows
        new_gs = self.canvas.figure.add_gridspec(gs.get_geometry()[0] + 1, gs.get_geometry()[1])

        # Previous axes must be removed before adding new axes
        # A copy of previous axes (and artists, like lines) is stored
        # TO DO: store other artists besides lines (filter ax.get_children())
        if len(self.canvas.figure.axes)>0:
            self.previous_axes_list = []
            for ax in self.canvas.figure.axes:
                previous_axes = Cached_Axes()
                for line in ax.lines:
                    previous_line = Cached_Line(x = line.get_xdata(),
                                            y = line.get_ydata(),
                                            color = line.get_color())
                    previous_axes._add_line(previous_line)
                self.previous_axes_list.append(previous_axes)
                ax.remove()
        # Add new axes and re-introduce previous lines (if any)
        for i in range(nrows+1):
            new_ax = self.canvas.figure.add_subplot(new_gs[i])
            # new_ax.set_picker(True) # option for axis to be clickable/pickable
            try:
                for line in self.previous_axes_list[i].lines:
                    new_ax.plot(line.x, line.y, color=line.color)
            except IndexError:
                pass
        self.canvas.draw_idle()


    def _replace_toolbar_icons(self):
        # Modify toolbar icons and some tooltips
        for action in self.toolbar.actions():
            text = action.text()
            if text == "Pan":
                action.setToolTip(
                    "Pan/Zoom: Left button pans; Right button zooms; "
                    "Click once to activate; Click again to deactivate"
                )
            if text == "Zoom":
                action.setToolTip(
                    "Zoom to rectangle; Click once to activate; "
                    "Click again to deactivate"
                )
            if len(text) > 0:  # i.e. not a separator item
                icon_path = os.path.join(ICON_ROOT, text + ".png")
                action.setIcon(QIcon(icon_path))


class Cached_Line:
    '''Custom line class to store line data when axes are re-created'''
    def __init__(self,x,y,color):
        self.x = x
        self.y = y
        self.color = color
class Cached_Axes(Cached_Line):
    '''Custom axes class to store axes info when axes are re-created'''
    def __init__(self):
        self.lines = []
    def _add_line(self,line):
        self.lines.append(line)

class NapariNavigationToolbar(NavigationToolbar2QT):
    """Custom Toolbar style for Napari."""

    def _update_buttons_checked(self):
        """Update toggle tool icons when selected/unselected."""
        super()._update_buttons_checked()
        # changes pan/zoom icons depending on state (checked or not)
        if "pan" in self._actions:
            if self._actions["pan"].isChecked():
                self._actions["pan"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Pan_checked.png"))
                )
            else:
                self._actions["pan"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Pan.png"))
                )
        if "zoom" in self._actions:
            if self._actions["zoom"].isChecked():
                self._actions["zoom"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Zoom_checked.png"))
                )
            else:
                self._actions["zoom"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Zoom.png"))
                )
