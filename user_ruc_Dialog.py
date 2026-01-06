"""Module for launching the user_ruc_Dialog UI."""# pylint: disable=C0103
import sys
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog,QMessageBox,QApplication # pylint: disable=E0611
from PyQt5.QtCore import Qt # pylint: disable=E0611
import numpy as np
from util.TableWithCopyPaste import TableWithCopyPaste #pylint: disable=W0611

class UserRUCDialog(QDialog): # pylint: disable=R0904
    """Class for the user_ruc_Dialog UI."""
    def __init__(self,parent=None,mod='',dim=2,mats=None,ruc=None): # pylint: disable=R0913,R0917
        """
        Initialization routine called for the UserRUCDialog class.

        Parameters:
            parent (class): self from parent calling this class
            mod (str): NASMAT *RUC MOD label
            dim (int): unit cell dimension (2, 3)
            mats (list): list of NASMAT *CONSTITUENT material ids as str
            ruc (dict): ruc input as dict

        Returns:
            None.
        """
        super().__init__(parent)
        loadUi("ui/user_ruc_dialog.ui", self)

        self.mod_label.setText(mod)
        self.dim=dim
        self.mats=mats
        self.avail_mats.setPlainText(','.join(mats))
        self.SM_table.set_dim(dim)

        if self.dim==3:
            self.na_edit.setEnabled(True)
            self.g_scrollbar.setEnabled(True)
            self.D_table.setEnabled(True)
        else:
            self.gscroll_label.setText('')

        self.dim_set=[False,False,False]
        if self.dim!=3:
            self.dim_set[0]=True

        if ruc:
            self.ruc=ruc
            self._set_ruc_from_input()
        else:
            self.ruc={}

        self.D_table.setrowlim(1)
        self.D_table.horizontalHeader().setVisible(False)
        self.D_table.verticalHeader().setVisible(False)
        self.D_table.setRowCount(1)
        self.H_table.setrowlim(1)
        self.H_table.horizontalHeader().setVisible(False)
        self.H_table.verticalHeader().setVisible(False)
        self.H_table.setRowCount(1)
        self.L_table.setrowlim(1)
        self.L_table.horizontalHeader().setVisible(False)
        self.L_table.verticalHeader().setVisible(False)
        self.L_table.setRowCount(1)
        self.D_table.tableupdated.connect(self.chk_N_vals)
        self.H_table.tableupdated.connect(self.chk_N_vals)
        self.L_table.tableupdated.connect(self.chk_N_vals)
        self.SM_table.tableupdated.connect(self.chk_N_vals)

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

    def _set_ruc_from_input(self):
        """
        Function to set UI values from given ruc input.

        Parameters:
            None.

        Returns:
            None.
        """

        if self.dim==3:
            self.na_edit.setText(str(self.ruc['na']))
            newdata = [[','.join([str(self.ruc['d'][i]) for i in range(self.ruc['na'])])]]
            self.D_table.set_data(data=newdata)

        self.nb_edit.setText(str(self.ruc['nb']))
        newdata = [[','.join([str(self.ruc['h'][i]) for i in range(self.ruc['nb'])])]]
        self.H_table.set_data(data=newdata)

        self.ng_edit.setText(str(self.ruc['ng']))
        newdata = [[','.join([str(self.ruc['l'][i]) for i in range(self.ruc['ng'])])]]
        self.L_table.set_data(data=newdata)

        if self.dim==2:
            SM=np.flip(self.ruc['sm'], axis=0)
            newdata = [[','.join([str(SM[i,j]) for j in range(self.ruc['ng'])])
                        for i in range(self.ruc['nb'])]]
        elif self.dim==3:
            SM=np.flip(self.ruc['sm'], axis=2)
            newdata = [[','.join([str(SM[k,j,i]) for j in range(self.ruc['nb'])])
                        for i in range(self.ruc['na'])] for k in range(self.ruc['ng'])]

        self.SM_table.set_data(data=newdata)
        self._set_SM_rowcol_names()

        if self.dim==3:
            self.clearD_pb.setEnabled(True)
            self.refineD_pb.setEnabled(True)
            self.scaleD_pb.setEnabled(True)

        self.clearH_pb.setEnabled(True)
        self.refineH_pb.setEnabled(True)
        self.scaleH_pb.setEnabled(True)
        self.clearL_pb.setEnabled(True)
        self.refineL_pb.setEnabled(True)
        self.scaleL_pb.setEnabled(True)

    def set_NA(self):
        """
        Callback function to set UI NA value.

        Parameters:
            None.

        Returns:
            None.
        """

        na = self.na_edit.text()
        if na.isdigit():
            self.dim_set[0]=True
            self.ruc['na']=int(na)
            self.D_table.setColumnCount(int(na))
            self.setD_pb.setEnabled(True)
            self.SM_table.setRowCount(int(na))
            self.set_SM()
        else:
            self.na_edit.setText('')
            self.dim_set[0]=False

    def set_NB(self):
        """
        Callback function to set UI NB value.

        Parameters:
            None.

        Returns:
            None.
        """

        nb = self.nb_edit.text()
        if nb.isdigit():
            self.dim_set[1]=True
            self.ruc['nb']=int(nb)
            self.H_table.setColumnCount(int(nb))
            self.setH_pb.setEnabled(True)
            if self.dim==2:
                self.SM_table.setRowCount(int(nb))
            else:
                self.SM_table.setColumnCount(int(nb))
            self.set_SM()
        else:
            self.nb_edit.setText('')
            self.dim_set[1]=False

    def set_NG(self):
        """
        Callback function to set UI NG value.

        Parameters:
            None.

        Returns:
            None.
        """

        ng = self.ng_edit.text()
        if ng.isdigit():
            self.dim_set[2]=True
            self.ruc['ng']=int(ng)
            self.L_table.setColumnCount(int(ng))
            self.setL_pb.setEnabled(True)
            if self.dim==3:
                self.SM_table.set_n_slice(int(ng))
                self.g_scrollbar.setMaximum(int(ng))
            else:
                self.SM_table.setColumnCount(int(ng))
            self.set_SM()
        else:
            self.ng_edit.setText('')
            self.dim_set[2]=False

    def set_SM(self):
        """
        Callback function to set UI SM values.

        Parameters:
            None.

        Returns:
            None.
        """

        if all(self.dim_set):
            self.setSM_pb.setEnabled(True)
            self._set_SM_rowcol_names()
        else:
            self.setSM_pb.setEnabled(False)
            if self.dim==3:
                self.g_scrollbar.setMaximum(self.ruc['ng'])
                self.g_scrollbar.setMinimum(1)
                self.g_scrollbar.setValue(1)
                self.gscroll_label.setText('GAMMA = 1')


    def _get_constval(self,fmt='float'):
        """
        Function to get constant from UI QLineEdit item.

        Parameters:
            fmt (str): variable format

        Returns:
            None.
        """

        val=self.val_edit.text()
        if fmt=='int' and val.isdigit():
            return int(val)
        elif fmt=='float':
            try:
                return float(val)
            except ValueError:
                self.val_edit.setText('')
                return None

    def _chk_table_empty(self,table):
        """
        Function to check if given table is empty.

        Parameters:
            table (TableWithCopyPaste): input table to check

        Returns:
            None.
        """

        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item=table.item(row,col)
                if item and item.text():
                    return False
        return True

    def chk_D_table(self):
        """
        Callback function to set UI D table.

        Parameters:
            None.

        Returns:
            None.
        """

        empty = self._chk_table_empty(self.D_table)
        if not empty:
            self.clearD_pb.setEnabled(True)
            self.refineD_pb.setEnabled(True)
            self.scaleD_pb.setEnabled(True)
        else:
            self.clearD_pb.setEnabled(False)
            self.refineD_pb.setEnabled(False)
            self.scaleD_pb.setEnabled(False)

        self.D_table.update_data()

    def chk_H_table(self):
        """
        Callback function to set UI H table.

        Parameters:
            None.

        Returns:
            None.
        """

        empty = self._chk_table_empty(self.H_table)
        if not empty:
            self.clearH_pb.setEnabled(True)
            self.refineH_pb.setEnabled(True)
            self.scaleH_pb.setEnabled(True)
        else:
            self.clearH_pb.setEnabled(False)
            self.refineH_pb.setEnabled(False)
            self.scaleH_pb.setEnabled(False)

        self.H_table.update_data()

    def chk_L_table(self):
        """
        Callback function to set UI L table.

        Parameters:
            None.

        Returns:
            None.
        """

        empty = self._chk_table_empty(self.L_table)
        if not empty:
            self.clearL_pb.setEnabled(True)
            self.refineL_pb.setEnabled(True)
            self.scaleL_pb.setEnabled(True)
        else:
            self.clearL_pb.setEnabled(False)
            self.refineL_pb.setEnabled(False)
            self.scaleL_pb.setEnabled(False)

        self.L_table.update_data()

    def chk_SM_table(self):
        """
        Callback function to set UI SM table.

        Parameters:
            None.

        Returns:
            None.
        """

        empty = self._chk_table_empty(self.SM_table)
        if not empty:
            self.clearSM_pb.setEnabled(True)

            na = self.nb_edit.text()
            nb = self.nb_edit.text()
            ng = self.ng_edit.text()
            if self.dim==3 and (not na or not nb):
                self.na_edit.setText(str(self.SM_table.rowCount()))
                self.set_NA()
                self.nb_edit.setText(str(self.SM_table.columnCount()))
                self.set_NB()

            elif self.dim==2 and (not nb or not ng):
                self.nb_edit.setText(str(self.SM_table.rowCount()))
                self.set_NB()
                self.ng_edit.setText(str(self.SM_table.columnCount()))
                self.set_NG()
                self.SM_table.update_data()


            if self.dim==3:
                self.SM_table.update_data(slice=self.g_scrollbar.value()-1)
            elif self.dim==2:
                self.SM_table.update_data()
        else:
            self.clearSM_pb.setEnabled(False)

        self._set_SM_rowcol_names()

    def chk_N_vals(self):
        """
        Callback function to check if NA,NB,NG are correctly set after copy/paste

        Parameters:
            None. 

        Returns:
            None.
        """
        sender = self.sender()
        tablename = sender.objectName()
        if tablename not in ('SM_table','D_table','H_table','L_table'):
            # print(f"warning: sending table not found in UI: {tablename}")
            return

        nrows,ncols = sender.rowCount(),sender.columnCount()
        if tablename=='SM_table':
            if self.dim==2:
                self.nb_edit.setText(str(nrows))
                self.set_NB()
                self.ng_edit.setText(str(ncols))
                self.set_NG()
            else:
                self.na_edit.setText(str(nrows))
                self.set_NA()
                self.nb_edit.setText(str(ncols))
                self.set_NB()
                self.ng_edit.setText(str(self.ruc['ng']))
                self.set_NG()

        elif tablename=='D_table':
            self.na_edit.setText(str(ncols))
            self.set_NA()
        elif tablename=='H_table':
            self.nb_edit.setText(str(ncols))
            self.set_NB()
        elif tablename=='L_table':
            self.ng_edit.setText(str(ncols))
            self.set_NG()

        self._set_SM_rowcol_names()


    def setD_const(self):
        """
        Callback function to set UI D values to a constant.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_constval()
        if val:
            newdata = [[','.join([str(val) for _ in range(self.ruc['na'])])]]
            self.D_table.set_data(data=newdata)

    def setH_const(self):
        """
        Callback function to set UI H values to a constant.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_constval()
        if val:
            newdata = [[','.join([str(val) for _ in range(self.ruc['nb'])])]]
            self.H_table.set_data(data=newdata)

    def setL_const(self):
        """
        Callback function to set UI L values to a constant.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_constval()
        if val:
            newdata = [[','.join([str(val) for _ in range(self.ruc['ng'])])]]
            self.L_table.set_data(data=newdata)

    def setSM_const(self):
        """
        Callback function to set UI SM values to a constant.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_constval(fmt='int')
        if val:
            newdata=[]
            if self.dim==2:
                newdata = [[','.join([str(val) for _ in range(self.ruc['ng'])])
                            for _ in range(self.ruc['nb'])]]
            elif self.dim==3:
                newdata = [[','.join([str(val) for _ in range(self.ruc['nb'])])
                            for _ in range(self.ruc['na'])] for _ in range(self.ruc['ng'])]
            self.SM_table.set_data(data=newdata)
            self._set_SM_rowcol_names()

    def move_gamma_scrollbar(self):
        """
        Callback function to move UI gamma scrollbar.

        Parameters:
            None.

        Returns:
            None.
        """

        ind=self.g_scrollbar.value()
        self.gscroll_label.setText(f"GAMMA={ind}")
        self.SM_table.set_data(islice=ind-1)
        self._set_SM_rowcol_names()

    def _set_SM_rowcol_names(self):
        """
        Function to set row and column names for UI SM table.

        Parameters:
            None.

        Returns:
            None.
        """

        nrows,ncols = self.SM_table.rowCount(),self.SM_table.columnCount()
        row_names=[]
        col_names=[]
        if self.dim==3:
            row_names.extend([f"a={i}" for i in range(nrows, 0, -1)])
            self.SM_table.setVerticalHeaderLabels(row_names)
            col_names.extend([f"b={i+1}" for i in range(ncols)])
            self.SM_table.setHorizontalHeaderLabels(col_names)
        else:
            row_names.extend([f"b={i}" for i in range(nrows, 0, -1)])
            self.SM_table.setVerticalHeaderLabels(row_names)
            col_names.extend([f"g={i+1}" for i in range(ncols)])
            self.SM_table.setHorizontalHeaderLabels(col_names)

    def _get_refineval(self):
        """
        Function to get refine value from UI QLineEdit item

        Parameters:
            None.

        Returns:
            None.
        """

        val=self.refine_edit.text()
        if val.isdigit():
            return int(val)
        else:
            self.refine_edit.setText('')

    def setD_refine(self):
        """
        Callback function to refine grid for UI D values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_refineval()
        if val:
            data=self.D_table.get_data(fmt='float')
            newdata = [[','.join(str(item/val) for item in
                                 row for _ in range(val)) for row in data]]
            self.D_table.set_data(data=newdata)

            data=self.SM_table.convert_data(fmt='int') #grab data before na set
            self.na_edit.setText(str(self.D_table.columnCount()))
            if data:
                data=np.repeat(np.asarray(data), repeats=val, axis=1).tolist()
                newdata=[[','.join(map(str, row)) for row in slice] for slice in data]
                self.SM_table.set_data(data=newdata)
                self._set_SM_rowcol_names()

    def setH_refine(self):
        """
        Callback function to refine grid for UI H values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_refineval()
        if val:
            data=self.H_table.get_data(fmt='float')
            newdata = [[','.join(str(item/val) for item in
                                 row for _ in range(val)) for row in data]]
            self.H_table.set_data(data=newdata)

            data=self.SM_table.convert_data(fmt='int') #grab data before nb set
            self.nb_edit.setText(str(self.H_table.columnCount()))
            if data:
                data=np.repeat(np.asarray(data), val, axis=2).tolist()
                newdata=[[','.join(map(str, row)) for row in slice] for slice in data]
                self.SM_table.set_data(data=newdata)
                self._set_SM_rowcol_names()

    def setL_refine(self):
        """
        Callback function to refine grid for UI L values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_refineval()
        if val:
            data=self.L_table.get_data(fmt='float')
            newdata = [[','.join(str(item/val) for item in
                                 row for _ in range(val)) for row in data]]
            self.L_table.set_data(data=newdata)

            data=self.SM_table.convert_data(fmt='int') #grab data before nb set
            self.ng_edit.setText(str(self.L_table.columnCount()))
            if data:
                data=np.repeat(np.asarray(data), val, axis=0).tolist()
                newdata=[[','.join(map(str, row)) for row in slice] for slice in data]
                self.SM_table.set_data(data=newdata)
                self._set_SM_rowcol_names()

    def _get_scaleval(self):
        """
        Function to get scale value from UI QLineEdit item

        Parameters:
            None.

        Returns:
            None.
        """

        val=self.scale_edit.text()
        try:
            return float(val)
        except ValueError:
            self.scale_edit.setText('')
            return None

    def setD_scale(self):
        """
        Callback function to scale UI D values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_scaleval()
        if val:
            data=self.D_table.get_data(fmt='float')
            newdata = [[','.join(str(item*val) for item in row) for row in data]]
            self.D_table.set_data(data=newdata)

    def setH_scale(self):
        """
        Callback function to scale UI H values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_scaleval()
        if val:
            data=self.L_table.get_data(fmt='float')
            newdata = [[','.join(str(item*val) for item in row) for row in data]]
            self.L_table.set_data(data=newdata)

    def setL_scale(self):
        """
        Callback function to scale UI L values.

        Parameters:
            None.

        Returns:
            None.
        """

        val=self._get_scaleval()
        if val:
            data=self.L_table.get_data(fmt='float')
            newdata = [[','.join(str(item*val) for item in row) for row in data]]
            self.L_table.set_data(data=newdata)

    def clearD(self):
        """
        Callback function to clear UI D table.

        Parameters:
            None.

        Returns:
            None.
        """

        self.D_table.clear()

    def clearH(self):
        """
        Callback function to clear UI H table.

        Parameters:
            None.

        Returns:
            None.
        """

        self.H_table.clear()

    def clearL(self):
        """
        Callback function to clear UI L table.

        Parameters:
            None.

        Returns:
            None.
        """

        self.L_table.clear()

    def clearSM(self):
        """
        Callback function to clear UI SM table.

        Parameters:
            None.

        Returns:
            None.
        """

        for row in range(self.SM_table.rowCount()):
            for col in range(self.SM_table.columnCount()):
                item=self.SM_table.item(row,col)
                if item:
                    self.SM_table.takeItem(row,col)

    def _chk_valid(self):
        """
        Function to verify UI table data.

        Parameters:
            None.

        Returns:
            None.
        """

        err_found=False
        D=self.D_table.convert_data(fmt='float')
        if (D is None or not D) and self.dim==3:
            err_found=True
            QMessageBox.critical(None, 'Error', 'D input is not valid.')
        H=self.H_table.convert_data(fmt='float')
        if H is None or not H:
            err_found=True
            QMessageBox.critical(None, 'Error', 'H input is not valid.')
        L=self.L_table.convert_data(fmt='float')
        if L is None or not L:
            err_found=True
            QMessageBox.critical(None, 'Error', 'L input is not valid.')
        SM=self.SM_table.convert_data(fmt='int')
        if SM is None or not SM:
            err_found=True
            QMessageBox.critical(None, 'Error', 'SM input is not valid.')
        SMu=set(np.unique(SM).astype(str).tolist())
        if not SMu.issubset(set(self.mats)):
            print('Available materials: ', set(self.mats))
            print('Input materials: ', SMu)
            QMessageBox.warning(None, 'Warning', 'One of more materials in SM are not defined.')

        SM = np.asarray(SM)
        shp = SM.shape
        if self.dim==2: #input SM: 1,NB(reversed),NG; output SM: NB,NG
            if shp[1] != self.ruc['nb']:
                err_found=True
                QMessageBox.critical(None, 'Error', 'NB input does not match SM shape.')
            if shp[2] != self.ruc['ng']:
                err_found=True
                QMessageBox.critical(None, 'Error', 'NG input does not match SM shape.')
        elif self.dim==3: #input SM: NG,NA(reversed),NB; output SM: NG,NB,NA
            if shp[1] != self.ruc['na']:
                err_found=True
                QMessageBox.critical(None, 'Error', 'NA input does not match SM shape.')

            if shp[2] != self.ruc['nb']:
                err_found=True
                QMessageBox.critical(None, 'Error', 'NB input does not match SM shape.')

            if shp[0] != self.ruc['ng']:
                err_found=True
                QMessageBox.critical(None, 'Error', 'NG input does not match SM shape.')


        return err_found

    def accept_close(self):
        """
        Callback function to accept inputs and close UI.

        Parameters:
            None.

        Returns:
            None.
        """

        err_found=self._chk_valid()
        if not err_found:
            self.ruc['DIM']=f"{self.dim}D"
            if self.dim==3:
                self.ruc['d']=np.asarray(self.D_table.convert_data(fmt='float')).flatten()
            self.ruc['h']=np.asarray(self.H_table.convert_data(fmt='float')).flatten()
            self.ruc['l']=np.asarray(self.L_table.convert_data(fmt='float')).flatten()
            SM=np.asarray(self.SM_table.convert_data(fmt='int'))
            #SM needs to be re-ordered to match rest of code
            if self.dim==2: #input SM: NB(reversed),NG,1; output SM: NB,NG
                SM=np.flip(SM, axis=1)
                self.ruc['sm']=SM[0,:,:]
                self.ruc['na']=1
            elif self.dim==3: #input SM: NA(reversed),NB,NG; output SM: NG,NB,NA
                SM=np.flip(SM, axis=1)
                self.ruc['sm']=np.swapaxes(SM,1,2)

            self.accept()

#-----------------------------------------------------------------------------
if __name__ == "__main__":

    app = QApplication([])
    test_ruc_2d=False

    if test_ruc_2d: #testing 2d unit cell
        iruc={}
        iruc['nb']=4
        iruc['ng']=2
        iruc['h']=np.asarray([1.0,1.0,1.0,1.0])
        iruc['l']=np.asarray([2.0,2.0])
        iruc['sm']=np.asarray([[1,2],[2,2],[2,1],[2,1]])
        widget = UserRUCDialog(dim=2,mats=['1','2'],ruc=iruc)

    else: #testing 3d unit cell
        iruc={}
        iruc['na']=2
        iruc['nb']=4
        iruc['ng']=3
        iruc['d']=np.asarray([1.0,1.0])
        iruc['h']=np.asarray([1.0,1.0,1.0,1.0])
        iruc['l']=np.asarray([1.0,1.0,1.0])
        iruc['sm']=np.asarray([ #comments reflect nasmat input deck format
                                #gamma = 1
                                [[1, 1], #1,2,1,2
                                 [1, 2], #1,1,2,2
                                 [2, 1],
                                 [2, 2]],
                                #gamma = 2
                                [[2, 1],#1,2,1,1
                                 [2, 2],#2,2,1,2
                                 [1, 1],
                                 [2, 1]],
                                #gamma = 3
                                [[1, 1],#1,2,2,2
                                 [2, 2],#1,2,2,1
                                 [2, 2],
                                 [1, 2]], ])

        widget = UserRUCDialog(dim=3,mats=['1','2'],ruc=iruc)

    widget.show()
    sys.exit(app.exec_())
