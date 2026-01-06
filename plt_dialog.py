""" Module for launching the plt_data_plot UI"""
from pathlib import Path
from tkinter import filedialog
import numpy as np
from PyQt5.QtWidgets import (QWidget,QApplication,QDialog,QListWidget) # pylint: disable=E0611
from PyQt5.QtCore import (Qt,QObject,QEvent) # pylint: disable=E0611
from PyQt5 import uic

class ShowTooltip(QObject):
    """ helper class for showing QListWidget tooltips"""
    def __init__(self, parent=None,tooltips=None):
        """
        initialize class

        Parameters:
            parent (class): self from parent calling this class
            tooltips (dict): tooltips to display when hovering over item
        
        Returns:
            None.
        """

        super().__init__(parent)
        self._last_hovered = None
        self.tooltips = tooltips

    def eventFilter(self, obj, event): # pylint: disable=C0103
        """
        implements hover behavior

        Parameters:
            obj (QObject): object receiving the event (QListWidget)
            event (QEvent): MouseMove event to be processed
        
        Returns:
            bool: result from calling eventFilter (False, continue)
        """

        if event.type() == QEvent.MouseMove and isinstance(obj.parent(),QListWidget):
            item = obj.parent().itemAt(event.pos())
            if item is not None and item != self._last_hovered:
                tooltip_text = self.tooltips.get(item.text(), "")
                if tooltip_text is not None:
                    item.setToolTip(tooltip_text)
                self._last_hovered = item
            elif item is None:
                self._last_hovered = None
        return super().eventFilter(obj, event)

