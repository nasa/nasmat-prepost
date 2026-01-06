"""class and functions to support creating new MAC inputs""" #pylint: disable=C0302,C0103
import sys
import numpy as np
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import (QApplication,QDialog,QListWidgetItem, # pylint: disable=E0611
                            QTreeWidgetItem,QComboBox,QAbstractScrollArea,
                            QTableWidgetItem,QTableWidget,QMessageBox)
from PyQt5.QtCore import Qt # pylint: disable=E0611
from woven2d_Dialog import woven2d_Dialog
from user_ruc_Dialog import UserRUCDialog
from mac_inp.Read_RUC import get_builtin_ruc_2d,get_builtin_ruc_3d

class new_Dialog(QDialog): #pylint: disable=C0103,R0902,R0904
    """Class for the new_Dialog UI."""
    def __init__(self,parent=None,defaults=False,mac_inp=None): #pylint: disable=R0915
        """
        Initialization routine called for the new_Dialog class.

        Parameters:
            parent (class): self from parent calling this class
            defaults (bool): flag to use default values in UI
            mac_inp (dict): existing data to populate UI

        Returns:
            None.
        """

        super().__init__(parent)
        loadUi("ui/new_dialog.ui", self)

        self.defaults=defaults
        self.constits={}
        self.avail_rucs={}
        self.rucstr = {}
        self.dim = None
        self.current_ruc = None
        self.rucs_used_tree={}

        self.failsub_opts=['1 - Max Stress','2 - Max Strain','6 - Hashin-Rotem (stress)',\
                            '7 - Hashin-Rotem (strain)', '8 - 2D Max. Princ. Stress',\
                            '9 - 2D Max. Princ. Strain']

        self.ruc_tree.setColumnHidden(2,True)
        if mac_inp:
            self.mac=mac_inp
            self.load_mac()
        else:
            self.mac={}
            #set defaults
            self.kw_tab.setCurrentIndex(0)
            self.cmod14_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.cmod14_table.setColumnHidden(0, True) #temp
            [self.cmod14_table.setColumnHidden(i, True) for i in range(13,19)] #K #pylint: disable=W0106
            self.cmod14_table.resizeColumnsToContents()
            self.cmod69_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.cmod69_table.setColumnHidden(0, True) #temp
            [self.cmod69_table.setColumnHidden(i, True) for i in range(8,17)] #D,K #pylint: disable=W0106
            self.cmod69_table.resizeColumnsToContents()
            self.constit_tables.setCurrentIndex(0)

            self.indiv_unit_cell.setVisible(False)
            self.mod_cb.setCurrentIndex(2)
            self.vf_text.setText('0.0')
            self.r_text.setText('1.0')
            self.ruc_rot_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.ruc_rot_table.resizeColumnsToContents()

            self.fs_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.fs_table.resizeColumnsToContents()
            self.fs_table.setColumnHidden(0, True) #temp
            self.fs_table.setColumnHidden(10, True) #XC11
            self.fs_table.setColumnHidden(11, True) #XC22
            self.fs_table.setColumnHidden(12, True) #XC33

            self.macro_table.removeRow(0)
            self.micro_table.removeRow(0)

            self.mech_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.mech_table.resizeColumnsToContents()
            self.therm_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.therm_table.resizeColumnsToContents()
            self.sol_table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            self.sol_table.resizeColumnsToContents()

            if defaults:
                self._set_default_constit_mats()
                self._set_default_ruc()
                self._set_default_failsub()
                self._set_default_output()
                self._set_default_soln()

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
#-----------------------------------------------------------------------------
#------------------------------- *CONSTITUENTS -------------------------------
    def _set_default_constit_mats(self):
        """
        Function to set default constituents

        Parameters:
            None.

        Returns:
            None.
        """

        mats=[str(i+1) for i in range(3)]
        #IM7
        self.m_text.setText('1')
        self.name_text.setText('IM7')
        self.cmod_cb.setCurrentIndex(0) #CMOD=6
        self.tempdep_cb.setChecked(False)
        p=[None,'262.2E3','11.8E3','0.17','0.21','18.9E3','-0.9E-6','9.0E-6',
            None,None,None,None,None,None,None,None,None]
        [self.cmod69_table.setItem(0,i,QTableWidgetItem(p[i])) for i in range(len(p))] #pylint: disable=W0106
        self.constit_savemat()
        #Glass
        self.m_text.setText('2')
        self.name_text.setText('Glass')
        self.cmod_cb.setCurrentIndex(0) #CMOD=6
        self.tempdep_cb.setChecked(False)
        p=[None,'73.0E3','73.0E3','0.22','0.22','29.918E3','5.0E-6','5.0E-6',
            None,None,None,None,None,None,None,None,None]
        [self.cmod69_table.setItem(0,i,QTableWidgetItem(p[i])) for i in range(len(p))] #pylint: disable=W0106
        self.constit_savemat()
        #8552 Epoxy
        self.m_text.setText('3')
        self.name_text.setText('8552 Epoxy')
        self.cmod_cb.setCurrentIndex(0) #CMOD=6
        self.tempdep_cb.setChecked(False)
        p=[None,'3.45E3','3.45E3','0.35','0.35','1.61E3','42.0E-6','42.0E-6',
            None,None,None,None,None,None,None,None,None]
        [self.cmod69_table.setItem(0,i,QTableWidgetItem(p[i])) for i in range(len(p))] #pylint: disable=W0106
        self.constit_savemat()

        self.mats_list.setCurrentRow(0)
        self.fruc_cb.addItems(mats)
        self.mruc_cb.addItems(mats)


    def constit_cmod_sel(self):
        """
        Callback function to select *CONSTITUENTS CMOD parameter

        Parameters:
            None.

        Returns:
            None.
        """
        if self.cmod_cb.currentText()=='6' or self.cmod_cb.currentText()=='9' :
            self.cmod14_table.insertRow(1)
            self.cmod14_table.removeRow(0)
            self.constit_tables.setCurrentIndex(0)
        elif self.cmod_cb.currentText()=='14':
            self.cmod69_table.insertRow(1)
            self.cmod69_table.removeRow(0)
            self.constit_tables.setCurrentIndex(1)

        if self.cmod_cb.currentText()=='6':
            self.cmod69_table.setColumnHidden(8, True) #D1
            self.cmod69_table.setColumnHidden(9, True) #D2
            self.cmod69_table.setColumnHidden(10, True) #D3
        elif self.cmod_cb.currentText()=='9':
            self.cmod69_table.setColumnHidden(8, False) #D1
            self.cmod69_table.setColumnHidden(9, False) #D2
            self.cmod69_table.setColumnHidden(10, False) #D3

        self.cmod14_table.resizeColumnsToContents()
        self.cmod69_table.resizeColumnsToContents()

        self.constit_tempdep_chk()

    def constit_tempdep_chk(self):
        """
        Callback function to use temperature dependent properties

        Parameters:
            None.

        Returns:
            None.
        """

        index = self.constit_tables.currentIndex()
        page = self.constit_tables.widget(index)
        table = page.findChild(QTableWidget)

        if self.tempdep_cb.isChecked():
            table.setColumnHidden(0, False) #temp

        else:
            table.setColumnHidden(0, True) #temp

        table.resizeColumnsToContents()

    def constit_mphys_chk(self):
        """
        Callback function to perform multiphysics analysis

        Parameters:
            None.

        Returns:
            None.
        """

        if self.k_cb.isChecked():
            [self.cmod14_table.setColumnHidden(i, False) for i in range(13,19)] #pylint: disable=W0106
            [self.cmod69_table.setColumnHidden(i, False) for i in range(11,17)] #K #pylint: disable=W0106
        else:
            [self.cmod14_table.setColumnHidden(i, True) for i in range(13,19)] #pylint: disable=W0106
            [self.cmod69_table.setColumnHidden(i, True) for i in range(11,17)] #K #pylint: disable=W0106

        self.cmod14_table.resizeColumnsToContents()
        self.cmod69_table.resizeColumnsToContents()

    def constit_addrow_before(self):
        """
        Callback function to add row to cmod table before current index

        Parameters:
            None.

        Returns:
            None.
        """
        self._constit_addrow()

    def constit_addrow_after(self):
        """
        Callback function to add row to cmod table after current index

        Parameters:
            None.

        Returns:
            None.
        """
        self._constit_addrow(ioff=1)

    def _constit_addrow(self,ioff=0):
        """
        Callback function to add row to cmod table

        Parameters:
            ioff (int): 0 for before and 1 for after

        Returns:
            None.
        """
        index = self.constit_tables.currentIndex()
        page = self.constit_tables.widget(index)
        table = page.findChild(QTableWidget)
        table.insertRow(table.currentRow()+ioff)

    def constit_delrow(self):
        """
        Callback function to delete row from cmod table

        Parameters:
            None.

        Returns:
            None.
        """
        index = self.constit_tables.currentIndex()
        page = self.constit_tables.widget(index)
        table = page.findChild(QTableWidget)
        table.removeRow(table.currentRow())
        table.resizeColumnsToContents()

    def constit_savemat(self):
        """
        Callback function to save material for later use

        Parameters:
            None.

        Returns:
            None.
        """

        cur =  [self.mats_list.item(i).text() for i in range(self.mats_list.count())]
        curmats=[s.split(' - ')[0] for s in cur]
        mat=self.m_text.text()
        if not mat:
            mat=str(len(curmats)+1)
            self.m_text.setText(mat)

        add_new = False
        if mat not in curmats and int(mat)!=len(curmats)+1:
            newmat=str(len(curmats)+1)
            print(f"Renumbering material {mat} to {newmat} to be sequential...")
            mat=newmat
            self.m_text.setText(mat)
            add_new = True
        elif mat not in curmats:
            add_new = True

        name=self.name_text.text()
        mstr=f"{mat} - {name}"
        if add_new:
            item = QListWidgetItem(mstr)
            self.mats_list.addItem(item)

        self.del_mats_pb.setEnabled(True)

        #store material data within self.constits
        m = {'m':int(self.m_text.text()),'cmod':int(self.cmod_cb.currentText()),
            'matid':'U','matdb':1}
        if not name:
            self.name_text.setText(f"M = {self.m_text.text()}")
        m['comments']=[f"# -- {name}"]

        tref = self.tref_text.text()
        if tref:
            m['tref'] = tref

        index = self.constit_tables.currentIndex()
        page = self.constit_tables.widget(index)
        table = page.findChild(QTableWidget)

        if self.tempdep_cb.isChecked(): #temp dependent
            m['ntp'] = table.rowCount()
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    var=table.horizontalHeaderItem(col).text().lower()
                    txt = table.item(row, col).text()
                    if not txt:
                        continue
                    val = float(txt)
                    if var=='temp': #resetting due to mismatch in parameter name
                        var='tem'
                    if var not in m:
                        m[var]=np.zeros(m['ntp'])
                    m[var][row]=val
        else: #temp independent
            el_vars=[]
            k_vars = ['K11','K22','K33','K23','K13','K12']
            if m['cmod'] in (6,9):
                el_vars=['EA','ET','NUA','NUT','GA','ALPA','ALPT']
                m['el']=np.zeros(7)
            elif m['cmod']==14:
                el_vars=['E1','E2','E3','NU12','NU13','NU23','G12','G13','G23','ALP1','ALP2','ALP3']
                m['el']=np.zeros(12)

            for col in range(table.columnCount()):
                var=table.horizontalHeaderItem(col).text()
                txt = table.item(0, col).text()
                if not txt:
                    continue
                val = float(txt)
                if var in el_vars:
                    idx = el_vars.index(var)
                    m['el'][idx] = val
                elif var in k_vars:
                    idx = k_vars.index(var)
                    if 'k' not in m:
                        m['k']=np.zeros(6)
                    m['k'][idx]=val
                elif var in ('D1','D2','D3'):
                    if 'd' not in m:
                        m['d']=np.zeros(3)
                    m['d'][int(var[1])-1]= val

        self.constits[mstr] = m


    def constit_delmat(self):
        """
        Callback function to delete material

        Parameters:
            None.

        Returns:
            None.
        """

        for item in self.mats_list.selectedItems():
            self.constits.pop(item.text())
            self.mats_list.takeItem(self.mats_list.row(item))

        #renumber materials if needed
        keymap={}
        for i in range(self.mats_list.count()-1,-1,-1):
            item=self.mats_list.item(i)
            imat=int(item.text().split(' - ')[0])
            if imat!=i+1:
                item.setText(f"{i+1} - {item.text().split(' - ')[1]}")
                keymap[str(imat)]=str(i+1)
            else:
                keymap[str(imat)]=str(imat)


        self.constits = {
            f"{keymap.get(k.split(' - ')[0], k.split(' - ')[0])} - {k.split(' - ', 1)[1]}": v
            for k, v in self.constits.items()
        }

        for item in self.mats_list.selectedItems():
            self.m_text.setText(item.text().split(' - ')[0])

        if self.mats_list.count()==0:
            self.del_mats_pb.setEnabled(False)

    def constit_updatetable(self):
        """
        Callback function to update material tables

        Parameters:
            None.

        Returns:
            None.
        """
        self.cmod14_table.resizeColumnsToContents()
        self.cmod69_table.resizeColumnsToContents()

    def constit_populate(self):
        """
        Callback function to populate tables

        Parameters:
            None.

        Returns:
            None.
        """

        #get number and name of material from list
        liststr=self.mats_list.currentItem().text()
        mstr = liststr.split(' - ')
        mat=mstr[0]
        name=mstr[1]

        #get data
        m=self.constits[liststr]

        #populate values
        self.m_text.setText(mat)
        self.name_text.setText(name)
        ind=self.cmod_cb.findText(str(m['cmod']))
        self.cmod_cb.setCurrentIndex(ind)

        tempdep = False
        if 'ntp' in m:
            tempdep=True


        mphys = False
        if 'k' in m or 'k11' in m:
            mphys = True
        self.k_cb.setChecked(mphys)

        if not tempdep and (m['cmod']==6 or m['cmod']==9):
            self.cmod69_table.setColumnHidden(0, False)
        if not tempdep and m['cmod']==14:
            self.cmod14_table.setColumnHidden(0, False)

        curtable = None
        if m['cmod']==6 or m['cmod']==9 :
            curtable=self.cmod69_table
            el_vars = ['EA','ET','NUA','NUT','GA','ALPA','ALPT']
            if mphys:
                [self.cmod69_table.setColumnHidden(i, False) for i in range(11,17)] #K #pylint: disable=W0106
            else:
                [self.cmod69_table.setColumnHidden(i, True) for i in range(11,17)] #K #pylint: disable=W0106
        elif m['cmod']==14:
            curtable=self.cmod14_table
            el_vars = ['E1','E2','E3','NU12','NU13','NU23','G12','G13','G23','ALP1','ALP2','ALP3']
            if mphys:
                [self.cmod14_table.setColumnHidden(i, False) for i in range(13,19)] #pylint: disable=W0106
            else:
                [self.cmod14_table.setColumnHidden(i, True) for i in range(13,19)] #pylint: disable=W0106

        curtable.blockSignals(True)
        self.tempdep_cb.setChecked(tempdep)
        self.constit_tempdep_chk()
        curtable.blockSignals(False)

        el_dict={}
        k_dict={}
        k_vars = ['K11','K22','K33','K23','K13','K12']
        if not tempdep:
            el_dict = {var.lower():str(m['el'][i]) for i,var in enumerate(el_vars)}
            if 'k' in m:
                k_dict = {var.lower():str(m['k'][i]) for i,var in enumerate(k_vars)}

        curtable.setRowCount(0)
        nrows = 1
        if tempdep:
            nrows = m['ntp']
        curtable.setRowCount(nrows)
        for row in range(nrows):
            for col in range(curtable.columnCount()):
                var=curtable.horizontalHeaderItem(col).text().lower()
                if var in m: #if in this first loop, must be temperature dependent
                    item = QTableWidgetItem(str(m[var][row]))
                elif var=='temp' and 'tem' in m: #temperature
                    item = QTableWidgetItem(str(m['tem'][row]))
                elif var=='temp'and 'tem' not in m:
                    item = QTableWidgetItem("")
                elif var in ('d1','d2','d3'):
                    if var in m:
                        item = QTableWidgetItem(str(m['d'][int(var[1])-1]))
                    else:
                        item = QTableWidgetItem("")
                elif var in el_dict: #EL mech props, no temp dependence
                    item = QTableWidgetItem(el_dict[var])
                else: #thermal conductivity, no temp dependence
                    if mphys:
                        item = QTableWidgetItem(k_dict[var])
                    else:
                        item = QTableWidgetItem("")

                curtable.setItem(row,col,item)

