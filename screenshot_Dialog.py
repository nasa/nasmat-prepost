""" Module for launching the screenshot UI""" # pylint: disable=C0103
import os
import sys
import ctypes
import tkinter as tk
from tkinter import filedialog
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (QApplication,QDialog,QMessageBox) # pylint: disable=E0611
from PyQt5.QtCore import Qt # pylint: disable=E0611
from PyQt5 import uic


class ScreenshotDialog(QDialog): # pylint: disable=R0902
    """ dialog window for saving a screenshot of the current window"""
    def __init__(self, parent=None, filename='test.png', wsize=(800,600), dpi=300, width=None):
        """
        Initialize class

        Parameters:
            parent (class): self from parent calling this class
            filename (str): full file name including path and extension
            wsize (tuple): ints denoting the pixel count of current window size
            dpi (int): requested DPI (dots per inch)
            width (float): requested image width (inches)
        
        Returns:
            None.
        """

        super().__init__(parent)
        uic.loadUi("ui/screenshot.ui", self)

        #store inputs
        self.filename = filename
        self.wsize = wsize
        if width:
            self.width = width
        else:
            act_dpi = self._get_screen_dpi()
            self.width = wsize[0]/act_dpi

        #set defaults for outputs
        self.mag = 0
        self.req_dpi = dpi
        self.actual_dpi = 0
        self.last_dpi = dpi
        self.last_width = self.width
        self.units = self.units_comboBox.currentText()

        #update defaults in UI
        if filename:
            self.file_edit.setText(filename)
        self.reqdpi_edit.setText(f"{dpi}")
        self.curwidth_label.setText(f"{self.width}")
        self.outputwidth_edit.blockSignals(True)
        self.outputwidth_edit.setText(f"{self.width}")
        self.outputwidth_edit.blockSignals(False)
        self.origsizedim_label.setText(f"{wsize[0]} x {wsize[1]} pixels")
        self._calc_dpi()

    def keyPressEvent(self, event): # pylint: disable=C0103
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

    def browse_for_file(self):
        """
        Browses to update the file path/name

        Parameters:
            None.
        
        Returns:
            None.
        """

        filename = filedialog.asksaveasfilename(title="Save Image As...",
        defaultextension=".png",
        filetypes=[("PNG file", "*.png")],
        initialdir=os.path.dirname(self.filename),
        initialfile=os.path.basename(self.filename))

        if filename:
            self.filename=filename
            self.file_edit.setText(filename)

    def chk_valid_input(self):
        """
        Checks if an input is valid

        Parameters:
            None.
        
        Returns:
            None.
        """

        is_float = False
        sender = self.sender()
        try:
            f = float(sender.text())
            if f > 0 and np.isfinite(f):
                is_float = True
        except ValueError:
            is_float = False

        if not is_float:
            QMessageBox.critical(None, 'Error', 'Invalid value detected, resetting...')
            if sender.objectName()=='reqdpi_edit':
                sender.setText(f"{int(self.last_dpi)}")
            elif sender.objectName()=='outputwidth_edit':
                sender.setText(f"{self.last_width}")
        else:
            if sender.objectName()=='reqdpi_edit':
                self.last_dpi = int(sender.text())
            elif sender.objectName()=='outputwidth_edit':
                self.last_width = float(sender.text())
            self._calc_dpi()


    def change_units(self):
        """
        Changes the dimension units 

        Parameters:
            None.
        
        Returns:
            None.
        """

        units = self.units_comboBox.currentText()

        if self.units != units:
            conv_factor = 1.0
            if units=='inches':
                conv_factor = 1/2.54 #cm to inches
            elif units=='cm':
                conv_factor = 2.54 #inches to cm

            cur_width = float(self.curwidth_label.text())
            output_width = float(self.outputwidth_edit.text())
            self.curwidth_label.setText(f"{cur_width*conv_factor}")
            self.outputwidth_edit.setText(f"{output_width*conv_factor}")
            self.units=units
            self.unit_label.setText(units)

    def update_width(self):
        """
        Updates the output image width

        Parameters:
            None.
        
        Returns:
            None.
        """

        #Note: width does not appear to be outputting correctly, disabled for now in UI
        self.outputwidth_edit.setEnabled(self.updatewidth_checkBox.isChecked())

    def accept(self):
        """
        Override default accept behavior to save state

        Parameters:
            None.
        
        Returns:
            None.
        """

        self._calc_dpi()

        self.filename=self.file_edit.text()
        p = Path(self.filename)
        if p.parent.is_dir():
            super().accept()
        else:
            QMessageBox.critical(None, 'Error', 'File does not contain a valid path...')

    def _calc_dpi(self):
        """
        Calculates new dpi value

        Parameters:
            None.
        
        Returns:
            None.
        """

        width_pix,height_pix = self.wsize
        actual_width_pix = width_pix*self.mag
        actual_height_pix = height_pix*self.mag

        output_width = float(self.outputwidth_edit.text())
        if self.units == 'cm': #convert cm to inches for DPI calc
            output_width /= 2.54

        req_dpi = int(self.reqdpi_edit.text())
        while self.actual_dpi < req_dpi:
            self.mag += 1
            actual_width_pix = width_pix*self.mag
            actual_height_pix = height_pix*self.mag
            self.actual_dpi = int(np.round(actual_width_pix/output_width))

        self.newsizedim_label.setText(f"{actual_width_pix} x {actual_height_pix} pixels")
        self.actdpival_label.setText(f"{self.actual_dpi}")

    def _get_screen_dpi(self):
        """
        Gets screen dpi 

        Parameters:
            None.
        
        Returns:
            dpi (int): actual dpi of screen
        """

        if sys.platform.startswith("win"):
            user32 = ctypes.windll.user32
            dc = user32.GetDC(0)
            LOGPIXELSX = 88
            dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
            user32.ReleaseDC(0, dc)
            return dpi

        if sys.platform.startswith("linux"):
            try:
                root = tk.Tk()
                dpi = root.winfo_fpixels('1i')
                root.destroy()
                return dpi
            except Exception as e:
                print("Failed to get DPI on Linux:", e)
                print("Using default DPI=96")
                return 96 

        print("Unsupported OS, using default DPI=96")
        return 96

if __name__ == "__main__":
    app = QApplication([])
    w = ScreenshotDialog(filename=os.path.join(os.getcwd(),'test.png'))
    w.show()
    sys.exit(app.exec_())
