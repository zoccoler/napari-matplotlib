import os
from pathlib import Path
from typing import List, Tuple

import matplotlib as mpl
import napari
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.backend_bases import NavigationToolbar2
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QVBoxLayout, QWidget, QAction, QLabel
from qtpy import QtCore, QtWidgets

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


class NapariNavigationToolbar(NavigationToolbar2QT):
    """Custom Toolbar style for Napari."""  
    def __init__(self, canvas, parent=None, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self.tb_canvas = canvas
        self.tb_parent = parent
        self.tb_coordinates = coordinates

    def _add_new_button(self, text, tooltip_text, image_file_path, callback, separator=True, checkable=False):
        """Add a new buttons to the toolbar.

        Parameters
        ----------
        text : str
            the text representing the name of the button
        tooltip_text : str
            the tooltip text exhibited when cursor hovers over button
        image_file_path : str
            path to the "png" file containing the button image
        callback : function
            function to be called when button is clicked
        separator: bool
            Whether to add a spacer before new button
        checkable: bool
            flag that indicates if button should or not be chackable
        """        
        self.toolitems.append((text, tooltip_text, image_file_path, callback))
        # Get last widget (A QLabel spacer)
        n_widgets = self.layout().count() # get number of widgets
        myWidget = self.layout().itemAt(n_widgets-1).widget() # get last widget
        # Remove last widget (the spacer)
        self.layout().removeWidget(myWidget)
        myWidget.deleteLater()
        if separator:
            # Add a separator
            self.addSeparator()
        # Add custom button (addAction from QToolBar)
        # https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QToolBar.html#PySide2.QtWidgets.PySide2.QtWidgets.QToolBar.addAction
        a = self.addAction(QIcon(image_file_path), text, callback)
        self._actions[text] = a
        if checkable:
            a.setCheckable(True)
        if tooltip_text is not None:
            a.setToolTip(tooltip_text)
       
        ## Rebuild spacer at the very end of toolbar (reuse 'locLabel' created by __init__ from NavigationToolbar2QT)
        # https://github.com/matplotlib/matplotlib/blob/85d7bb370186f2fa86df6ecc3d5cd064eb7f0b45/lib/matplotlib/backends/backend_qt.py#L631
        if self.tb_coordinates:
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)

    def _update_buttons_checked(self, button_name=None):
        """Update toggle tool icons when selected/unselected."""
        # super()._update_buttons_checked()
        # changes pan/zoom icons depending on state (checked or not)
        if "pan" in self._actions:
            self._actions['pan'].setChecked(self.mode.name == 'PAN')
            if self._actions["pan"].isChecked():
                self._actions["pan"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Pan_checked.png"))
                )
            else:
                self._actions["pan"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Pan.png"))
                )
        if "zoom" in self._actions:
            self._actions['zoom'].setChecked(self.mode.name == 'ZOOM')
            if self._actions["zoom"].isChecked():
                self._actions["zoom"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Zoom_checked.png"))
                )
            else:
                self._actions["zoom"].setIcon(
                    QIcon(os.path.join(ICON_ROOT, "Zoom.png"))
                )
        # If new button added and checkacble, update state and icon
        if button_name is not None:
            if button_name in self._actions:
                if self._actions[button_name].isChecked():
                    # Button was checked, update icon to checked
                    self._actions[button_name].setIcon(
                        QIcon(os.path.join(ICON_ROOT, button_name + "_checked.png"))
                        )
                    self._actions[button_name].setChecked(True)
                    
                else:
                    # Button unchecked
                    self._actions[button_name].setIcon(
                        QIcon(os.path.join(ICON_ROOT, button_name + ".png"))
                        )
                    self._actions[button_name].setChecked(False)