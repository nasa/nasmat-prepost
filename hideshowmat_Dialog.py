"""Module for launching the HideShowMatDialog UI.""" # pylint: disable=C0103
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication # pylint: disable=E0611
from PyQt5.QtWidgets import QDialog # pylint: disable=E0611

class HideShowMatDialog(QDialog):
    """Class for the HideShowMatDialog UI."""
    def __init__(self,parent=None,mac_inp=None):
        """
        Initialization routine called for the HideShowMatDialog class.

        Parameters:
            parent (class): self from parent calling this class
            mac_inp (dict): mac inputs to be pre-populate values in UI

        Returns:
            None.
        """

        super().__init__(parent)
        self.mac_inp=mac_inp
        loadUi("ui/hideshowmat_dialog.ui", self)
        self._set_buttons()

    def show_all(self):
        """
        Callback function to show all materials.

        Parameters:
            None.

        Returns:
            None.
        """

        items=self._get_all_items()
        self.showlistWidget.clear()
        self.hidelistWidget.clear()
        self.showlistWidget.insertItems(0,items)
        self.showlistWidget.sortItems()
        self._set_buttons()

    def hide_all(self):
        """
        Callback function to hide all materials.

        Parameters:
            None.

        Returns:
            None.
        """

        items=self._get_all_items()
        self.hidelistWidget.clear()
        self.showlistWidget.clear()
        self.hidelistWidget.insertItems(0,items)
        self.hidelistWidget.sortItems()
        self._set_buttons()

    def show_selected(self):
        """
        Callback function to show selected materials.

        Parameters:
            None.

        Returns:
            None.
        """

        wh=self.hidelistWidget
        ws=self.showlistWidget
        si=wh.selectedItems()
        selected=[item.text() for item in si]
        old=self._get_show_items()
        new=list(set(old+selected))
        ws.clear()
        ws.insertItems(0,new)
        ws.sortItems()
        for item in si:
            wh.takeItem(wh.row(item))
        wh.sortItems()
        self._set_buttons()

    def hide_selected(self):
        """
        Callback function to hide selected materials.

        Parameters:
            None.

        Returns:
            None.
        """
        wh=self.hidelistWidget
        ws=self.showlistWidget
        si=ws.selectedItems()
        selected=[item.text() for item in si]
        old=self.get_hide_items()
        new=list(set(old+selected))
        wh.clear()
        wh.insertItems(0,new)
        wh.sortItems()
        for item in si:
            ws.takeItem(ws.row(item))
        ws.sortItems()
        self._set_buttons()

    def _get_all_items(self):
        """
        Function to get both show and hide items.

        Parameters:
            None.

        Returns:
            None.
        """

        items1=self._get_show_items()
        items2=self.get_hide_items()
        return list(set(items1+items2))

    def get_hide_items(self):
        """
        Function to get hide items.

        Parameters:
            None.

        Returns:
            None.
        """

        wh=self.hidelistWidget
        items=[]
        for i in range(wh.count()):
            items.append(wh.item(i).text())
        return items

    def _get_show_items(self):
        """
        Function to get show items.

        Parameters:
            None.

        Returns:
            None.
        """

        ws=self.showlistWidget
        items=[]
        for i in range(ws.count()):
            items.append(ws.item(i).text())
        return items

    def _set_buttons(self):
        """
        Function to set buttons in UI.

        Parameters:
            None.

        Returns:
            None.
        """

        if self.hidelistWidget.count()>0 and self.showlistWidget.count()!=0:
            self.hideall_pb.setEnabled(True)
            self.hide_pb.setEnabled(True)
        elif self.hidelistWidget.count()>0 and self.showlistWidget.count()==0:
            self.hideall_pb.setEnabled(False)
            self.hide_pb.setEnabled(False)
        else:
            self.hideall_pb.setEnabled(True)
            self.hide_pb.setEnabled(True)

        if self.showlistWidget.count()>0 and self.hidelistWidget.count()!=0:
            self.showall_pb.setEnabled(True)
            self.show_pb.setEnabled(True)
        elif self.showlistWidget.count()>0 and self.hidelistWidget.count()==0:
            self.showall_pb.setEnabled(False)
            self.show_pb.setEnabled(False)
        else:
            self.showall_pb.setEnabled(True)
            self.show_pb.setEnabled(True)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    w = HideShowMatDialog()
    w.show()
    sys.exit(app.exec_())
