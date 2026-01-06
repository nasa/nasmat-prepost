"""class and functions handling text edit UI""" #pylint: disable=C0103
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QDialog # pylint: disable=E0611

class Edit_text_dialog(QDialog): #pylint: disable=C0103
    """Class for the Edit_text_dialog UI."""
    def __init__(self,parent=None,file=None,raw_input=None):
        """
        Initialization routine called for the Edit_text_dialog class.

        Parameters:
            parent (class): self from parent calling this class
            file (str): input file name
            raw_input (list): strings containing raw input 

        Returns:
            None.
        """

        super().__init__(parent)
        loadUi("ui/Edit_text_dialog.ui", self)

        self.orig_text=raw_input

        if file:
            self.label_macname.setText(file)
        if raw_input:
            self.textEdit.setPlainText(''.join(raw_input))

        self.text=[]

    def get_text(self):
        """
        Callback function to get current text.

        Parameters:
            None.

        Returns:
            None.
        """

        self.text=self.textEdit.toPlainText()

    def reset_text(self):
        """
        Callback function to reset text to original input.

        Parameters:
            None.

        Returns:
            None.
        """

        self.textEdit.setPlainText(''.join(self.orig_text))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Edit_text_dialog()
    status=w.exec()
    sys.exit()
