"""utility class for table editing"""# pylint: disable=C0103
from PyQt5.QtCore import Qt,pyqtSignal,pyqtProperty # pylint: disable=E0611
from PyQt5.QtWidgets import QMessageBox,QTableWidgetItem,QTableWidget # pylint: disable=E0611
import pyperclip

class TableWithCopyPaste(QTableWidget):
    """table copy/paste utility class"""

    #adding a custom signal to indicate the table has been updated
    tableupdated = pyqtSignal()

    def __init__(self,parent=None):
        """
        Initialization routine called for the TableWithCopyPaste class.

        Parameters:
            parent (class): self from parent calling this class

        Returns:
            None.
        """

        super().__init__(parent)

        self.rucstr = ''
        self.data = [[]]
        self.n_slice=None
        self.dim=None
        self._rowlim = None

    #adding a custom property to control pasting if number of rows should be limited
    #e.g., prevents pasting in an array of data if only one row is required
    def getrowlim(self):
        """
        Callback function to get maximum number of allowed rows in table.

        Parameters:
            None.

        Returns:
            None.
        """

        return self._pasteopt

    def setrowlim(self, ival):
        """
        Callback function to set maximum number of allowed rows in table.

        Parameters:
            ival (int): maximum number of rows

        Returns:
            None.
        """
        self._rowlim = ival

    RowLimPaste = pyqtProperty(bool, fget=getrowlim, fset=setrowlim)

    def keyPressEvent(self, event):
        """
        Callback function to handle key press events.

        Parameters:
            event (QKeyEvent): data based on key press

        Returns:
            None.
        """

        super().keyPressEvent(event)
        #TODO: add copy support for table
        if (event.key() == Qt.Key_V and
            (event.modifiers() & Qt.KeyboardModifier.ControlModifier)): #pasting - Ctrl+V
            self.rucstr = pyperclip.paste()
            self._process_str()
            self.set_data(islice=0)

    def _process_str(self):
        """
        Function to process strings for updating table.

        Parameters:
            None.

        Returns:
            None.
        """

        if self.dim==3 and not self.n_slice:
            QMessageBox.critical(None, 'Error',
                                'Slice not defined for 3D data input. Set NG variable.')
            return

        rucstr=self.rucstr.replace(' ','')
        #account for possibile mising newline on last roww
        if not rucstr.endswith('\r\n'):
            rucstr=rucstr+'\r\n'

        rows = rucstr.split('\r\n')[:-1]
        newrows=[]
        continue_found=False
        for i,row in enumerate(rows):
            if not row or row.startswith('#'): #skip rows starting with comment
                continue

            # if self._rowlim and i>self._rowlim-1:
            #     break

            if not continue_found: #initializing current new row string
                curnew=''

            newrow=row.split('=')
            if len(newrow)==1:
                newrow=newrow[0]
            elif len(newrow)==2:
                newrow=newrow[1]
            else:
                print('WARNING: inadmisible input pasted into user-defined table')
                print(' ---> ', newrow)
                newrow=newrow[1]

            if newrow.endswith('&'):
                continue_found=True
                newrow=newrow[:-1]
                curnew=curnew+newrow
            else:
                continue_found=False
                curnew=curnew+newrow
                newrows.append(curnew)

        if not self.n_slice:
            self.n_slice=1

        if len(newrows)%self.n_slice !=0:
            QMessageBox.critical(None, 'Error',
                                'NG variable does not evenly divide into input.')
            return

        #convert list of lists (2D) to 3D representation
        sz=len(newrows)//self.n_slice
        self.data = [newrows[i:i+sz] for i in range(0, len(newrows), sz)]
        #print(self.data)

    def update_data(self,islice=0):
        """
        Function to update table.

        Parameters:
            islice (int): slice index for 3D tables

        Returns:
            None.
        """

        values=[]
        for row in range(self.rowCount()):
            row_values = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item is not None:
                    row_values.append(item.text())
                else:
                    row_values.append("")
            values.append(','.join(row_values))

        self.data[islice]=values

    def set_data(self,data=None,islice=0):
        """
        Function to set table data.

        Parameters:
            data (list of lists): strings containing new table data
            islice (int): slice index for 3D tables

        Returns:
            None.
        """

        if data:
            self.data=data

        try:
            rows=self.data[islice]
        except IndexError:
            return

        if len(rows) == 0:
            return

        #blockSignals required to correctly update table
        self.blockSignals(True)
        self.clearContents()
        self.setRowCount(len(rows))
        self.setColumnCount(len(rows[0].split(',')))
        # print("RowCount =", self.rowCount(), "ColumnCount =", self.columnCount())

        #prefill with empty items to avoid "silent" error when set below
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                if self.item(i, j) is None:
                    self.setItem(i, j, QTableWidgetItem(''))
                    # check_item = self.item(i, j)
                    # if check_item is None:
                    #     print("Dummy insert failed at ", i, j)

        for i, row in enumerate(rows):
            row = row.split(',')
            for j, value in enumerate(row):
                item = self.item(i,j)
                if item is not None:
                    item.setText(value)
                else:
                    self.setItem(i, j, QTableWidgetItem(value))

                # check_item = self.item(i, j)
                # if check_item is None:
                #     print("Insert failed at ", i, j)
                #     print('row: ',row)
                #     print('value: ',value)

        self.blockSignals(False)
        self.tableupdated.emit()


    def get_data(self,fmt='float'):
        """
        Function to get table data.

        Parameters:
            fmt (str): format for output table data

        Returns:
            data (list of lists): strings containing table data
        """

        data=[]
        for row in range(self.rowCount()):
            cd=[]
            for col in range(self.columnCount()):
                item=self.item(row,col)
                if item and item.text():
                    txt=item.text()
                    if fmt=='float':
                        cd.append(float(txt))
                    elif fmt=='int':
                        cd.append(int(txt))
                else:
                    cd.append('')
            data.append(cd)
        return data

    def convert_data(self,fmt='float'):
        """
        Function to convert table data.

        Parameters:
            fmt (str): format for output table data

        Returns:
            newdata (list of lists): strings containing table data
        """

        newdata=None
        try:
            if fmt=='float':
                newdata = [[[float(num) for num in item.split(',')]
                            for item in sublist] for sublist in self.data]
            elif fmt=='int':
                newdata = [[[int(num) for num in item.split(',')]
                            for item in sublist] for sublist in self.data]
            return newdata
        except ValueError:
            return newdata

    def set_dim(self,dim):
        """
        Function to set dim parameter

        Parameters:
            dim (int): dim parameter

        Returns:
            None.
        """

        self.dim=dim

    def set_n_slice(self,n_slice):
        """
        Function to set n_slice parameter

        Parameters:
            n_slice (int): format for output table data

        Returns:
            None.
        """

        self.n_slice=n_slice
