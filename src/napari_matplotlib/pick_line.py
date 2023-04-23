import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

# Define a custom subclass of Line2D with a custom property
class MyLine2D(mlines.Line2D):
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

fig, ax = plt.subplots()
ax.set_title('click on points')

x = np.arange(100)
y = np.random.rand(100)

line = MyLine2D(x, y, linestyle='-', marker='*', picker=True, pickradius=5)
ax.add_line(line)


# line, = ax.plot(x, y, '-*',
#                 picker=True, pickradius=5)  # 5 points tolerance

y2 = np.random.rand(100)
line2 = MyLine2D(x, y2, linestyle='-', marker='*', picker=True, pickradius=5, color='orange')
ax.add_line(line2)
ax.set_xlim(min(x), max(x))
ax.set_ylim(np.amin(np.concatenate([y, y2])), np.amax(np.concatenate([y, y2])))

def onpick(event):
    # Event attributes
    print(event.name)
    print(event.canvas)
    print(event.guiEvent)
    # If KeyEvent or MouseEvent, some extra attributes are:
    # x, y, inaxes, xdata, ydata
    # they also have the following
    # button (right, left, etc), key (SHIFT, any character, etc)

    # PickEvent always has these attributes:
    # mouseevent
    # artist
    # Certain events (like Line2D and PatchCollection) have additional metadata such as pickradius
    # For example, Line2D attaches the ind property, which are the indices into the line data under the pick point
    thisline = event.artist
    xdata = thisline.get_xdata()
    ydata = thisline.get_ydata()
    ind = event.ind
    points = tuple(zip(xdata[ind], ydata[ind]))
    print('onpick points:', points)

    if thisline.selected == True:
        thisline.selected = False
    else:
        thisline.selected = True
    print(thisline.selected)



fig.canvas.mpl_connect('pick_event', onpick)

plt.show()