#-----------------------------------------------------------------------------
#----------------------------------- *RUC ------------------------------------
    def _set_default_ruc(self):
        """
        Function to set default ruc

        Parameters:
            None.

        Returns:
            None.
        """

        #IM7
        self.msm_text.setText('0')
        self.ruc_name.setText('IM7/8552')
        self.fruc_cb.setCurrentIndex(0) #IM7
        self.mruc_cb.setCurrentIndex(2) #8552 epoxy
        self.mod_cb.setCurrentIndex(2) #GMC2D
        self.archid_cb.setCurrentIndex(0) #2x2
        self.vf_text.setText('0.6')
        self.ruc_save()
        self.ruc_list.setCurrentRow(0)
        self.ruc_list.item(0).setSelected(True)
        self.ruc_use()

    def ruc_define(self):
        """
        Callback function to define a single unit cell

        Parameters:
            None.

        Returns:
            None.
        """

        self.pb_RUC.setVisible(False)
        self.pb_2Dwoven_RUC.setVisible(False)
        self.indiv_unit_cell.setVisible(True)

    def ruc_go_back(self):
        """
        Callback function to return to previous selection mode

        Parameters:
            None.

        Returns:
            None.
        """

        self.pb_RUC.setVisible(True)
        self.pb_2Dwoven_RUC.setVisible(True)
        self.indiv_unit_cell.setVisible(False)

    def ruc_2dwoven_define(self):
        """
        Callback function to define a 2d woven unit cell

        Parameters:
            None.

        Returns:
            None.
        """

        mats=self._get_mats()
        w2d=woven2d_Dialog(self,mats)
        stat=w2d.exec()
        if stat: #dialog closed, can be used to do another action
            if w2d.final_ruc:
                self.ruc_define()
                if 'child' in w2d.final_ruc:
                    self.ruc_name.setText('2D Weave with Stacks')
                else:
                    self.ruc_name.setText('2D Weave')
                self.archid_cb.setEnabled(False)
                self.archid_cb.clear()
                self.mod_cb.setEnabled(False)
                self.vf_text.setEnabled(False)
                self.vf_text.setText('')
                self.r_text.setEnabled(False)
                self.r_text.setText('')
                self.fruc_cb.setEnabled(False)
                self.fruc_cb.clear()
                self.mruc_cb.setEnabled(False)
                self.mruc_cb.clear()
                #save only highest level ruc to minimize content in table
                parent = w2d.final_ruc
                self.ruc_save(ruc=parent)
                if 'child' in parent and parent['child']:
                    for child_ruc in parent['child']:
                        if 'comments' in child_ruc and child_ruc['comments']:
                            com=child_ruc['comments'][0]
                            name = self._get_name(com)
                        else:
                            name=f"RUC {child_ruc['msm']}"
                        rucstr=f"Name={name},MSM={child_ruc['msm']},MOD={child_ruc['mod']}"

                        self.avail_rucs[id(child_ruc)]=child_ruc
                        self.rucstr[rucstr]=id(child_ruc)

    def ruc_set_archid(self):
        """
        Callback function to set *RUC ARCHID

        Parameters:
            None.

        Returns:
            None.
        """

        self.archid_cb.clear()
        mod=str(self.mod_cb.currentText().replace(' ','').split('-')[0])
        if mod in ['102','202','302']:
            self.archid_cb.setEnabled(True)
            self.archid_cb.addItems(['1','2','6','13','99'])
            self.dim=2
        elif mod in ['103','203']:
            self.archid_cb.setEnabled(True)
            # self.archid_cb.addItems(['13','99']) #option 13 not in public NASMAT
            self.archid_cb.blockSignals(True)
            self.archid_cb.addItems(['99'])
            self.archid_cb.blockSignals(False)
            self.dim=3
        else:
            self.archid_cb.setEnabled(False)
            self.dim=1


    def ruc_archid_action(self):
        """
        Callback function to define actions based on archid index

        Parameters:
            None.

        Returns:
            None.
        """

        self.vf_text.setEnabled(True)
        self.fruc_cb.setEnabled(True)
        self.mruc_cb.setEnabled(True)
        self.ruc_edit_user_pb.setEnabled(False)
        self.r_text.setEnabled(False)

        archid=self.archid_cb.currentText()
        mod=self.mod_cb.currentText().replace(' ','').split('-')[0]

        if archid=='99' and mod not in ('2','3'):
            self.ruc_edit_user_pb.setEnabled(True)
            if mod.endswith('3'):
                dim=3
            else:
                dim=2
            self.vf_text.setEnabled(False)
            self.fruc_cb.setEnabled(False)
            self.mruc_cb.setEnabled(False)
            mats=self._get_all_mats()
            user_ruc=UserRUCDialog(self,mats=mats,dim=dim,mod=mod)
            stat=user_ruc.exec()
            if stat:
                if user_ruc.ruc:
                    self.ruc_save(ruc=user_ruc.ruc)

        if archid in ('6','13') and mod in ('102','202'):
            self.r_text.setEnabled(True)

    def _get_all_mats(self):
        """
        Function to get all available materials

        Parameters:
            None.

        Returns:
            mats (list): all available materials (constit and msm)
        """

        mats=self._get_mats()
        rucmats=[]
        for i in range(self.ruc_list.count()):
            avail=self.ruc_list.item(i).text()
            msm=avail.split(',')[1].split('=')[1]
            if msm!='0':
                rucmats.append(msm)
        rucmats=list(set(rucmats))
        mats+=rucmats
        return mats

    def ruc_getmats(self):
        """
        Callback function to get available materials

        Parameters:
            None.

        Returns:
            None.
        """

        mats=self._get_all_mats()

        self.fruc_cb.clear()
        self.fruc_cb.addItems(mats)
        self.mruc_cb.clear()
        self.mruc_cb.addItems(mats)

    def ruc_edit_user(self):
        """
        Callback function to edit a user-defined RUC (ARCHID=99)

        Parameters:
            None.

        Returns:
            None.
        """

        mod=self.mod_cb.currentText().replace(' ','').split('-')[0]
        if mod.endswith('3'):
            dim=3
        else:
            dim=2
        user_ruc=UserRUCDialog(self,mats=self._get_all_mats(),dim=dim,mod=mod,
                                ruc=self.avail_rucs[self.current_ruc])
        stat=user_ruc.exec()
        if stat:
            if user_ruc.ruc:
                self.ruc_save(ruc=user_ruc.ruc)

    def ruc_add_rot(self):
        """
        Callback function to disable/enable RUC rotations

        Parameters:
            None.

        Returns:
            None.
        """

        self.ruc_rot_table.setEnabled(self.ruc_rot_chk.isChecked())

    def ruc_rot_resize(self,item):
        """
        Callback function to resize the RUC rotation table

        Parameters:
            item (QTableWidgetItem): item triggering resize

        Returns:
            None.
        """

        self.ruc_rot_table.blockSignals(True)
        self.ruc_rot_table.resizeColumnToContents(item.column())
        self.ruc_rot_table.blockSignals(False)

    def _ruc_rot_chk_orthog(self):
        """
        Function to check if ruc rotation vectors are orthogongal

        Parameters:
            None

        Returns:
            msg (str): error message if found
            v (list): d1,d2,d3 vectors
        """

        msg=''
        err = 0.001 #matches NASMAT impelentation of check
        v = []
        for r in range(self.ruc_rot_table.rowCount()):
            row_vals = []
            for c in range(self.ruc_rot_table.columnCount()):
                item = self.ruc_rot_table.item(r, c)
                if item is None or not item.text().strip():
                    item.setText('0.0')

                try:
                    val = float(item.text())
                    row_vals.append(val)
                except ValueError:
                    msg += f"Rotation value in row={r}, col={c} is invalid."
                    row_vals.append('0.0')

            v.append(np.array(row_vals, dtype=np.double))

        if msg:
            return msg

        dd1=np.dot(v[0],v[1])
        if abs(dd1)>=err:
            msg+=f"Vectors D1,D2 not orthogonal, err={dd1}\n"
        dd2=np.dot(v[0],v[2])
        if abs(dd2)>=err:
            msg+=f"Vectors D1,D3 not orthogonal, err={dd2}\n"
        dd3=np.dot(v[1],v[2])
        if abs(dd3)>=err:
            msg+=f"Vectors D2,D3 not orthogonal, err={dd3}\n"

        if msg:
            return msg

        return v

    def ruc_save(self,ruc=None):
        """
        Callback function to save a single unit cell

        Parameters:
            ruc (dict): input ruc parameters

        Returns:
            None.
        """

        v = None
        if self.ruc_rot_chk.isChecked():
            v = self._ruc_rot_chk_orthog()
            if isinstance(v,str): #error found
                QMessageBox.critical(None, 'Error', v[:-1])
                return

        name=self.ruc_name.text()
        msm=self.msm_text.text()
        mod=self.mod_cb.currentText().replace(' ','').split('-')[0]
        archid=self.archid_cb.currentText()
        vf=self.vf_text.text()
        r=self.r_text.text()
        f=self.fruc_cb.currentText()
        m=self.mruc_cb.currentText()

        from_weave2d=False
        if archid=='':
            archid='99'
            from_weave2d=True

        #if ruc is not defined, get built-in architecture
        if archid!='99':
            if not r:
                r='1.0'
            if self.dim==2:
                p={}
                ruc=get_builtin_ruc_2d(int(archid),float(vf),int(f),int(m),float(r),p)
                ruc['DIM']='2D'
            elif self.dim==3:
                p={}
                asp=1.0 #not used by current options
                ruc=get_builtin_ruc_3d(int(archid),float(vf),int(f),int(m),float(r),asp,{})
                ruc['DIM']='3D'
            else:
                ruc['DIM']='1D'

            ruc['vf']=float(vf)
            ruc['f']=int(f)
            ruc['m']=int(m)
            if self.r_text.isEnabled():
                ruc['r']=float(r)

        if not ruc:
            ruc = {}

        ruc['comments']=[name]
        ruc['msm']=int(msm)
        ruc['archid']=int(archid)

        if v:
            ruc.update(dict(zip(('d1', 'd2', 'd3'), v)))

        if 'mod' not in ruc.keys():
            ruc['mod']=int(mod)
        else:
            mod = ruc['mod']

        check=[msm,mod,archid,vf,f,m]
        rucstr=''
        if '' not in check and archid!='99':
            rucstr=f"Name={name},MSM={msm},MOD={mod},ARCHID={archid},VF={vf},F={f},M={m}"
        elif archid=='99' or from_weave2d:
            rucstr=f"Name={name},MSM={msm},MOD={mod},ARCHID={archid}"

        self._ruc_add_to_save(rucstr,ruc)

    def _ruc_add_to_save(self,rucstr,ruc):
        """
        Function to add ruc to availble table

        Parameters:
            None.

        Returns:
            None.
        """
        #optional logic to never overwrite rucs
        # if id(ruc) in self.avail_rucs:
        #     # ruc['name']=ruc['name']+'_1'
        #     rucstr=rucstr+'_1'
        #     ruc_add = copy.deepcopy(ruc)
        # else:
        #     ruc_add = ruc

        ruc_add = ruc

        add_ruc = True
        for _,aruc in self.avail_rucs.items():

            same = all((np.array_equal(aruc[k], ruc_add[k])
                        if isinstance(aruc[k], np.ndarray)
                        else aruc[k] == ruc_add[k]) for k in ruc_add)
            if same:
                add_ruc=False
                break

        if add_ruc:
            self.avail_rucs[id(ruc_add)]=ruc_add
            self.rucstr[rucstr] = id(ruc_add)
            item = QListWidgetItem(rucstr)
            self.ruc_list.addItem(item)
            self.ruc_delavail_pb.setEnabled(True)
            self.ruc_getmats()

    def _get_used_rucs(self, target_key=None, column=2):
        """
        function to check if a target RUC is used in the tree

        Parameters:
            target_key (int): memory address of ruc to look for
            column (int): ruc id value

        Returns:
            tuple:
                bool: logical indicating whether an RUC is being used
                TreeWidgetItem: the matching item in the tree 
        """
        def recurse(item):
            """
            recursive function to check if a target RUC is used in the tree

            Parameters:
                item (QTreeWidgetItem): current item in tree

            Returns:
                tuple:
                    bool: logical indicating whether an RUC is being used
                    TreeWidgetItem: the matching item in the tree 
            """
            # Check if this item matches target_key
            if target_key is not None and int(item.text(column)) == target_key:
                return True, item

            # Check children recursively
            for i in range(item.childCount()):
                found, child_item = recurse(item.child(i))
                if found:
                    return True, child_item

            return False, None

        for i in range(self.ruc_tree.topLevelItemCount()):
            found, item = recurse(self.ruc_tree.topLevelItem(i))
            if found:
                return True, item

        #no items present
        return False, None

    def ruc_delavail(self):
        """
        Callback function to delete selected unit cells

        Parameters:
            None.

        Returns:
            None.
        """
        self.ruc_list.blockSignals(True)
        self.ruc_tree.blockSignals(True)
        for item in self.ruc_list.selectedItems():
            key=item.text()
            found,_ = self._get_used_rucs(self.rucstr[key])
            if not found:
                self.ruc_list.takeItem(self.ruc_list.row(item))
                self.avail_rucs.pop(self.rucstr[key], None)
                self.rucstr.pop(key,None)
            else:
                QMessageBox.warning(None,"Warning",
                    "The action cannot be completed because the selected RUC is used.")
        if self.ruc_list.count()==0:
            self.ruc_delavail_pb.setEnabled(False)
            self.ruc_tree.clear()

        self.ruc_list.blockSignals(False)
        self.ruc_tree.blockSignals(False)

    def _get_mat_str(self,ruc):
        """
        Function to get a string of materials in the unit cell

        Parameters:
            None.

        Returns:
            None.
        """

        mats=np.unique(ruc['sm'].astype(int).flatten())
        pos=np.sort(mats[mats>0])
        neg=np.sort(mats[mats<0])[::-1]

        return ','.join(map(str,np.concatenate((pos,neg))))

    def ruc_use(self):
        """
        Callback function to use unit cells in NASMAT

        Parameters:
            None.

        Returns:
            None.
        """

        self.ruc_list.blockSignals(True)
        self.ruc_tree.blockSignals(True)

        if self.ruc_list.selectedItems():
            parent=self.ruc_tree.invisibleRootItem()
            parent.setExpanded(True)
            child = QTreeWidgetItem()
            rucstr=self.ruc_list.currentItem().text()
            self.ruc_list.clearSelection()
            child.setText(0,rucstr)
            child.setText(1,self._get_mat_str(self.avail_rucs[self.rucstr[rucstr]]))
            child.setText(2,str(self.rucstr[rucstr])) #key within avail_rucs (not visible)
            parent.addChild(child)

            ruc=self.avail_rucs[self.rucstr[rucstr]]
            if 'child' in ruc and ruc['child']:
                for newruc in ruc['child']:
                    newchild = QTreeWidgetItem()
                    if 'comments' in newruc and newruc['comments']:
                        com=newruc['comments'][0]
                        name = self._get_name(com)
                    else:
                        name=f"RUC {newruc['msm']}"
                    rucstr=f"Name={name},MSM={newruc['msm']},MOD={newruc['mod']}"
                    newchild.setText(0,rucstr)
                    newchild.setText(1,self._get_mat_str(ruc=newruc))
                    newchild.setText(2,str(self.rucstr[rucstr]))
                    child.addChild(newchild)
                    newchild.setExpanded(True)
                child.setExpanded(True)

            for i in range(self.ruc_tree.columnCount()):
                self.ruc_tree.resizeColumnToContents(i)

            self.ruc_tree.clearSelection()

        self.ruc_list.blockSignals(False)
        self.ruc_tree.blockSignals(False)

    def ruc_reorder_up(self):
        """
        Callback function to move a unit cell one position up

        Parameters:
            None.

        Returns:
            None.
        """

        self._ruc_move(0)

    def ruc_reorder_down(self):
        """
        Callback function to move a unit cell one position down

        Parameters:
            None.

        Returns:
            None.
        """

        self._ruc_move(1)

    def ruc_addto_upperlevel(self):
        """
        Callback function to move a unit cell one level up

        Parameters:
            None.

        Returns:
            None.
        """

        self._ruc_move(2)

    def ruc_addto_lowerlevel(self):
        """
        Callback function to move a unit cell one level down

        Parameters:
            None.

        Returns:
            None.
        """
        self._ruc_move(3)

    def _ruc_move(self,mode):
        """
        Function to move a unit cell in the NASMAT hierarchy

        Parameters:
            mode (int): parameter to define move type

        Returns:
            None.
        """

        item=self.ruc_tree.currentItem()
        if item:
            root = self.ruc_tree.invisibleRootItem()
            parent=(item.parent() or root)

            if mode<=1: #reorder up/down

                mv = None
                iloc=parent.indexOfChild(item)
                if mode==0: #move up
                    mv=-1
                    if iloc==0:
                        return
                elif mode==1: #move down
                    mv=1
                    if self.ruc_tree.itemBelow(item) is None:
                        return
                child=parent.takeChild(iloc)
                parent.insertChild(iloc+mv,child)
                parent.setExpanded(True)
                child.setExpanded(True)
            elif mode==2: #move up level, make child of parent's parent
                gparent=(parent.parent() or root)
                if parent!=gparent:
                    iloc=parent.indexOfChild(item)
                    child=parent.takeChild(iloc)
                    giloc=gparent.indexOfChild(parent)
                    gparent.insertChild(giloc+1,child)
                    gparent.setExpanded(True)
                    parent.setExpanded(True)
                    child.setExpanded(True)
            elif mode==3: #move down level, make child of previous item
                newitem=(self.ruc_tree.itemAbove(item) or root)
                newparent=(newitem.parent() or root)
                while newparent!=root and newparent!=parent:
                    newitem=(self.ruc_tree.itemAbove(newitem) or root)
                    newparent=(newitem.parent() or root)

                iloc=parent.indexOfChild(item)
                if iloc!=0:
                    child=parent.takeChild(iloc)
                    newitem.addChild(child)
                    newitem.setExpanded(True)
                    parent.setExpanded(True)
                    child.setExpanded(True)

    def ruc_delused(self):
        """
        Callback function to remove a used unit cell from the table

        Parameters:
            None.

        Returns:
            None.
        """

        self.ruc_tree.blockSignals(True)
        selected=self.ruc_tree.selectedItems()
        if selected:
            root = self.ruc_tree.invisibleRootItem()
            for item in selected:
                (item.parent() or root).removeChild(item)
        self.ruc_tree.blockSignals(False)

    def ruc_populate_inputs(self):
        """
        Callback function to populate ruc inputs

        Parameters:
            None.

        Returns:
            None.
        """

        sender = self.sender()
        #get the ruc string, only the first if multiple are selected
        rucstr = None
        if sender == self.ruc_list:
            rucstr=self.ruc_list.currentItem().text()
            self.ruc_tree.blockSignals(True)
            self.ruc_tree.clearSelection()
            self.ruc_tree.blockSignals(False)
        elif sender == self.ruc_tree:
            rucstr=self.ruc_tree.selectedItems()[0].text(0)
            self.ruc_list.blockSignals(True)
            self.ruc_list.clearSelection()
            self.ruc_list.blockSignals(False)

        self.ruc_define()

        d = dict(kv.split('=') for kv in rucstr.split(','))
        self.msm_text.setText(d['MSM'])
        self.ruc_name.setText(d['Name'])
        ind=self.mod_cb.findText(d['MOD'], Qt.MatchStartsWith)
        self.archid_cb.blockSignals(True)
        self.mod_cb.setCurrentIndex(ind)
        ind=self.archid_cb.findText(d['ARCHID'], Qt.MatchStartsWith)
        self.archid_cb.setCurrentIndex(ind)
        self.archid_cb.blockSignals(False)

        if d['ARCHID'] != '99':
            ind=self.fruc_cb.findText(d['F'], Qt.MatchStartsWith)
            self.fruc_cb.setCurrentIndex(ind)
            ind=self.mruc_cb.findText(d['M'], Qt.MatchStartsWith)
            self.mruc_cb.setCurrentIndex(ind)
            self.vf_text.setEnabled(True)
            self.vf_text.setText(d['VF'])
            self.ruc_edit_user_pb.setEnabled(False)
        else:
            self.vf_text.setEnabled(False)
            self.vf_text.clear()
            self.ruc_edit_user_pb.setEnabled(True)

        self.current_ruc = self.rucstr[rucstr]
        ruc = self.avail_rucs[self.current_ruc]
        if 'r' in ruc.keys():
            self.r_text.setEnabled(True)
            self.r_text.setText(str(ruc['r']))
        else:
            self.r_text.setEnabled(False)
            self.r_text.clear()
        if 'asp' in ruc.keys():
            self.asp_text.setEnabled(True)
            self.asp_text.setText(str(ruc['asp']))
        else:
            self.asp_text.setEnabled(False)
            self.asp_text.clear()
        if 'd1' in ruc.keys():
            self.ruc_rot_chk.setChecked(True)
            self.ruc_rot_table.setEnabled(True)
            v = [ruc['d1'],ruc['d2'],ruc['d3']]
            for r in range(self.ruc_rot_table.rowCount()):
                for c in range(self.ruc_rot_table.columnCount()):
                    item = self.ruc_rot_table.item(r,c)
                    item.setText(str(v[r][c]))
        else:
            self.ruc_rot_chk.setChecked(False)
            self.ruc_rot_table.setEnabled(False)
            for r in range(self.ruc_rot_table.rowCount()):
                for c in range(self.ruc_rot_table.columnCount()):
                    item = self.ruc_rot_table.item(r,c)
                    if r==c:
                        item.setText('1.0')
                    else:
                        item.setText('0.0')


