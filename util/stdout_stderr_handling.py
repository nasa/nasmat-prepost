"""Support functions to handle stdout/stderr"""
import sys
import traceback
from PyQt5.QtCore import QObject,pyqtSignal # pylint: disable=E0611
from PyQt5.QtGui import QColor # pylint: disable=E0611

def qt_excepthook(exc_type, exc_value, exc_tb):
    """ Helper function to redefine except behavior"""
    sys.__stderr__.write(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )
    sys.stderr.write(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )

class EmittingStream(QObject):
    """ Helper class to redirect stdout/stderr output to UI."""
    textWritten = pyqtSignal(str,QColor)
    encoding = "utf-8"
    errors = "replace"

    def __init__(self,parent=None, color=QColor("black")):
        """
        Initialization function for class

        Parameters:
            parent (class): self from parent calling this class
            color (QColor): text color

        Returns:
            None.
        """

        super().__init__(parent)
        self.color=color

    def write(self, text):
        """
        Write function for appending data

        Parameters:
            text (str): text to be written to UI

        Returns:
            None.
        """

        if not text:
            return

        if not isinstance(text, str):
            text = str(text)

        self.textWritten.emit(text,self.color)

    def flush(self):
        """
        Flush function (required for Python)

        Parameters:
            None.

        Returns:
            None.
        """

    def isatty(self):
        """
        Function to check if stream is connected to a terminal

        Parameters:
            None.

        Returns:
            None.
        """

        return False

    def fileno(self):
        """
        Function to return file number

        Parameters:
            None.

        Returns:
            None.
        """

        return -1
