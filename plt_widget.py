"""primary widget and functions for creating matplotlib data plots"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout) # pylint: disable=E0611
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure


class PltWidget(QWidget):
    """ used to create a matplotlib plot"""
    def __init__(self,parent=None,title=None,xlabel=None,ylabel=None,legend_state=None):
        """
        initialize class

        Parameters:
            parent (class): self from parent calling this class
            title (str): plot title
            xlabel (str): plot x-axis label
            ylabel (str): plot y-axis label
            legend_state (dict): previous legend settings
        
        Returns:
            None.
        """

        super().__init__(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_visible(False)
        self._release=None

        if legend_state:
            self.legend_state=legend_state
        else:
            self.legend_state=None

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.curves = {}

        # Axis titles and labels
        if title:
            self.set_title(title)
        if xlabel:
            self.set_xlabel(xlabel)
        if ylabel:
            self.set_ylabel(ylabel)

        self.figure.tight_layout()

    def _update_legend(self):
        """
        updates the plot legend

        Parameters:
            None.
        
        Returns:
            None.
        """

        legend = self.ax.get_legend()
        if not legend:
            legend = self.ax.legend()
            legend.set_draggable(True)

            self._release = self.canvas.mpl_connect(
            "button_release_event", self._wrapped_legend)

        if self.curves:
            self.ax.set_visible(True)
            legend.set_visible(True)
        else:
            legend.set_visible(False)
            self.ax.set_visible(False)

    def _wrapped_legend(self,event): #pylint: disable=W0613
        """
        helper function to assign to button release event

        Parameters:
            event (QEvent): button release event
        
        Returns:
            None.
        """

        self.get_legend_pos()

    def get_legend_pos(self):
        """
        function to get legend state variables

        Parameters:
            None.
        
        Returns:
            None.
        """

        ax=self.ax
        leg=ax.get_legend()
        loc=leg._get_loc() #pylint: disable=W0212
        bbox = leg.get_bbox_to_anchor()
        bbox_axes = bbox.transformed(ax.transAxes.inverted())
        self.legend_state={'loc':loc,'bbox':bbox_axes.bounds}

    def set_legend_pos(self):
        """
        function to set legend state variables

        Parameters:
            None.
        
        Returns:
            None.
        """

        if not self.legend_state:
            return

        state=self.legend_state
        self._update_legend()
        legend=self.ax.get_legend()
        legend.set_loc(state['loc'])
        legend.set_bbox_to_anchor(state['bbox'], transform=self.ax.transAxes)
        self.ax.relim()
        self.ax.autoscale_view()
        self.figure.tight_layout()
        self.canvas.draw_idle()


    def add_curve(self,x,y,label=None,legend=None,
                linestyle='-',marker=None,color='black'):
        """
        adds a curve without clearing existing ones

        Parameters:
            x,y (list, ndarray): x and y data to plot
            label (str): curve label in self.curves
            legend (str): curve label in legend
            linestyle (str): line style for plot
            marker (str): marker designation for curve
            color (str): color of curve
        
        Returns:
            None.
        """

        if label in self.curves:
            curve = self.curves[label]
            curve.set_data(x,y)
            curve.set_linestyle(linestyle)
            curve.set_marker(marker)
            curve.set_color(color)
            curve.set_label(legend)
        else:
            curve,=self.ax.plot(x,y,label=legend,linestyle=linestyle,
                                marker=marker,color=color)

            self.curves[label] = curve

        self._update_legend()
        self.ax.relim()
        self.ax.autoscale_view()
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def remove_curve(self, label):
        """
        removes a curve from the plot

        Parameters:
            label (str): curve label in self.curves

        
        Returns:
            None.
        """

        if label in self.curves:
            curve = self.curves.pop(label)
            curve.remove()
            self._update_legend()
            self.ax.relim()
            self.ax.autoscale_view()
            self.figure.tight_layout()
            self.canvas.draw_idle()

    def set_title(self, title):
        """
        sets the plot title

        Parameters:
            title (str): plot title

        Returns:
            None.
        """

        self.title = title
        self.ax.set_title(title, fontweight="bold")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def set_xlabel(self, xlabel):
        """
        sets the plot xlabel

        Parameters:
            title (str): X-axis label

        Returns:
            None.
        """

        self.xlabel = xlabel
        self.ax.set_xlabel(xlabel, fontweight="bold")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def set_ylabel(self, ylabel):
        """
        sets the plot ylabel

        Parameters:
            title (str): Y-axis label

        Returns:
            None.
        """

        self.ylabel = ylabel
        self.ax.set_ylabel(ylabel, fontweight="bold")
        self.figure.tight_layout()
        self.canvas.draw_idle()