#-----------------------------------------------------------------------------
#----------------------------- Damage/Failure ------------------------------
    def _set_default_failsub(self):
        """
        Function to set default failure properties

        Parameters:
            None.

        Returns:
            None.
        """

        nmats=len(self.constits.keys())
        [self.failsub_addrow() for i in range(nmats)] #pylint: disable=W0106

        fs=[['4335','113','113','128','138','138','None','2608','354','354'],
            ['2358','2358','2358','1000','1000','1000','None','1653','1653','1653'],
            ['59.4','59.4','59.4','112','112','112','None','259','259','259']]

        for i in range(nmats):
            self.fs_table.cellWidget(i,1).setCurrentIndex(i)
            self.fs_table.cellWidget(i,9).setCurrentIndex(0)
            self.fs_table.cellWidget(i,13).setCurrentIndex(2)
            for j in range(10):
                if j==6:
                    continue
                item=QTableWidgetItem()
                item.setText(fs[i][j])
                self.fs_table.setItem(i,j+3,item)

    def failsub_tempdep_chk(self):
        """
        Callback function to use temperature dependent failure properties

        Parameters:
            None.

        Returns:
            None.
        """

        if self.fs_tempdep_chk.isChecked():
            self.fs_table.setColumnHidden(0, False) #temp

        else:
            self.fs_table.setColumnHidden(0, True) #temp

        self.fs_table.resizeColumnsToContents()

    def failsub_addrow(self):
        """
        Callback function to add row to failure table

        Parameters:
            None.

        Returns:
            None.
        """

        self.fs_table.insertRow(self.fs_table.rowCount())

        fsmats_cb=QComboBox()
        fsmats_cb.addItems(self._get_mats())
        fsmats_cb.setEnabled(True)
        self.fs_table.setCellWidget(self.fs_table.rowCount()-1,1,fsmats_cb)

        fsopts_cb=QComboBox()
        fsopts_cb.addItems(self.failsub_opts)
        fsopts_cb.setEnabled(True)
        self.fs_table.setCellWidget(self.fs_table.rowCount()-1,2,fsopts_cb)

        fscomp_cb=QComboBox()
        fscomp_cb.setEnabled(True)
        fscomp_cb.addItems(['DIF','SAM','OFF'])
        fscomp_cb.setCurrentIndex(1)
        fscomp_cb.currentIndexChanged.connect(self.failsub_showhide_comp)
        self.fs_table.setCellWidget(self.fs_table.rowCount()-1,9,fscomp_cb)

        fsact_cb=QComboBox()
        fsact_cb.addItems(['-1 - Stop Exec.','0 - Do Nothing, Cont.',
                            '1 - Zero Stiff., Cont.','2 - Dir. Dmg., Cont.',
                            '3 - PDFA Model'])
        fsact_cb.setEnabled(True)
        fsact_cb.setCurrentIndex(2)
        self.fs_table.setCellWidget(self.fs_table.rowCount()-1,13,fsact_cb)

        fsnorm_cb=QComboBox()
        fsnorm_cb.addItems(['1 - Dmg. only in x2-x3 plane (crit=8,9)',
                            '2 - Dmg. only in plane (crit=8,9)',
                            '3 - Dmg. only in plane (crit=8,9)' ])
        fsnorm_cb.setEnabled(True)
        self.fs_table.setCellWidget(self.fs_table.rowCount()-1,14,fsnorm_cb)

        self.fs_table.resizeColumnsToContents()


    def failsub_showhide_comp(self, item):
        """
        Callback function to show or hide component values in failsub table

        Parameters:
            item

        Returns:
            None.
        """

        if item == 0: #COMPR
            self.fs_table.setColumnHidden(10, False) #XC11
            self.fs_table.setColumnHidden(11, False) #XC22
            self.fs_table.setColumnHidden(12, False) #XC33

        hide_cols=True
        for row in range(self.fs_table.rowCount()):
            wid = self.fs_table.cellWidget(row,9)
            if wid.currentText()=='DIF':
                hide_cols=False
                break

        if hide_cols:
            self.fs_table.setColumnHidden(10, True) #XC11
            self.fs_table.setColumnHidden(11, True) #XC22
            self.fs_table.setColumnHidden(12, True) #XC33

        self.fs_table.resizeColumnsToContents()

    def failsub_delrow(self):
        """
        Callback function to delete row to failure table

        Parameters:
            None.

        Returns:
            None.
        """

        self.fs_table.removeRow(self.fs_table.currentRow())
        self.fs_table.resizeColumnsToContents()

    def failsub_updatetable(self):
        """
        Callback function to update failure table

        Parameters:
            None.

        Returns:
            None.
        """

        self.fs_table.resizeColumnsToContents()

    def pdfa_addrow(self):
        """
        Callback function to add row to pdfa table

        Parameters:
            None.

        Returns:
            None.
        """

        self.pdfa_table.insertRow(self.pdfa_table.rowCount())

        pdfamats_cb=QComboBox()
        pdfamats_cb.addItems(self._get_mats())
        pdfamats_cb.setEnabled(True)
        self.pdfa_table.setCellWidget(self.pdfa_table.rowCount()-1,0,pdfamats_cb)

        pdfacmod_cb=QComboBox()
        pdfacmod_cb.addItems(['1 - Crack Band'])
        pdfacmod_cb.setEnabled(True)
        self.pdfa_table.setCellWidget(self.pdfa_table.rowCount()-1,1,pdfacmod_cb)

        pdfacoh_cb=QComboBox()
        pdfacoh_cb.addItems(['1 - Camanho-Davila Mixed Mode'])
        pdfacoh_cb.setEnabled(True)
        self.pdfa_table.setCellWidget(self.pdfa_table.rowCount()-1,2,pdfacoh_cb)

        pdfacmm_cb=QComboBox()
        pdfacmm_cb.addItems(['1 - Power Law'])
        pdfacmm_cb.setEnabled(True)
        self.pdfa_table.setCellWidget(self.pdfa_table.rowCount()-1,5,pdfacmm_cb)

        self.pdfa_table.resizeColumnsToContents()

    def pdfa_delrow(self):
        """
        Callback function to delete row in pdfa table

        Parameters:
            None.

        Returns:
            None.
        """

        self.pdfa_table.removeRow(self.pdfa_table.currentRow())
        self.pdfa_table.resizeColumnsToContents()
