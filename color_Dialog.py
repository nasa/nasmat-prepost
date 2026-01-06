"""class and functions handling the color dialog UI""" #pylint: disable=C0103
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QDialog # pylint: disable=E0611
from PyQt5.QtCore import Qt # pylint: disable=E0611
from vtkmodules.vtkCommonColor import vtkColorSeries # pylint: disable=E0611

class color_Dialog(QDialog): #pylint: disable=C0103
    """Class for the color_Dialog UI."""
    def __init__(self,parent=None,colors=None):
        """
        Initialization routine called for the woven2d_Dialog class.

        Parameters:
            parent (class): self from parent calling this class
            colors (dict): colormap settings 

        Returns:
            None.
        """

        super().__init__(parent)
        loadUi("ui/color_dialog.ui", self)

        self.colors=colors.copy()
        self._get_colormap_presets()
        self.colors_comboBox.setCurrentIndex(colors['colormap'])

        txt=','.join(map(str,colors['background']))
        self.background_color_txt.setText(txt)
        self.colors_comboBox.setCurrentIndex(colors['colormap'])

        self.update_colormap()
        self.update_background_color()

    def keyPressEvent(self, event):
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

    def _get_colormap_presets(self):
        """
        Function to get preset colormaps

        Parameters:
            None.

        Returns:
            None.
        """

        color_series = vtkColorSeries()
        self.colors_comboBox.addItem('Default')
        num_series = color_series.GetNumberOfColorSchemes()
        for i in range(num_series):
            color_series.SetColorScheme(i)
            self.colors_comboBox.addItem(color_series.GetColorSchemeName())


    def update_background_color(self):
        """
        Callback function to update background color

        Parameters:
            None

        Returns:
            None.
        """

        txt = self.background_color_txt.text().replace(' ', '')

        txt_rgb = txt.split(',')
        is_empty = any(i=='' for i in txt_rgb)
        if ((len(txt_rgb) != 3) or is_empty):
            #print('Define background color using a comma-separated list with three values [0-1].')
            self.colors['background'] = [0.8, 0.88, 0.92] #reset to default
        else:
            self.colors['background'] = [float(c) for c in txt_rgb]


    def update_colormap(self):
        """
        Callback function to update colormap

        Parameters:
            None

        Returns:
            None.
        """

        self.colors['colormap']=self.colors_comboBox.currentIndex()

#-----------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = color_Dialog(colors={'background':[0.8, 0.88, 0.92],'colormap':0})
    status=w.exec()
    print(w.colors)
    sys.exit()