class PltDialog(QDialog):
    """ dialog window for making x/y plots"""
    def __init__(self, parent=None,input_data=None,opts=None,tooltips=None):
        """
        initialize class

        Parameters:
            parent (class): self from parent calling this class
            input_data (dict): input data for plotting
            opts (dict): plot options for data
            tooltips (dict): optional tooltips to display over hovered items
        
        Returns:
            None.
        """

        super().__init__(parent)
        uic.loadUi("ui/plt_data_plot.ui", self)

        if opts:
            self.plotopts = opts['plot']
            self.chartopts = opts['chart']
            self.x_lineEdit.setText(self.chartopts['x_label'])
            self.y_lineEdit.setText(self.chartopts['y_label'])
            self.title_lineEdit.setText(self.chartopts['title'])
            self.change_title()
            self.change_xlabel()
            self.change_ylabel()
        else:
            self.plotopts = {}
            self.chartopts = {'x_label':'','y_label':'','title':''}

        if tooltips:
            self.tooltips = tooltips
        else:
            self.tooltips = {}

        if input_data:
            self.data = input_data
            # self.avail_data.blockSignals(True)
            for label in input_data.keys():
                self.avail_data.addItem(label)
                self.avail_data.setCurrentRow(self.avail_data.count() - 1)
                if label in self.plotopts:
                    self.change_plot()
            # self.avail_data.blockSignals(False)
            # self.avail_data.setCurrentRow(0)
        else:
            self.data = {}

        #set legend must be called after curves have been added to plot
        if opts:
            self.set_legend()

        self.hover = ShowTooltip(self,tooltips=self.tooltips)
        self.avail_data.viewport().setMouseTracking(True)
        self.avail_data.viewport().installEventFilter(self.hover)

    def keyPressEvent(self, event): #pylint: disable=C0103
        """
        Key press event handler

        Parameters:
            event (QEvent): triggered event from key press

        Returns:
            None.
        """

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Ignore Enter, particularly for QLineEdit (exits UI)
            event.ignore()
            return
        super().keyPressEvent(event)

    def _get_label(self):
        """
        helper function to get selected label

        Parameters:
            None.
        
        Returns:
            label (str): text of selected item in avail_data QListWidget
        """

        selected = [item.text() for item in self.avail_data.selectedItems()]
        return selected[0] if len(selected) == 1 else None

    def add_data_from_file(self):
        """
        callback function to add x-y data from file

        Parameters:
            None.
        
        Returns:
            None.
        """
        filename = filedialog.askopenfilenames(title="Select a *.data,*.csv results file...",
                                              filetypes=[("All files","*.data;*.csv"),
                                                        ("NASMAT file","*.data"),
                                                        ("CSV file","*.csv")])
        for file in filename:
            label=Path(file).stem
            ext = Path(file).suffix
            if label in self.data:
                label = label + "_1"

            if ext.lower()=='.data':
                self.data[label] = np.loadtxt(file)
            elif ext.lower()=='.csv':
                self.data[label] = np.loadtxt(file,delimiter=',')

            self.avail_data.addItem(label)
            self.tooltips[label]=file

    def rm_data(self):
        """
        callback function to remove selected x-y data

        Parameters:
            None.
        
        Returns:
            None.
        """

        label=self._get_label()
        if not label:
            return

        self.data.pop(label)
        if label in self.tooltips:
            self.tooltips.pop(label)
        self.rm_from_plot()
        item = self.avail_data.findItems(label,Qt.MatchExactly)
        if item:
            self.avail_data.takeItem(self.avail_data.row(item[0]))

    def add_to_plot(self):
        """
        callback function to add data to x-y plot

        Parameters:
            None.
        
        Returns:
            None.
        """

        label=self._get_label()
        if not label:
            return

        self.plotopts[label]={}
        self.flipX_pb.setEnabled(True)
        self.flipY_pb.setEnabled(True)
        self.change_plot()

    def rm_from_plot(self):
        """
        callback function to remove selected data from x-y plot

        Parameters:
            None.
        
        Returns:
            None.
        """

        label=self._get_label()
        if not label:
            return

        if label not in self.plotopts:
            return

        pltwidget=self.findChild(QWidget, "PltWidget")

        pltwidget.remove_curve(label=label)
        self.plotopts.pop(label)

        self.flipX_pb.setEnabled(False)
        self.flipY_pb.setEnabled(False)

        #reset plotopts if all data have been removed
        if not self.plotopts:
            self.color_cb.setCurrentIndex(0)
            self.marker_cb.setCurrentIndex(0)
            self.linestyle_cb.setCurrentIndex(0)
            self.legend_lineEdit.setText("")

    def flip_x(self):
        """
        callback function to change sign of x-axis data

        Parameters:
            None.
        
        Returns:
            None.
        """

        self.change_plot(flip_x=True)

    def flip_y(self):
        """
        callback function to change sign of y-axis data

        Parameters:
            None.
        
        Returns:
            None.
        """

        self.change_plot(flip_y=True)

    def change_plot(self,flip_x=False,flip_y=False):
        """
        callback function to change the x-y plot

        Parameters:
            flip_x (bool): logical to change the sign of X data
            flip_y (bool): logical to change the sign of y data
        
        Returns:
            None.
        """

        label=self._get_label()
        if not label:
            return

        if label not in self.plotopts:
            return

        if flip_x:
            self.data[label][:, 0] *= -1
        if flip_y:
            self.data[label][:, 1] *= -1

        x = self.data[label][:, 0]
        y = self.data[label][:, 1]

        color=self.color_cb.currentText()
        marker=self.marker_cb.currentText()
        ls=self.linestyle_cb.currentText()
        curve_name=self.legend_lineEdit.text().strip()
        if not curve_name:
            curve_name = label
            self.legend_lineEdit.setText(label)

        self.plotopts[label]={'c':self.color_cb.currentIndex(),
                                'm':self.marker_cb.currentIndex(),
                                'ls':self.linestyle_cb.currentIndex(),
                                'legend':curve_name}

        pltwidget=self.findChild(QWidget, "PltWidget")
        pltwidget.add_curve(x, y,label=label,legend=curve_name,
                            linestyle=ls,marker=marker,color=color)

    def set_plotopts(self):
        """
        callback function to set x-y plot options for a curve

        Parameters:
            None.
        
        Returns:
            None.
        """

        label=self._get_label()
        if not label:
            self.legend_lineEdit.setText("")
            return

        if label in self.plotopts:
            p = self.plotopts[label]
            self.color_cb.blockSignals(True)
            self.marker_cb.blockSignals(True)
            self.linestyle_cb.blockSignals(True)
            self.legend_lineEdit.blockSignals(True)

            self.color_cb.setCurrentIndex(p['c'])
            self.marker_cb.setCurrentIndex(p['m'])
            self.linestyle_cb.setCurrentIndex(p['ls'])
            self.legend_lineEdit.setText(p['legend'])

            self.color_cb.blockSignals(False)
            self.marker_cb.blockSignals(False)
            self.linestyle_cb.blockSignals(False)
            self.legend_lineEdit.blockSignals(False)

            self.flipX_pb.setEnabled(True)
            self.flipY_pb.setEnabled(True)
        else:
            self.legend_lineEdit.setText("")
            self.flipX_pb.setEnabled(False)
            self.flipY_pb.setEnabled(False)

    def change_title(self):
        """
        callback function to change the x-plot title

        Parameters:
            None.
        
        Returns:
            None.
        """

        pltwidget=self.findChild(QWidget, "PltWidget")
        title = self.title_lineEdit.text().strip()
        pltwidget.set_title(title)
        self.chartopts['title'] = title

    def change_xlabel(self):
        """
        callback function to change the x-plot xlabel

        Parameters:
            None.
        
        Returns:
            None.
        """

        pltwidget=self.findChild(QWidget, "PltWidget")
        label = self.x_lineEdit.text().strip()
        pltwidget.set_xlabel(label)
        self.chartopts['x_label'] = label

    def change_ylabel(self):
        """
        callback function to change the x-plot ylabel

        Parameters:
            None.
        
        Returns:
            None.
        """

        pltwidget=self.findChild(QWidget, "PltWidget")
        label=self.y_lineEdit.text().strip()
        pltwidget.set_ylabel(label)
        self.chartopts['y_label'] = label

    def set_legend(self):
        """
        callback function to set the legend position

        Parameters:
            None.
        
        Returns:
            None.
        """

        if 'legend_state' in self.chartopts:
            pltwidget=self.findChild(QWidget, "PltWidget")
            pltwidget.legend_state=self.chartopts['legend_state']
            pltwidget.set_legend_pos()

    def accept(self):
        """
        override default accept behavior to save legend_state

        Parameters:
            None.
        
        Returns:
            None.
        """

        pltwidget=self.findChild(QWidget, "PltWidget")
        pltwidget.get_legend_pos()
        self.chartopts['legend_state']=pltwidget.legend_state
        super().accept()

if __name__ == "__main__":
    import sys

    app = QApplication([])

    # sample plot for visualization
    xx = [0, 1, 2, 3, 4]
    yy = [0, 1, 4, 9, 16]
    xx2 = [0, 3, 4, 6, 12]
    yy2 = [0, 1, 2, 3, 14]
    data = {'test':np.column_stack((xx, yy)),
            'test2':np.column_stack((xx2, yy2))}
    popts = {'plot':{'test':{'c':0,'m':0,'ls':0,'legend':'test'},
                    'test2':{'c':3,'m':0,'ls':2,'legend':'test2'}},
            'chart':{'x_label':'X','y_label':'Y','title':'Sample Plot'}}
    w = PltDialog(input_data=data,opts=popts)
    w.show()
    sys.exit(app.exec_())