#-----------------------------------------------------------------------------
#--------------------------------- Solution ----------------------------------

    def _set_default_soln(self):
        """
        Function to set default solution

        Parameters:
            None.

        Returns:
            None.
        """

        self.mech_cb.setChecked(True)
        self.mech_gb.setEnabled(True)
        self.mechsync_pb.setEnabled(False)
        self.mech_table.setColumnHidden(0, True) #component
        self.solv_cb.setChecked(True)
        self.solv_gb.setEnabled(True)
        self.solsync_pb.setEnabled(False)
        t=[['0.0','0.0','-'],
           ['1.0','0.03','1']]
        for i in range(self.mech_table.rowCount()):
            mechcomp_cb=QComboBox()
            mechcomp_cb.addItems(['11','22','33','23','13','12'])
            mechcomp_cb.setEnabled(True)
            self.mech_table.setCellWidget(i,0,mechcomp_cb)
            for j in range(self.mech_table.columnCount()-1):
                item=QTableWidgetItem()
                item.setText(t[i][j])
                self.mech_table.setItem(i,j+1,item)

        self.mphys_table.setColumnHidden(0, True) #component
        for i in range(self.mech_table.rowCount()):
            mphyscomp_cb=QComboBox()
            mphyscomp_cb.addItems(['11','22','33'])
            mphyscomp_cb.setEnabled(True)
            self.mphys_table.setCellWidget(i,0,mphyscomp_cb)

        t=[['0.0','-'],
           ['1.0','0.001']]
        for i in range(self.sol_table.rowCount()):
            for j in range(self.sol_table.columnCount()):
                item=QTableWidgetItem()
                item.setText(t[i][j])
                self.sol_table.setItem(i,j,item)

    def mech_use(self):
        """
        Callback function to use *MECH

        Parameters:
            None.

        Returns:
            None.
        """
        chk=self.mech_cb.isChecked()
        self.mech_gb.setEnabled(chk)
        self.mechsync_pb.setEnabled(False)
        if chk: #require solve if using *MECH
            self.solv_cb.setChecked(True)
            self.solv_use()

    def mech_lop_change(self):
        """
        Callback function to select *MECH LOP

        Parameters:
            None.

        Returns:
            None.
        """

        lop_map={'1':'11','2':'22','3':'33','4':'23','5':'13','6':'12'}
        cur_lop=self.lop_cb.currentText()
        if cur_lop=='99':
            self.mech_table.setColumnHidden(0, False) #component
        else:
            self.mech_table.setColumnHidden(0, True) #component
            rows_to_delete=[]
            for row in range(self.mech_table.rowCount()):
                row_w = self.mech_table.cellWidget(row,0)
                if not row_w:
                    continue
                lop=row_w.currentText()
                if lop_map[cur_lop]!=lop:
                    rows_to_delete.append(row)
            for row in reversed(rows_to_delete):
                self.mech_table.removeRow(row)

    def mech_add(self):
        """
        Callback function to add row to mech table

        Parameters:
            None.

        Returns:
            None.
        """

        row = self.mech_table.rowCount()
        self.mech_table.insertRow(row)
        mechcomp_cb=QComboBox()
        mechcomp_cb.addItems(['11','22','33','23','13','12'])
        mechcomp_cb.setEnabled(True)
        self.mech_table.setCellWidget(row,0,mechcomp_cb)

        return row

    def mech_rm(self):
        """
        Callback function to remove row from mech table

        Parameters:
            None.

        Returns:
            None.
        """

        self.mech_table.removeRow(self.mech_table.currentRow())
        self.mech_table.resizeColumnsToContents()

    def mech_sync(self):
        """
        Callback function to sync mech table with others

        Parameters:
            None.

        Returns:
            None.
        """

        #TODO: add mech_sync

    def mech_clear_table(self):
        """
        Callback function to clear mech table

        Parameters:
            None.

        Returns:
            None.
        """

        self.mech_table.clearContents()

    def mphys_use(self):
        """
        Callback function to use *MULTIPHYICS

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.mphys_cb.isChecked()
        self.mphys_gb.setEnabled(chk)
        self.mphyssync_pb.setEnabled(False)
        if chk: #require solve if using *MULTIPHYSICS
            self.solv_cb.setChecked(True)
            self.solv_use()

    def mphys_lop_change(self):
        """
        Callback function to define *MULTIPHYSICS LOP

        Parameters:
            None.

        Returns:
            None.
        """

        lop_map={'1':'11','2':'22','3':'33'}
        cur_lop=self.mphys_lop_cb.currentText()
        if cur_lop=='99':
            self.mphys_table.setColumnHidden(0, False) #component
        else:
            self.mphys_table.setColumnHidden(0, True) #component
            rows_to_delete=[]
            for row in range(self.mphys_table.rowCount()):
                row_w = self.mphys_table.cellWidget(row,0)
                if not row_w:
                    continue
                lop=row_w.currentText()
                if lop_map[cur_lop]!=lop:
                    rows_to_delete.append(row)
            for row in reversed(rows_to_delete):
                self.mphys_table.removeRow(row)

    def mphys_add(self):
        """
        Callback function to add row to multiphysics table

        Parameters:
            None.

        Returns:
            None.
        """

        row = self.mphys_table.rowCount()
        self.mphys_table.insertRow(row)
        mphyscomp_cb=QComboBox()
        mphyscomp_cb.addItems(['11','22','33'])
        mphyscomp_cb.setEnabled(True)
        self.mphys_table.setCellWidget(row,0,mphyscomp_cb)

        return row

    def mphys_rm(self):
        """
        Callback function to remove row from multiphysics table

        Parameters:
            None.

        Returns:
            None.
        """

        self.mphys_table.removeRow(self.mphys_table.currentRow())
        self.mphys_table.resizeColumnsToContents()

    def mphys_sync(self):
        """
        Callback function to sync multiphysics table with others

        Parameters:
            None.

        Returns:
            None.
        """

        #TODO: add mphys_sync

    def mphys_clear_table(self):
        """
        Callback function to clear multiphysics table 

        Parameters:
            None.

        Returns:
            None.
        """

        self.mphys_table.clearContents()

    def therm_use(self):
        """
        Callback function to use *THERM 

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.therm_cb.isChecked()
        self.therm_gb.setEnabled(chk)
        self.thermsync_pb.setEnabled(False)

    def therm_add(self):
        """
        Callback function to add row from therm table

        Parameters:
            None.

        Returns:
            None.
        """

        self.therm_table.insertRow(self.therm_table.currentRow()+1)

    def therm_rm(self):
        """
        Callback function to remove row from therm table

        Parameters:
            None.

        Returns:
            None.
        """

        self.therm_table.removeRow(self.therm_table.currentRow())
        self.therm_table.resizeColumnsToContents()

    def therm_sync(self):
        """
        Callback function to sync therm table with others

        Parameters:
            None.

        Returns:
            None.
        """

        #TODO: add therm_sync

    def therm_clear_table(self):
        """
        Callback function to clear therm table

        Parameters:
            None.

        Returns:
            None.
        """

        self.therm_table.clearContents()

    def solv_use(self):
        """
        Callback function to use *SOLVER

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.solv_cb.isChecked()
        self.solv_gb.setEnabled(chk)
        self.solsync_pb.setEnabled(False)

    def solv_add(self):
        """
        Callback function to add row to solver table

        Parameters:
            None.

        Returns:
            None.
        """

        self.sol_table.insertRow(self.sol_table.currentRow()+1)

    def solv_rm(self):
        """
        Callback function to remove row from solver table

        Parameters:
            None.

        Returns:
            None.
        """

        self.sol_table.removeRow(self.sol_table.currentRow())
        self.sol_table.resizeColumnsToContents()

    def solv_sync(self):
        """
        Callback function to sync solver table with others

        Parameters:
            None.

        Returns:
            None.
        """

        #TODO: add solv_sync

    def solv_clear_table(self):
        """
        Callback function to clear solver table

        Parameters:
            None.

        Returns:
            None.
        """

        self.sol_table.clearContents()

#-----------------------------------------------------------------------------
#---------------------------------- Output -----------------------------------
    def _set_default_output(self):
        """
        Function to set default output

        Parameters:
            None.

        Returns:
            None.
        """

        self.npl_cb.setCurrentIndex(2)

    def h5_use(self):
        """
        Callback function to use *HDF5

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.hdf5_chk.isChecked()
        self.hdf5_gb.setEnabled(chk)
        #TODO: fix glitchy hdf5 maxlev button, enabling group box
        self.maxlev_text.setEnabled(chk)
        self.maxlev_label.setEnabled(chk)

    def xy_use(self):
        """
        Callback function to use *XYPLOT

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.xyplot_cb.isChecked()
        self.xyplot_gb.setEnabled(chk)

    def xy_addmac(self):
        """
        Callback function to add row to *XYPLOT macro table

        Parameters:
            None.

        Returns:
            None.
        """

        self.macro_table.insertRow(self.macro_table.currentRow()+1)

    def xy_addmic(self):
        """
        Callback function to add row to *XYPLOT micro table

        Parameters:
            None.

        Returns:
            None.
        """

        self.micro_table.insertRow(self.micro_table.currentRow()+1)

    def xy_rmmac(self):
        """
        Callback function to remove row from *XYPLOT macro table

        Parameters:
            None.

        Returns:
            None.
        """

        self.macro_table.removeRow(self.macro_table.currentRow())
        self.macro_table.resizeColumnsToContents()

    def xy_rmmic(self):
        """
        Callback function to remove row from *XYPLOT micro table

        Parameters:
            None.

        Returns:
            None.
        """

        self.micro_table.removeRow(self.micro_table.currentRow())
        self.micro_table.resizeColumnsToContents()

    def matlab_use(self):
        """
        Callback function to use *MATLAB

        Parameters:
            None.

        Returns:
            None.
        """

        chk=self.matlab_chk.isChecked()
        self.matlab_gb.setEnabled(chk)


#-----------------------------------------------------------------------------
    def cancel_macinp(self):
        """
        Callback function to revert mac input changes

        Parameters:
            None.

        Returns:
            None.
        """

        #revert material numbers from actual to indexed
        if 'rev_mat_map' in self.mac.keys():
            vmapf = np.vectorize(self.mac['rev_mat_map'].get)
            for key in self.mac['ruc']['rucs'].keys():
                ruc=self.mac['ruc']['rucs'][key]
                ruc['sm']=vmapf(ruc['sm'])

        #return to calling program.
        self.reject()


    def save_macinp(self):
        """
        Callback function to save all mac parameters to dict

        Parameters:
            None.

        Returns:
            None.
        """

        self.mac['constit']={}
        self.mac['ruc']={}
        self.mac['failsub']={}
        self.mac['pdfa']={}
        self.mac['hdf5']={}
        self.mac['xy']={}
        self.mac['matlab']={}
        self.mac['print']={}
        self.mac['mech']={}
        self.mac['multiphysics']={}
        self.mac['therm']={}
        self.mac['solver']={}
        self.mac['probtype']={}
        self.mac['ext']={}
        #*CONSTITUENTS
        c={'nmats':len(self.constits.keys()),'mats':{}}

        for key in self.constits.keys():
            c['mats'][key.split(' - ')[0]]=self.constits[key]

        self.mac['constit']=c

        #*RUC
        # -- get and store tree
        self.mac['rucs_avail'] = {k:self.avail_rucs[v] for k,v in self.rucstr.items()}
        self.mac['rucs_used_tree'] = self._get_ruc_tree()
        self.mac['ruc']={}
        self.mac['ruc']['nrucs']=0
        self.mac['ruc']['rucs']={}
        self.mac['ruc']['crot']={}
        item=self.ruc_tree.topLevelItem(0)
        while item is not None:
            self.mac['ruc']['nrucs']+=1
            rucstr=item.text(0)
            iruc = self.rucstr[rucstr]
            #assumes that only one msm number is used (no duplicates)
            msm = str(self.avail_rucs[iruc]['msm'])
            self.mac['ruc']['rucs'][msm]=self.avail_rucs[iruc]
            if 'crot' in self.avail_rucs[iruc] and self.avail_rucs[iruc]['crot']:
                self.mac['ruc']['crot'][msm]= self.avail_rucs[iruc]['crot']
                # self.mac['ruc']['rucs'][msm].pop('crot')
            item=self.ruc_tree.itemBelow(item)

        #Set other required dicts
        rucs=self.mac['ruc']['rucs']
        all_mats=[np.arange(1,self.mac['constit']['nmats']+1)]
        [all_mats.append(rucs[key]['sm'].flatten()) for key in rucs.keys()]  #pylint: disable=W0106
        all_mats=np.unique(np.concatenate(all_mats)).astype(int)
        self.mac['mat_map']={i:all_mats[i] for i in range(all_mats.shape[0])}
        self.mac['rev_mat_map']={all_mats[i]:i for i in range(all_mats.shape[0])}
        self.mac['ruc_map']={str(rucs[key]['msm']): str(i + 1) for i, key in enumerate(rucs)}

        nmp={key : self.mac['mat_map'][key] for key in self.mac['mat_map'].keys()}
        vmapf = np.vectorize(self.mac['rev_mat_map'].get)
        for key in self.mac['ruc']['rucs'].keys():
            ruc=self.mac['ruc']['rucs'][key]
            ruc['sm']=vmapf(ruc['sm'])
            ruc['all_mats']=np.vectorize(nmp.get)(ruc['sm']).astype(int)
            ruc['all_mats_uniq'],ruc['all_mats_uniq_cnt']=\
                np.unique(ruc['all_mats'], return_counts=True)

        #*FAILURE_SUBCELL
        fs={}
        tkeys = ['temp', 'x11', 'x22', 'x33', 'x23', 'x13', 'x12', 'x11c', 'x22c', 'x33c']
        critcnt = {}
        for row in range(self.fs_table.rowCount()):
            rd={}
            for col in range(self.fs_table.columnCount()):
                var=self.fs_table.horizontalHeaderItem(col).text().lower()
                item=self.fs_table.item(row,col)
                tempdep = self.fs_tempdep_chk.isChecked()
                if item and item.text():
                    if tempdep and var in tkeys:
                        rd[var]=[float(item.text())]
                    else:
                        rd[var]=float(item.text())
                else:
                    widget=self.fs_table.cellWidget(row,col)
                    if isinstance(widget,QComboBox):
                        text=widget.currentText()
                        if var=='mat':
                            rd[var]=int(text)
                        elif var=='compr':
                            rd[var]=text
                        elif var in ('crit','action','norm'):
                            rd[var]=text.split(' ')[0]

            if rd['action']!='3':
                rd.pop('norm')

            mat=str(rd['mat'])

            if mat not in fs:
                fs[mat]={'mat':rd['mat'],'crits':{}}

            if mat not in critcnt:
                critcnt[mat]=[]
            if rd['crit'] not in critcnt[mat]:
                critcnt[mat].append(rd['crit'])

            icrit = str(critcnt[mat].index(rd['crit']))

            rd.pop('mat')
            if tempdep:
                if icrit not in fs[mat]['crits']:
                    fs[mat]['crits'][icrit]=rd
                else:
                    for key in fs[mat]['crits'][icrit]:
                        if key in tkeys:
                            fs[mat]['crits'][icrit][key].extend(rd[key])
                        else:
                            fs[mat]['crits'][icrit][key]=rd[key]
            else:
                fs[mat]['crits'][icrit]=rd

        for key,val in fs.items():
            val['ncrit']=len(val['crits'])
            for _,crit in val['crits'].items():
                if tempdep and 'temp' in crit:
                    crit['ntemp'] = len(crit['temp'])
                elif tempdep and not 'temp' in crit:
                    for kk in crit:
                        if isinstance(crit[kk],list):
                            crit[kk] = crit[kk][0]

        self.mac['failsub']['nmat']=len(fs)
        self.mac['failsub']['mats']=fs

        #*PDFA
        dmg={'mats':{}}
        for row in range(self.pdfa_table.rowCount()):
            rd={}
            for col in range(self.pdfa_table.columnCount()):
                var=self.pdfa_table.horizontalHeaderItem(col).text().lower()
                item=self.pdfa_table.item(row,col)

                if item and item.text():
                    rd[var]=float(item.text())
                else:
                    widget=self.pdfa_table.cellWidget(row,col)
                    if isinstance(widget,QComboBox):
                        text=widget.currentText()
                        if var=='mat':
                            # rd[var]=int(text)
                            mat=text
                        else:
                            rd[var]=int(widget.currentText().split(' - ')[0])

            dmg['mats'][mat]=rd

        dmg['nmat']=len(dmg['mats'].keys())
        if dmg.get('mats'):
            self.mac['pdfa']=dmg

        #Output
        self.mac['print']['npl']=int(self.npl_cb.currentText().split(' - ')[0].replace(' ',''))
        self.mac['print']['vflev'] = int(self.vflev_text.text())

        if self.hdf5_chk.isChecked():
            self.mac['hdf5']['maxlev']= int(self.maxlev_text.text())
            self.mac['hdf5']['popt1']= int(self.popt1_cb.currentText().split(' - ')[0])
            self.mac['hdf5']['popt2']= int(self.popt2_cb.currentText().split(' - ')[0])

        if self.matlab_chk.isChecked():
            self.mac['matlab']['p']= int(self.matlabp_cb.currentText().split(' - ')[0])
            self.mac['matlab']['v']= int(self.matlabv_cb.currentText().split(' - ')[0])
            self.mac['matlab']['times']= self.matlabt_text.text().replace(' ','').split(',')
            self.mac['matlab']['ntimes']=len(self.mac['matlab']['times'])

        if self.xyplot_cb.isChecked():
            self.mac['xy']['freq']= int(self.freq_text.text())
            self.mac['xy']['macro']={}
            self.mac['xy']['macro']['macro']=self.macro_table.rowCount()
            self.mac['xy']['macro']['results']={}
            for row in range(self.macro_table.rowCount()):
                self.mac['xy']['macro']['results'][str(row)]={}
                for col in range(self.macro_table.columnCount()):
                    var=self.macro_table.horizontalHeaderItem(col).text().lower()
                    item=self.macro_table.item(row,col).text()
                    if var!='name':
                        item=int(item)
                    self.mac['xy']['macro']['results'][str(row)][var]=item

            self.mac['xy']['micro']={}
            self.mac['xy']['micro']['micro']=self.micro_table.rowCount()
            self.mac['xy']['micro']['results']={}
            for row in range(self.micro_table.rowCount()):
                self.mac['xy']['micro']['results'][str(row)]={}
                for col in range(self.micro_table.columnCount()):
                    var=self.micro_table.horizontalHeaderItem(col).text().lower()
                    item=self.micro_table.item(row,col).text()
                    if var!='name':
                        item=int(item)
                    self.mac['xy']['micro']['results'][str(row)][var]=item

        #Solution
        if self.mech_cb.isChecked():
            self.mac['mech']['lop']=int(self.lop_cb.currentText())
            self.mac['mech']['blocks']=self._get_load_blks(self.mech_table)

        if self.mphys_cb.isChecked():
            self.mac['multiphysics']['lop']=int(self.mphys_lop_cb.currentText())
            self.mac['multiphysics']['blocks']=self._get_load_blks(self.mphys_table)

        if self.therm_cb.isChecked():
            tsdata=self._get_therm_solver_data(self.therm_table)
            self.mac['therm']['npt']=len(tsdata['ti'])
            self.mac['therm'].update(tsdata)

        if self.solv_cb.isChecked():
            tsdata=self._get_therm_solver_data(self.sol_table)
            self.mac['solver']['method']=int(self.solmethod_cb.currentText().split(' - ')[0])
            solopt=int(self.solopt_cb.currentText().split(' - ')[0])
            self.mac['solver']['opt']=solopt
            self.mac['solver']['npt']=len(tsdata['ti'])
            self.mac['solver'].update(tsdata)
            self.mac['solver']['stp']=self.mac['solver']['stp'][1:]
            self.mac['solver']['itmax']=int(self.itmax_text.text())
            self.mac['solver']['err']=float(self.err_text.text())
            self.mac['solver']['nleg']=int(self.nleg_text.text())
            self.mac['solver']['ninteg']=int(self.ninteg_text.text())

        if self.probtype_cb.currentText()=='Mechanical Solution Only':
            self.mac['probtype']['mech']=1
            self.mac['probtype']['vect']=0
        elif self.probtype_cb.currentText()=='Multiphysics Solution Only':
            self.mac['probtype']['mech']=0
            self.mac['probtype']['vect']=1
        elif self.probtype_cb.currentText()=='Coupled Mechanical and Multiphysics Solutions':
            self.mac['probtype']['mech']=1
            self.mac['probtype']['vect']=1

        #return to calling program.
        self.accept()

    def _get_load_blks(self,table):
        """
        Callback function get loading blocks from table

        Parameters:
            table (QTableWidget): input table

        Returns:
            mdata (dict): paramters obtained from table
        """

        blkmap={'11':0,'22':1,'33':2,'23':3,'13':4,'12':5}
        #extract data from table
        mdata={}
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                var=table.horizontalHeaderItem(col).text().lower()
                item=table.item(row,col)
                #widget is in col 0, used to set dict key
                if item:
                    if var=='time' or var=='mag':
                        val=float(item.text())
                    else:
                        try:
                            val=int(item.text())
                        except ValueError:
                            val=0
                    if blkmap[comp] not in mdata:
                        mdata[blkmap[comp]]={'ti':[],'mag':[],'mode':[]}

                    if var=='time':
                        mdata[blkmap[comp]]['ti'].append(val)
                    else:
                        mdata[blkmap[comp]][var].append(val)

                else:
                    widget=table.cellWidget(row,col)
                    if isinstance(widget,QComboBox):
                        comp=widget.currentText()

        for _,blk in mdata.items():
            sorted_data = sorted(zip(blk['ti'], blk['mag'], blk['mode']))
            time_sorted, mag_sorted, mode_sorted = zip(*sorted_data)
            blk['ti']=list(time_sorted)
            blk['mag']=list(mag_sorted)
            blk['mode']=list(mode_sorted)
            blk['mode']=blk['mode'][1:] #first value in mode should be 0 and removed
            blk['npt'] = len(blk['ti'])

        return mdata

    def _get_therm_solver_data(self,table):
        """
        Callback function get *THERM or *SOLVER data from input table

        Parameters:
            table (QTableWidget): input table

        Returns:
            mdata (dict): paramters obtained from table
        """

        #extract data from table
        mdata={}
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                var=table.horizontalHeaderItem(col).text().lower()
                item=table.item(row,col)
                try:
                    val=float(item.text())
                except ValueError:
                    val=0.0

                if var=='time':
                    var = 'ti'
                if var not in mdata:
                    mdata[var]=[]
                mdata[var].append(val)

        newdata=[]
        [newdata.append(val) for key,val in mdata.items()] #pylint: disable=W0106
        sorted_data = sorted(zip(*newdata))
        sorted_lists = list(map(list, zip(*sorted_data)))
        keys=list(mdata.keys())
        for i in range(len(mdata.keys())):
            mdata[keys[i]]=sorted_lists[i]

        return mdata


    def load_mac(self):
        """
        Callback function to load MAC data into UI

        Parameters:
            None.

        Returns:
            None.
        """

        self.ruc_go_back() #needed to fix viz when loading

        if self.mac.get('constit'):
            c=self.mac['constit']
            for key in c['mats'].keys():
                mat=c['mats'][key]
                if 'comments' in mat and mat['comments']:
                    com=mat['comments'][0]
                    name = self._get_name(com)
                    liststr=f"{mat['m']} - {name}"
                else:

                    liststr=f"{mat['m']} - UNKNOWN"

                self.constits[liststr] = c['mats'][str(mat['m'])]


                item = QListWidgetItem(liststr)
                self.mats_list.addItem(item)

            if c['nmats']>0:
                self.mats_list.setCurrentRow(0)
                liststr = self.mats_list.currentItem().text()
                c =  self.constits[liststr]
                cmod=c['cmod']
                if cmod==6:
                    self.constit_tables.setCurrentIndex(0)
                    self.cmod69_table.setColumnHidden(8, True) #D1
                    self.cmod69_table.setColumnHidden(9, True) #D2
                    self.cmod69_table.setColumnHidden(10, True) #D3
                elif cmod==9:
                    self.constit_tables.setCurrentIndex(0)
                elif cmod==14:
                    self.constit_tables.setCurrentIndex(1)

                self.cmod_cb.findText(str(cmod))

                if 'tref' in c:
                    self.tref_text.setText(f"{c['tref']}")

                self.constit_tempdep_chk()

        if self.mac.get('rucs_avail'):
            kw =self.mac['rucs_avail']
            for rucstr,ruc in kw.items():
                self._ruc_add_to_save(rucstr,ruc)

        if self.mac.get('rucs_used_tree'):
            self.rucs_used_tree = self.mac['rucs_used_tree']

        if self.mac.get('ruc'):
            kw=self.mac['ruc']
            #convert sm from indexed to actual material number
            vmapf = np.vectorize(self.mac['mat_map'].get)

            #loop through and add all rucs
            for key,ruc in kw['rucs'].items():
                if 'comments' in ruc and ruc['comments']:
                    com=ruc['comments'][0]
                    name = self._get_name(com)
                else:
                    name=f"RUC {ruc['msm']}"
                ruc['sm']=vmapf(ruc['sm'])
                if 'archid' not in ruc:
                    archid = "NA"
                else:
                    archid = ruc['archid']
                if 'archid' not in ruc or ruc['archid']!=99:
                    rucstr=(f"Name={name},MSM={ruc['msm']},MOD={ruc['mod']},"
                            f"ARCHID={archid},VF={ruc['vf']},F={ruc['f']},M={ruc['m']}")
                else:
                    rucstr=(f"Name={name},MSM={ruc['msm']},MOD={ruc['mod']},"
                           f"ARCHID={archid}")
                if not self.mac.get('rucs_avail'):
                    self._ruc_add_to_save(rucstr,ruc)

            #Set the ruc_tree QTreeWidget model hierarchy
            #must be after ruc['sm'] mapping for all rucs
            if self.ruc_list.item(0):
                if not self.rucs_used_tree:
                    ruc = self.mac['ruc']['rucs']['0']
                    self.rucs_used_tree =  {
                                id(ruc): self._get_ruc_tree_from_kw(
                                                    parent_id=None,
                                                    ruc_key="0",
                                                    ilvl=0,
                                                    branch=set())
                                            }
                self._set_ruc(self.rucs_used_tree)

        if self.mac.get('failsub'):
            kw=self.mac['failsub']
            self.fs_table.blockSignals(True)
            self.fs_table.setRowCount(0)
            hide_xc = True
            tempdep=False
            for _,fc in kw['mats'].items():
                [self.failsub_addrow() for i in range(fc['ncrit'])] #pylint: disable=W0106
                for _,crit in fc['crits'].items():
                    if crit['compr']=='DIF':
                        hide_xc = False
                    if 'temp' in crit:
                        tempdep=True
                        [self.failsub_addrow() for i in range(crit['ntemp']-1)] #pylint: disable=W0106

            if hide_xc:
                self.fs_table.setColumnHidden(10, True) #XC11
                self.fs_table.setColumnHidden(11, True) #XC22
                self.fs_table.setColumnHidden(12, True) #XC33

            self.fs_tempdep_chk.setChecked(tempdep)

            irow = 0
            temp_rows = {}
            for imat,fc in kw['mats'].items():
                temp_rows[imat] = {}
                for icrit,crit in fc['crits'].items():
                    temp_rows[imat][icrit]=[]
                    if 'temp' in crit:
                        irowoff = len(crit['temp'])
                    else:
                        irowoff = 1

                    for col in range(self.fs_table.columnCount()):
                        var=self.fs_table.horizontalHeaderItem(col).text().lower()
                        item=self.fs_table.item(irow,col)
                        widget=self.fs_table.cellWidget(irow,col)
                        if not widget:
                            if var in crit:
                                if isinstance(crit[var],list):
                                    irowstd = []
                                    for ioff in range(crit['ntemp']):
                                        item = QTableWidgetItem(str(crit[var][ioff]))
                                        self.fs_table.setItem(irow+ioff, col, item)
                                        irowstd.append(irow+ioff)
                                    if not temp_rows[imat][icrit]: #only store the first time
                                        temp_rows[imat][icrit]=irowstd

                                else:
                                    item = QTableWidgetItem(str(crit[var]))
                                    self.fs_table.setItem(irow, col, item)
                            else:
                                item = QTableWidgetItem("")
                                self.fs_table.setItem(irow, col, item)
                        else:
                            if col==1:
                                ind=widget.findText(str(fc['mat']))
                                widget.setCurrentIndex(ind)
                            else:
                                try:
                                    ind = self._get_combobox_ind(widget,f"{crit[var]}")
                                except KeyError:
                                    ind=0

                                if ind is not None or ind==0:
                                    widget.setCurrentIndex(ind)
                                else:
                                    print((f"Invalid entry ({crit[var]}) for *FAILURE_SUBCELL ",
                                            f"{var}. Resetting to 0 index."))
                                    widget.setCurrentIndex(0)
                    irow += irowoff

            # Loop back through table and update MAT, CRIT, ACTION,
            # NORM widget indices to match when using temperature-dependent props.
            # First row is block is correct.
            for _,fc in temp_rows.items():
                for _,crit in fc.items():
                    if not crit:
                        continue
                    i1row = crit[0]
                    for irow in crit[1:]:
                        for col in range(self.fs_table.columnCount()):
                            widget=self.fs_table.cellWidget(irow,col)
                            if widget:
                                ind = self.fs_table.cellWidget(i1row,col).currentIndex()
                                widget.setCurrentIndex(ind)

            self.fs_table.blockSignals(False)

        if self.mac.get('pdfa'):
            kw=self.mac['pdfa']
            self.pdfa_table.setRowCount(0)
            [self.pdfa_addrow() for i in range(kw['nmat'])] #pylint: disable=W0106
            for irow,(_,mat) in enumerate(kw['mats'].items()):
                for col in range(self.pdfa_table.columnCount()):
                    var=self.pdfa_table.horizontalHeaderItem(col).text().lower()
                    item=self.pdfa_table.item(irow,col)
                    widget=self.pdfa_table.cellWidget(irow,col)
                    if not widget:
                        if var in mat:
                            item = QTableWidgetItem(str(mat[var]))
                        else:
                            item = QTableWidgetItem("")
                        self.pdfa_table.setItem(irow, col, item)
                    else:
                        if col==0:
                            ind=widget.findText(str(fc['mat']))
                            widget.setCurrentIndex(ind)
                        else:
                            ind = self._get_combobox_ind(widget,f"{mat[var]}")
                            if ind is not None or ind==0:
                                widget.setCurrentIndex(ind)
                            else:
                                print((f"Invalid entry ({mat[var]}) for *PDFA ",
                                        f"{var}. Resetting to 0 index."))
                                widget.setCurrentIndex(0)

        if self.mac.get('hdf5'):
            kw=self.mac['hdf5']
            self.hdf5_chk.setChecked(True)
            self.h5_use()
            self.maxlev_text.setText(f"{kw['maxlev']}")
            ind = self._get_combobox_ind(self.popt1_cb,f"{kw['popt1']}")
            if ind is not None or ind==0:
                self.popt1_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['popt1']}) for *HDF5, POPT1. Resetting to 0.")
                kw['popt1']=0
                self.popt1_cb.setCurrentIndex(0)
            ind = self._get_combobox_ind(self.popt2_cb,f"{kw['popt2']}")
            if ind is not None or ind==0:
                self.popt2_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['popt1']}) for *HDF5, POPT2. Resetting to 0.")
                kw['popt2']=0
                self.popt2_cb.setCurrentIndex(0)

        if self.mac.get('xy'):
            kw=self.mac['xy']
            self.xyplot_cb.setChecked(True)
            self.xy_use()
            self.freq_text.setText(f"{kw['freq']}")
            self._set_xy_tables(self.macro_table,kw['macro']['results'],self.xy_addmac)
            self._set_xy_tables(self.micro_table,kw['micro']['results'],self.xy_addmic)

        if self.mac.get('matlab'):
            kw=self.mac['matlab']
            self.matlab_chk.setChecked(True)
            self.matlab_use()
            ind = self._get_combobox_ind(self.matlabp_cb,f"{kw['p']}")
            if ind is not None or ind==0:
                self.matlabp_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['p']}) for *MATLAB, P. Resetting to 0.")
                kw['p']=0
                self.matlabp_cb.setCurrentIndex(0)
            ind = self._get_combobox_ind(self.matlabv_cb,f"{kw['v']}")
            if ind is not None or ind==0:
                self.matlabv_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['v']}) for *MATLAB, V. Resetting to 0.")
                kw['v']=0
                self.matlabv_cb.setCurrentIndex(0)
            if 'times' in kw:
                if isinstance(kw['times'],list):
                    self.matlabt_text.setText(",".join(str(f) for f in kw['times']))
                else:
                    self.matlabt_text.setText(f"{kw['times']}")
            else:
                self.matlabt_text.setText("")

        if self.mac.get('print'):
            kw=self.mac['print']
            ind = self._get_combobox_ind(self.npl_cb,f"{kw['npl']}")
            if ind is not None or ind==0:
                self.npl_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['npl']}) for *PRINT, NPL. Resetting to 1.")
                kw['opt']=1
                self.npl_cb.setCurrentIndex(1)

            self.vflev_text.setText(f"{kw['vflev']}")

        if self.mac.get('mech'):
            kw=self.mac['mech']
            self.mech_cb.setChecked(True)
            self.mech_use()
            ind=self.lop_cb.findText(str(kw['lop']))
            self.lop_cb.setCurrentIndex(ind)
            kwmap={'comp':'comp','time':'ti','mag':'mag','mode':'mode',
                    'lop':{i: i-1 for i in range(1, 7)}}
            self._set_data_tables(self.mech_table,kw,kwmap,self.mech_add)

        if self.mac.get('multiphysics'):
            kw=self.mac['multiphysics']
            self.mphys_cb.setChecked(True)
            self.mphys_use()
            ind=self.mphys_lop_cb.findText(str(kw['lop']))
            self.mphys_lop_cb.setCurrentIndex(ind)
            kwmap={'comp':'comp','time':'ti','mag':'mag','mode':'mode',
                    'lop':{i: i-1 for i in range(1, 4)}}
            self._set_data_tables(self.mphys_table,kw,kwmap,self.mphys_add)

        if self.mac.get('therm'):
            kw=self.mac['therm']
            self.therm_cb.setChecked(True)
            self.therm_use()

            self.therm_table.setRowCount(0)
            [self.therm_add() for i in kw['ti']] #pylint: disable=W0106
            for i,time in enumerate(kw['ti']):
                item = QTableWidgetItem(f"{time}")
                self.therm_table.setItem(i, 0, item)
                item = QTableWidgetItem(f"{kw['temp'][i]}")
                self.therm_table.setItem(i, 1, item)

        if self.mac.get('solver'):
            kw=self.mac['solver']
            self.solv_cb.setChecked(True)
            self.solv_use()

            ind = self._get_combobox_ind(self.solmethod_cb,f"{kw['method']}")
            if ind is not None or ind==0:
                self.solmethod_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['method']}) for *SOLVER, METHOD. Resetting to 1.")
                kw['method']=1
                self.solmethod_cb.setCurrentIndex(0)

            ind = self._get_combobox_ind(self.solopt_cb,f"{kw['opt']}")
            if ind is not None or ind==0:
                self.solopt_cb.setCurrentIndex(ind)
            else:
                print(f"Invalid entry ({kw['opt']}) for *SOLVER, OPT. Resetting to 0.")
                kw['opt']=0
                self.solopt_cb.setCurrentIndex(0)

            self.err_text.setText(f"{kw['err']}")
            self.itmax_text.setText(f"{kw['itmax']}")
            self.ninteg_text.setText(f"{kw['ninteg']}")
            self.nleg_text.setText(f"{kw['nleg']}")

            self.sol_table.setRowCount(0)
            [self.solv_add() for i in kw['ti']] #pylint: disable=W0106
            for i,time in enumerate(kw['ti']):
                item = QTableWidgetItem(f"{time}")
                self.sol_table.setItem(i, 0, item)
                if i==0:
                    item = QTableWidgetItem("-")
                else:
                    try:
                        item = QTableWidgetItem(f"{kw['stp'][i-1]}")
                    except TypeError:
                        item = QTableWidgetItem(f"{kw['stp']}")
                self.sol_table.setItem(i, 1, item)


        if self.mac.get('probtype'):
            kw=self.mac['probtype']
            if kw['mech']==1 and kw['vect']==0:
                self.probtype_cb.setCurrentIndex(0)
            elif kw['mech']==0 and kw['vect']==1:
                self.probtype_cb.setCurrentIndex(1)
            elif kw['mech']==1 and kw['vect']==1:
                self.probtype_cb.setCurrentIndex(2)

        #TODO: implement mac loading - *EXTERNAL_SETTINGS
        if self.mac.get('ext'):
            pass

    def _get_ruc_tree(self):
        """
        Build a nested dict from self.ruc_tree QTreeWidget

        Parameters:
            None.

        Returns:
            ruc_tree (dict): nested dict of tree items keyed by ruc_id
        """

        def _build(item, parent_id=None, ilvl=0, branch=None):
            """
            Recursive function to build the ruc tree

            Parameters:
                item (QTreeWidgetItem): current item in tree
                parent_id (int): id of parent ruc
                ilvl (int): single integer used to define level
                branch (set): all ids visited in current branch
                              used to detect infinite recursion                

            Returns:
                dict: nested dict of tree items keyed by ruc_id
            """
            if branch is None:
                branch = set()

            ruc_id = int(item.text(2))

            if ruc_id in branch:
                return {
                    "id": ruc_id,
                    "parent": parent_id,
                    "ilvl": ilvl,
                    "cycle": True,
                    "children": {}
                }

            branch.add(ruc_id)

            children = {}
            for i in range(item.childCount()):
                child_item = item.child(i)
                children[int(child_item.text(2))] = _build(
                    child_item,
                    parent_id=ruc_id,
                    ilvl=ilvl + 1,
                    branch=branch.copy()
                )

            return {
                "id": ruc_id,
                "parent": parent_id,
                "ilvl": ilvl,
                "children": children
            }

        # build tree starting from top-level items
        ruc_tree = {}
        for i in range(self.ruc_tree.topLevelItemCount()):
            item = self.ruc_tree.topLevelItem(i)
            ruc_tree[int(item.text(2))] = _build(item, parent_id=None, ilvl=0)

        return ruc_tree


    def _get_ruc_tree_from_kw(self, parent_id, ruc_key, ilvl, branch=None):
        """
        Recursively generate tree of items used in self.ruc_tree based on keyword

        Parameters:
            parent_id (int): id of parent ruc
            ruc_key (str): ruc string within keywords
            ilvl (int): single integer used to define level
            branch (set): all ids visited in current branch, used to detect infinite recursion
        Returns:
            dict: a branch of the full self.ruc_used_tree        
        """

        if branch is None:
            branch = set()

        ruc = self.mac['ruc']['rucs'][ruc_key]
        ruc_id = id(ruc)

        # check for infinite recursion and stop if encounterd
        if ruc_id in branch:
            return {
                "id": ruc_id,
                "parent": parent_id,
                "ilvl": ilvl,
                "cycle": True,
                "children": {}
            }

        branch.add(ruc_id)

        mats = np.unique(ruc['sm'])
        msms = sorted((m for m in mats if m <= 0), reverse=True)

        children = {}

        for msm in msms:
            child_key = str(msm)

            if child_key not in self.mac['ruc']['rucs']:
                continue

            child_ruc = self.mac['ruc']['rucs'][child_key]
            child_id = id(child_ruc)

            children[child_id] = self._get_ruc_tree_from_kw(
                parent_id=ruc_id,
                ruc_key=child_key,
                ilvl=ilvl + 1,
                branch=branch.copy()
            )

        return {
            "id": ruc_id,
            "parent": parent_id,
            "ilvl": ilvl,
            "children": children
        }


    def _set_ruc(self,tree):
        """
        Function to set ruc tree when loading data

        Parameters:
            tree (dict): self.ruc_used_tree containing parent/child relationships
                         of RUCs used in the model
        Returns:
            None.
        """

        for ruc_id,node in tree.items():
            rucstr=next((k for k, v in self.rucstr.items() if v == ruc_id), None)
            items = self.ruc_list.findItems(rucstr, Qt.MatchExactly)
            row = self.ruc_list.row(items[0])
            self.ruc_list.clearSelection()
            self.ruc_list.setCurrentItem(items[0])
            self.ruc_list.item(row).setSelected(True)
            self.ruc_use()
            for _ in range(node['ilvl']):
                _,item=self._get_used_rucs(ruc_id)
                self.ruc_tree.setCurrentItem(item)
                self.ruc_addto_lowerlevel()

            if node.get('children'):
                self._set_ruc(node['children'])


    def _set_data_tables(self,table,kwdata,kwmap,add_func):
        """
        Function to set UI data tables (mech, therm, multiphysics)

        Parameters:
            table (QTableWidget): input table to query
            kwdata (dict): dict of NASMAT keyword that matches table
            kwmap (dict): map from NASMAT keyword to UI variable name
            add_func (def): definition used to add values to table

        Returns:
            None.
        """

        table.setRowCount(0)
        for iblk, blk in kwdata['blocks'].items():
            # --- add rows and capture their actual indices ---
            rows = [add_func() for _ in range(blk['npt'])]
            irow = -1
            for local_row, table_row in enumerate(rows):
                for col in range(table.columnCount()):
                    var = table.horizontalHeaderItem(col).text().lower()
                    widget = table.cellWidget(table_row, col)
                    if not widget:
                        key = kwmap[var]
                        if key == 'mode':
                            if local_row == 0:
                                item = QTableWidgetItem('-')
                            else:
                                item = QTableWidgetItem(str(blk[key][local_row - 1]))
                        else:
                            item = QTableWidgetItem(str(blk[key][local_row]))
                        table.setItem(table_row, col, item)
                    else:
                        if isinstance(widget, QComboBox):
                            if var == 'comp':
                                if kwdata['lop'] == 99:
                                    comp = int(iblk) + 1
                                    irow += 1
                                    ind = kwmap['lop'][comp]
                                else:
                                    ind = kwmap['lop'][kwdata['lop']]
                                widget.setCurrentIndex(ind)

        if 'lop' in kwdata.keys() and kwdata['lop']!=99:
            table.setColumnHidden(0,True)

    def _get_combobox_ind(self,cb,prefix):
        """
        Function to set UI data tables

        Parameters:
            cb (QComboBox): combobox to query
            prefix (str): string to query in cb

        Returns:
            int: index with matching prefix if found
        """
        for i in range(cb.count()):
            if cb.itemText(i).lstrip().startswith(prefix):
                return i
        return None

    def _set_xy_tables(self,table,kwdata,add_func):
        """
        Function to set UI XY plot tables

        Parameters:
            table (QTableWidget): input table to query
            kwdata (dict): dict of NASMAT keyword that matches table
            add_func (def): definition used to add values to table

        Returns:
            None.
        """

        table.setRowCount(0)
        [add_func() for i in range(len(kwdata))] #pylint: disable=W0106
        for i,res in kwdata.items():
            for col in range(table.columnCount()):
                var=table.horizontalHeaderItem(col).text().lower()
                item = QTableWidgetItem(f"{res[var]}")
                table.setItem(int(i), col, item)

    def _get_mats(self):
        """
        Returns material number strings from self.constits

        Parameters:
            None

        Returns:
            mats (list): material number strings
        """

        mats = [s.split(' - ')[0] for s in self.constits.keys()]
        return mats

    def _get_name(self,com):
        """
        Returns name from comments list

        Parameters:
            None

        Returns:
            name (str): name found from formatted comment string
        """

        name=com
        if com.startswith('#--'):
            name=com[3:]
        elif com.startswith('# --'):
            name=com[4:]
        elif com.startswith('#'):
            name=com[1:]

        return name


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = new_Dialog(defaults=True)
    status=w.exec()
    sys.exit()
