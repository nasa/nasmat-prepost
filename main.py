"""Primary python file for launching the NASMAT PrePost UI.""" #pylint: disable=C0302
import sys
import os
import tkinter as tk
import copy
import math
#import time
from tkinter import filedialog
import numpy as np

from PyQt5.QtWidgets import (QApplication,QMessageBox, # pylint: disable=E0611
                            QMainWindow,QWidget,QTreeWidgetItem,
                            QInputDialog,QLineEdit,QHeaderView)
from PyQt5.QtCore import QTimer,pyqtSlot # pylint: disable=E0611
from PyQt5.QtGui import QColor,QTextCursor,QTextCharFormat # pylint: disable=E0611
from PyQt5.uic import loadUi

from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter # pylint: disable=E0611
from vtkmodules.vtkIOImage import vtkPNGWriter # pylint: disable=E0611

from NASMAT_PrePost import NASMATPrePost
from mac_inp import mac_inp
from mac_out import mac_out
from NASMAT import NASMAT
from new_Dialog import new_Dialog
from plt_dialog import PltDialog
from color_Dialog import color_Dialog
from show_md import ShowMd
from hideshowmat_Dialog import HideShowMatDialog
from Edit_text_dialog import Edit_text_dialog
from geth5 import GetH5
from util.npp_settings import get_npp_settings,write_npp_settings
from util.get_default_vtk_settings import get_default_vtk_settings
from util.get_model_hierarchy import get_model_hierarchy
from util.stdout_stderr_handling import qt_excepthook
from util.stdout_stderr_handling import EmittingStream

class Main(QMainWindow): #pylint: disable=R0902,R0904
    """The main window of the NASMAT PrePost UI."""

    def __init__(self):
        """
        Initialization routine called for the main class.

        Parameters:
            None.

        Returns:
            None.
        """

        super().__init__()
        loadUi("ui/NASMAT_PrePost.ui", self)

        self.version = 'NASMAT PrePost v1.0'
        self.setWindowTitle(self.version)

        sys.excepthook = qt_excepthook
        sys.stdout=EmittingStream(parent=self,color=QColor("black"))
        sys.stdout.textWritten.connect(self._append_text)
        sys.stderr=EmittingStream(parent=self,color=QColor("red"))
        sys.stderr.textWritten.connect(self._append_text)

        self.colors={'background':[0.8, 0.88, 0.92],'colormap':0}

        npps=get_npp_settings()
        if not npps:
            npps['CLEAR_CMD']='TRUE'
            npps['COLORMAP']=0
            npps['BACKGROUND_COLOR']=[0.8,0.88,0.92]

            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

        npp=NASMATPrePost()
        npp.set('npp_settings',npps)


        self.runkeys=['NASMAT_SOLVER','NASMAT_SHARED_PATH','INTEL_PATH','INTEL_OPTS','HDF5_PATH']
        if all(key in npps for key in self.runkeys) and os.path.isfile(npps['NASMAT_SOLVER']):
            self.actionRun_NASMAT.setEnabled(True)

        vtk_widget=self.findChild(QWidget, "vtk_widget")

        if 'BACKGROUND_COLOR' in npps:
            vtk_widget.set_background_color(npps['BACKGROUND_COLOR'])

        root = tk.Tk()
        root.withdraw()

        for column in range(self.treeWidget.columnCount()):
            self.treeWidget.header().setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.treeWidget.header().setMinimumHeight(50)
        for column in range(self.treeWidget_Res.columnCount()):
            self.treeWidget_Res.header().setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.treeWidget_Res.header().setMinimumHeight(50)

        self.has_macroapi=False
        self.results_opened = False
        self.plot_h5=False
        self.set_h5_flags=[False,False,False]
        self.macroapi_keys=None
        self.ninc=None
        self.elem_to_deck=None
        self.selected_tree=None
        self.deck_map=None
        self.ruc_tree=None
        self.treeitems_by_id={}
        self.timer = QTimer(self)
        self.timer.setInterval(3000) #initial timer interval, 3000 ms
        self.timer.timeout.connect(self.plot_h5_play_inc)
        self.inc_mode = 1 #1 for increasing, -1 for decreasing
        self.update_fields = False

    def closeEvent(self,event): #pylint: disable=C0103
        """
        Callback function to handle closing the UI

        Parameters:
            event (QEvent): event to close UI

        Returns:
            None.
        """

        npp=NASMATPrePost()
        filestr = npp.get('cur_file')

        if not filestr:
            event.accept()
            return

        if self.actionSave_NASMAT_Deck.isEnabled():
            reply = QMessageBox.question(
                self,
                "File Saved?",
                "Do you want to save the file before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel)

            if reply == QMessageBox.Yes:
                if self.actionSave_NASMAT_Deck.isEnabled():
                    nasmat = npp.get('nasmat')
                    file = nasmat[filestr]['MACfileName']
                    if file == 'tmp.MAC':
                        self.save_as()
                    else:
                        self.save()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            reply = QMessageBox.question(
                self,
                "Close NASMAT PrePost?",
                "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    @pyqtSlot(str, QColor)
    def _append_text(self,text,color):
        """
        Helper function for appending stdout/stderr to UI

        Parameters:
            text (str): text to be written to UI
            color (QColor): text color 

        Returns:
            None.
        """

        if not self.displayed_txt:
            return

        sb = self.displayed_txt.verticalScrollBar()
        at_bottom = sb.value()==sb.maximum()

        cursor = self.displayed_txt.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.displayed_txt.setTextCursor(cursor)
        if at_bottom:
            sb.setValue(sb.maximum())

    def new_mac_file_w_def(self):
        """
        Callback function for defining a new MAC file with defaults.

        Parameters:
            None.

        Returns:
            None.
        """

        nd=new_Dialog(self,defaults=True)
        status=nd.exec()
        if status and nd.mac['ruc']:
            self.actionSave_NASMAT_Deck.setEnabled(True)
            self.actionSave_NASMAT_Deck_As.setEnabled(True)
            self._init_npp(mac=nd.mac)

    def new_mac_file(self):
        """
        Callback function for defining a new MAC file with no defaults set.

        Parameters:
            None.

        Returns:
            None.
        """

        nd=new_Dialog(self)
        status=nd.exec()
        if status and nd.mac['ruc']:
            self.actionSave_NASMAT_Deck.setEnabled(True)
            self.actionSave_NASMAT_Deck_As.setEnabled(True)
            self._init_npp(mac=nd.mac)

    def open_mac_file(self):
        """
        Callback function for opening an existing MAC file.

        Parameters:
            None.

        Returns:
            None.
        """

        filename = filedialog.askopenfilename(title="Select a *.MAC input file...",
                                              filetypes=[("MAC files","*.MAC;*.mac"),])
        if filename:
            self._init_npp(filename=filename,read_from_mac=True)
            self.actionOpen_NASMAT_H5_File.setEnabled(False)
            self.actionSave_NASMAT_Deck_As.setEnabled(True)
            #self.actionSave_NASMAT_Deck.setEnabled(True) #for testing only

    def open_h5_file(self):
        """
        Callback function for opening an existing NASMAT h5 file.

        Parameters:
            None.

        Returns:
            None.
        """

        filename = filedialog.askopenfilename(title="Select a NASMAT *.h5 output file...",
                                              filetypes=[("NASMAT H5 files","*.h5"),])
        if filename:
            self._init_npp(filename=filename,read_from_h5=True)
            self.mode_cb.setEnabled(True)
            self.treeWidget_Res.blockSignals(True)
            self.treeWidget_Res.clearSelection()
            self.treeWidget_Res.blockSignals(False)
            self.results_opened = True
            ind=self.mode_cb.findText('H5 Arrays')
            # self.ninc=inp['h5'].ninc

            #block signals to prevent multiple callback calls
            self.tabWidget.blockSignals(True)
            self.treeWidget.blockSignals(True)
            self.res_comp_cb.blockSignals(True) #do not block mode, other values need to be set...
            self._update_hierarchy(update_res=False)
            self._update_hierarchy(update_res=True)
            self.mode_cb.setCurrentIndex(ind)
            self.actionAttach_h5_file.setEnabled(False)

            self.res_comp_cb.blockSignals(False)
            self.treeWidget.blockSignals(False)
            self.tabWidget.blockSignals(False)

            self.time_text.setText('0.0')
            self.inc_text.blockSignals(True)
            self.inc_text.setText('1')
            self.inc_text.blockSignals(False)

            self.actionSave_Video.setEnabled(True)

    def save(self):
        """
        Callback function for saving an existing or new MAC file.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr=npp.get('cur_file')
        curfilename=nasmat[filestr]['MACfileName']
        save_file = True
        if os.path.exists(curfilename):
            result = QMessageBox.question(self,"Question",
                    "Are you sure you want to overwrite the existing file?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)
            if result != QMessageBox.Yes:
                self.save_as()
                save_file = False #already saved

        if save_file:
            mackw=nasmat[filestr]['input']['0']
            mac_out(mackw,name=curfilename)


    def save_as(self):
        """
        Callback function for saving a new MAC file.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr=npp.get('cur_file')
        curfilename=nasmat[filestr]['MACfileName']
        filename = filedialog.asksaveasfilename(title="Save As...",
                defaultextension=".MAC",
                filetypes=[("MAC files", "*.MAC;*.mac")],
                initialfile=os.path.basename(curfilename))
        if filename:
            mackw=nasmat[filestr]['input']['0']
            self.setWindowTitle(self.version+f" - {filename}")
            filenums = [int(i) for i in nasmat]
            newfile = str(filenums[-1]+1)
            nasmat[newfile] = copy.deepcopy(nasmat[filestr])
            nasmat[newfile]['MACfileName'] = filename
            npp.set('cur_file',newfile)
            npp.set('nasmat',nasmat)
            mac_out(mackw,name=filename)

    def save_screenshot(self):
        """
        Callback function for saving a screenshot of the current plot.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr=npp.get('cur_file')
        filename=nasmat[filestr]['MACfileName']
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')

        vtk_widget=self.findChild(QWidget, "vtk_widget")

        img_filter = vtkWindowToImageFilter()
        img_filter.SetInput(vtk_widget.render_window)
        img_filter.Update()
        img_writer = vtkPNGWriter()
        if vs[id(ci)]['show_res']:
            var=vs[id(ci)]['var']
            comp=vs[id(ci)]['comp']
            default_text=filename[:-4]+f"-plot-{var}{comp}.png"
        else:
            default_text=filename[:-4]+'-plot-mats.png'

        text, valid = QInputDialog.getText(self, 'Updating Variable Plot Range',
                                           'Define the output file name:',
                                           QLineEdit.Normal, default_text)

        if text and valid:
            img_writer.SetFileName(text)
            img_writer.SetInputConnection(img_filter.GetOutputPort())
            img_writer.Write()
            print(f"screenshot saved to: {text}")

        npp.set('vtk_settings',vs)

    def save_video(self):
        """
        Callback function for saving a video of the current object.

        Parameters:
            None.

        Returns:
            None.
        """

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        user_input,ok_pressed = QInputDialog.getText(self,"Output Video FPS",
                                    "Enter the desired output video FPS:",
                                    text=str(int(3*self.ninc/10)))
        if ok_pressed:
            try:
                vs[id(ci)]['video_fps']=int(user_input)
            except ValueError:
                vs[id(ci)]['video_fps']=int(3*self.ninc/10)
        else:
            vs[id(ci)]['video_fps']=int(3*self.ninc/10)

        txt = ci.text(0).split(' - ')[-1].split(',')[-1].split(':')[1]
        default_txt = 'RUCID'+f"-{txt}-{vs[id(ci)]['var']}{vs[id(ci)]['comp']}.mp4"
        filename = filedialog.asksaveasfilename(title="Save Video As...",
        defaultextension=".mp4",
        filetypes=[("Video files", "*.mp4")],
        initialfile=default_txt)
        if filename:
            vs[id(ci)]['video_outfile'] = filename
        else:
            vs[id(ci)]['video_outfile']=default_txt

        ind = vs[id(ci)]['ind'] #get current ind for later
        npp.set('vtk_settings',vs)
        vtk_widget.update(sweep=(0,self.ninc))

        #reset view to increment when entered
        vs[id(ci)]['ind'] = ind
        npp.set('vtk_settings',vs)
        vtk_widget.update()


    def _init_npp(self,filename='tmp.MAC',read_from_mac=False,read_from_h5=False,mac=None):
        """
        Primary function initializing NASMAT PrePost based on user input.

        Parameters:
            filename (str): MAC file name (new or existing)
            read_from_mac (bool): flag to read from MAC input file
            read_from_h5 (bool): flag to read from NASMAT h5 file
            mac (dict): existing mac dict containing NASMAT keywords and values
        Returns:
            None.
        """

        if read_from_mac and read_from_h5:
            raise ValueError('Both read_from_mac and read_from_h5 cannot both be true.')
        if not read_from_mac and not read_from_h5 and not mac:
            raise ValueError('mac dict must be supplied when read logicals are both false.')

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')

        if not nasmat:
            nkeys = len(nasmat.keys())
            filestr=f"{nkeys+1}"
            npp.set('cur_file',filestr)
            nasmat[filestr] = {}
            nasmat[filestr]['MACfileName'] = filename
            nasmat[filestr]['settings'] = {}
            nasmat[filestr]['hide_mat']=[]
            nasmat[filestr]['input']={}
            nasmat[filestr]['output']={}
            nasmat[filestr]['ruc_plot']=''
        else:
            filestr = npp.get('cur_file')

        npp.set('cur_deck','')

        if mac is None:
            mac = {}
        else:
            nasmat[filestr]['input']['0']=mac

        self.actionAttach_h5_file.setEnabled(True)
        self.actionShowHide_Materials.setEnabled(True)
        self.actionSave_Screenshot.setEnabled(True)
        self.setWindowTitle(self.version+f" - {filename}")

        npps = get_npp_settings()
        npp.set('npp_settings',npps)
        npp.set('nasmat',nasmat)
        update_res=False

        if read_from_mac or mac:
            if read_from_mac:
                self._read_mac()
            self.menuEdit_NASMAT_Deck.setEnabled(True)
            self.actionEdit_UI.setEnabled(True)
            if 'raw_input' in nasmat[filestr]['input']['0'].keys():
                self.actionEdit_text.setEnabled(True)
            update_res=False

        if read_from_h5:
            self.menuEdit_NASMAT_Deck.setEnabled(False)
            self.actionEdit_UI.setEnabled(False)
            self.actionEdit_text.setEnabled(False)
            mi=GetH5(h5name=filename)
            nasmat[filestr]['input'] = mi.setup_mac()
            nasmat[filestr]['input']['h5']=mi
            self.ninc=mi.ninc

            if mi.has_macroapi:
                self.has_macroapi=True
                npp.set('macroapi',self.has_macroapi)
                self.macroapi_keys=list(mi.file['NASMAT Data'].keys())
                self.elem_to_deck=mi.elem_to_deck

                def get_sort_key(s):
                    parts = s.split(",")
                    elem = int(parts[0].strip().split(":")[1])
                    ip = int(parts[1].strip().split(":")[1])
                    return elem, ip

                self.macroapi_keys = sorted(self.macroapi_keys, key=get_sort_key)

            update_res=True

        self.plot_h5=False
        self.set_h5_flags=[False,False,False]#mode,item,comp

        if nasmat[filestr]['input']['0']['ruc']['nrucs'] > 0:
            self._update_hierarchy(update_res=update_res)
        # self._update_vtk()


    def _update_hierarchy(self,update_res=False):
        """
        Function to update NASMAT model hierarchy for UI.

        Parameters:
            update_res (bool): flag to update hierarchy based on results (all RUCs in the model)

        Returns:
            None.
        """

        self.tabWidget.setEnabled(True)
        if update_res:
            self.treeWidget_Res.clear()
            self.selected_tree=self.treeWidget_Res
            self.treeWidget_Res.blockSignals(True)
            self._set_model_hierachy(False)
            self.treeWidget_Res.setCurrentItem(self.treeWidget_Res.topLevelItem(0))
            self.treeWidget_Res.blockSignals(False)
            self.tabWidget.setCurrentIndex(1)
        else:
            self.treeWidget.clear()
            self.treeWidget.blockSignals(True)
            self.selected_tree=self.treeWidget
            self._set_model_hierachy(True)
            self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
            self.treeWidget.blockSignals(False)
            self.tabWidget.setCurrentIndex(0)


    def _read_mac(self):
        """
        Function for reading a MAC file.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr = npp.get('cur_file')
        mi = mac_inp(name=nasmat[filestr]['MACfileName'],echo=False)
        nasmat[filestr]['input']={}
        nasmat[filestr]['input']['0'] = mi.mac #deck hard-wired to be 0 only
        npp.set('nasmat',nasmat)

    def displayed_materials(self):
        """
        Callback function for showing/hiding materials in UI.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        file = npp.get('cur_file')
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        #cur_plot =  self.selected_tree.currentItem().text(0)

        #Get materials from all subvolumes
        rucs=nasmat[file]['input']['0']['ruc']['rucs']
        all_mats=np.concatenate([rucs[key]['sm'].flatten() for key in rucs.keys()])
        all_mats=np.unique(all_mats.astype(int))
        all_mats=np.vectorize(vs[id(ci)]['map'].get)(all_mats).tolist()
        all_mats=[str(i) for i in all_mats]

        dialog = HideShowMatDialog(self)


        if nasmat[file]['hide_mat']:
            hide_mat=[str(vs[id(ci)]['map'][i]) for i in nasmat[file]['hide_mat']]
            show_mat=list(set(all_mats).difference(hide_mat))
            dialog.showlistWidget.insertItems(0,show_mat)
            dialog.showlistWidget.sortItems()
            dialog.hidelistWidget.insertItems(0,hide_mat)
            dialog.hidelistWidget.sortItems()
        else:
            dialog.showlistWidget.insertItems(0,all_mats)
            dialog.showlistWidget.sortItems()

        status=dialog.exec()
        if not status:
            return
        hide_mat=[vs[id(ci)]['revmap'][int(i)] for i in dialog.get_hide_items()]
        nasmat[file]['hide_mat']=hide_mat

        npp.set('nasmat',nasmat)
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def show_hide_title(self):
        """
        Callback function to show/hide the wtk_widget title text

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['show_title'] = not vs[id(ci)]['show_title']

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def show_hide_axes(self):
        """
        Callback function to show/hide the plot axes

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['show_axes'] = not vs[id(ci)]['show_axes']

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def show_hide_mat_ids(self):
        """
        Callback function to show/hide material ids.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['show_mats'] = not vs[id(ci)]['show_mats']
        if vs[id(ci)]['show_mats']:
            vs[id(ci)]['opacity']=0.8
        else:
            vs[id(ci)]['opacity']=1.0

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def show_all_ori(self):
        """
        Callback function to show all material orientations.

        Parameters:
            None.

        Returns:
            None.
        """

        self._update_orientations(flags=[True,True,True])

    def hide_all_ori(self):
        """
        Callback function to hide all material orientations.

        Parameters:
            None.

        Returns:
            None.
        """

        self._update_orientations(flags=[False,False,False])

    def show_1dir_ori(self):
        """
        Callback function to show only 1-direction orientation

        Parameters:
            None.

        Returns:
            None.
        """

        self._update_orientations(flags=[True,False,False])

    def _update_orientations(self,flags):
        """
        Callback function to show only 1-direction orientation

        Parameters:
            flags (list): 3 bools for setting orientations

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')

        vs[id(ci)]['show_ori'][0] = flags[0]
        vs[id(ci)]['show_ori'][1] = flags[1]
        vs[id(ci)]['show_ori'][2] = flags[2]

        if any(vs[id(ci)]['show_ori']):
            vs[id(ci)]['opacity']=0.8
            selected,_,_ = self.get_selected()
            msm=selected.split(',')[0].split('M=')[1]
            nasmat = npp.get('nasmat')
            file = npp.get('cur_file')
            rucs=nasmat[file]['input']['0']['ruc']['rucs']
            ruc=rucs[msm]
            if not vs[id(ci)]['ori_scale']:
                scale=np.linalg.norm([np.average(ruc['d']),np.average(ruc['h']),
                                        np.average(ruc['l'])])
                vs[id(ci)]['ori_scale']=scale*0.2

        else:
            vs[id(ci)]['opacity']=1.0

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            vs=npp.get('vtk_settings')
            vs[id(npp.get('selected'))]=vs[id(ci)]
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def set_ori_scale_factor(self):
        """
        Callback function to set the orientation arrow scale factor.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        text, valid = QInputDialog.getText(self, 'Updating Orientation Arrow Scale Factor',
                                           'Enter a number to scale the orientations by:')
        if text and valid and vtk_widget:
            vs[id(ci)]['ori_scale'] = float(text)
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def set_opacity(self):
        """
        Callback function to set the grid opacity

        Parameters:
            None

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        text, valid = QInputDialog.getText(self, 'Updating the Plot Opacity',
                                           'Enter a number to define the plot opacity [0,1]:',
                                           text=str(vs[id(ci)]['opacity']))
        if text and valid and vtk_widget:
            val = float(text)
            if val<0:
                val=0.0
            elif val>1.0:
                val=1.0
            vs[id(ci)]['opacity'] = val
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def show_hide_subvol_ids(self):
        """
        Callback function to show/hide subvolume ids.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['show_ids']=not vs[id(ci)]['show_ids']
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()



    def show_hide_subvol_edges(self):
        """
        Callback function to show/hide subvolume edges.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['show_subvol_edges']=not vs[id(ci)]['show_subvol_edges']
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def plot_change_range(self):
        """
        Callback function to change variable plot range.

        Parameters:
            None.

        Returns:
            None.
        """

        text, valid = QInputDialog.getText(self, 'Updating Variable Plot Range',
                                           'Enter a new min/max value separated by a comma:')
        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        if text and valid:
            vals=text.lstrip().rstrip().split(',')
            vs[id(ci)]['plot_range']=[float(val) for val in vals]
            vtk_widget=self.findChild(QWidget, "vtk_widget")
            if vtk_widget:
                npp.set('vtk_settings',vs)
                vtk_widget.update()

    def plot_reset_range(self):
        """
        Callback function to reset plot range.

        Parameters:
            None.

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        vs[id(ci)]['plot_range']=[]
        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            npp.set('vtk_settings',vs)
            vtk_widget.update()

    def set_default_vtk_settings(self,items):
        """
        Function to set default vtk settings.

        Parameters:
            items (list): QTreeWidgetItem objects that require vtk settings for plotting 

        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs = npp.get('vtk_settings')
        nasmat=npp.get('nasmat')
        filestr=npp.get('cur_file')
        npps = npp.get('npp_settings')
        #set initial default behavior
        for item in items:
            vs[id(item)]=get_default_vtk_settings()
            vs[id(item)]['PlotMode'] = 'Main'
            vs[id(item)]['map']=nasmat[filestr]['input']['0']['mat_map']
            vs[id(item)]['revmap']=nasmat[filestr]['input']['0']['rev_mat_map']
            if '2D RUC' in item.text(0): #hide axes by default for 2D plots
                vs[id(item)]['show_axes'] = False
            if hasattr(self,'colors'):
                vs[id(item)]['cmap']=self.colors['colormap']

            if 'SHOW_AXES' in npps and npps['SHOW_AXES'].upper()=='FALSE':
                vs[id(item)]['show_axes']=False
            elif 'SHOW_AXES' in npps and npps['SHOW_AXES'].upper()=='TRUE':
                vs[id(item)]['show_axes']=True
            if 'SHOW_TITLE' in npps and npps['SHOW_TITLE'].upper()=='FALSE':
                vs[id(item)]['show_title']=False
            elif 'SHOW_TITLE' in npps and npps['SHOW_TITLE'].upper()=='TRUE':
                vs[id(item)]['show_title']=True

        npp.set('vtk_settings',vs)

    def _set_model_hierachy(self,mode):
        """
        Function to set model hierarchy in UI.

        Parameters:
            mode (bool): flag defining hiearhy structure 
                            True - shortenend keyword, no duplicate RUCs
                            False - full model, all RUCs

        Returns:
            None.
        """

        tree=self.selected_tree
        tree.setEnabled(True)
        tree.clear()

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        file = npp.get('cur_file')
        hierarchy=npp.get('hierarchy')

        parent=tree.invisibleRootItem()
        if mode:
            for deck in nasmat[file]['input'].keys():
                if deck=='h5' or deck=='rucid':
                    continue

                s=nasmat[file]['input'][deck]

                if self.has_macroapi:
                    parent = QTreeWidgetItem(parent, ['MacroAPI Mesh', ''])
                hrchy,hrchy_items,hstr=get_model_hierarchy(s,mode)

                if self.has_macroapi:
                    if isinstance(hstr, dict):
                        old_key = next(iter(hstr))
                        new_key=s['name'] +' - '+ old_key
                        hstr[new_key] = hstr.pop(old_key)
                    elif isinstance(hstr, list):
                        new_str=s['name'] +' - '+ hstr[0]
                        hstr[0]=new_str
                    else: #hstr is a str
                        new_str=s['name'] +' - '+ hstr
                        hstr=new_str

                self._add_tree_item(parent,hstr,0,rid=s['ruc_map'])
        else:
            if self.has_macroapi:
                self.deck_map={}
                for deck in nasmat[file]['input'].keys():
                    if deck=='h5' or deck=='rucid':
                        continue
                    name=nasmat[file]['input'][deck]['name']
                    si=name.find('(')+1
                    ei=name.find(')')
                    self.deck_map[int(name[si:ei])-1]=name

                parent = QTreeWidgetItem(parent, ['MacroAPI Mesh', ''])
                for key in self.macroapi_keys:
                    elem=key.split(',')[0].split(':')[1]
                    decknum=self.elem_to_deck[elem]
                    deck=self.deck_map[decknum]
                    s=nasmat[file]['input'][str(decknum)]
                    maxlev=nasmat[file]['input']['h5'].maxlev

                    res_str=key + f" (deck:{decknum})"
                    hrchy,hrchy_items,hstr=get_model_hierarchy(s,mode,maxlev)
                    hierarchy['res'][res_str]={}
                    hierarchy['res'][res_str]['hierarchy']=hrchy
                    hierarchy['res'][res_str]['items']=hrchy_items

                    if isinstance(hstr, dict):
                        old_key = next(iter(hstr))
                        new_key=res_str +' - '+ old_key
                        hstr[new_key] = hstr.pop(old_key)
                    elif isinstance(hstr, list):
                        new_str=res_str +' - '+ hstr[0]
                        hstr[0]=new_str
                    else: #hstr is a str
                        new_str=res_str +' - '+ hstr
                        hstr=new_str
                    self._add_tree_item(parent,hstr,0)
            else:
                deck=list(nasmat[file]['input'].keys())[0]
                s=nasmat[file]['input'][deck]
                if 'h5' in nasmat[file]['input'].keys():
                    maxlev=nasmat[file]['input']['h5'].maxlev
                else:
                    maxlev=None
                hrchy,hrchy_items,hstr=get_model_hierarchy(s,mode,maxlev)
                hierarchy['res']['hierarchy']=hrchy
                hierarchy['res']['items']=hrchy_items
                self._add_tree_item(parent,hstr,0)
        npp.set('hierarchy',hierarchy)

    def _add_tree_item(self,parent,value,idnum,rid=None):
        """
        Function to add individual tree items to UI.

        Parameters:
            parent (QTreeWidgetItem): parent item where children will be added
            value (dict, list, or str): case-specific inputs for setting children
            idnum (int): id counter for objects
            rid (dict): optional rucid inputs, not currently used 
        Returns:
            None.
        """

        parent.setExpanded(True)
        if isinstance(value,dict):
            for key, val in value.items():
                child = QTreeWidgetItem()
                child.setText(0, key)
                if rid:
                    cols=key.split(',') #kept in for generality
                    c=cols[0].split('=')
                    child.setText(1,rid[c[1]])

                idnum+=1
                self.set_default_vtk_settings([child])
                parent.addChild(child)
                self.treeitems_by_id[id(child)]=child
                idnum=self._add_tree_item(child, val, idnum, rid=rid)
        elif isinstance(value,list):
            for val in value:
                if isinstance(val,dict):
                    idnum=self._add_tree_item(parent, val, idnum, rid=rid)
                elif isinstance(val,str):
                    child = QTreeWidgetItem()
                    child.setText(0, val)
                    if rid:
                        cols=val.split(',') #kept in for generality
                        c=cols[0].split('=')
                        child.setText(1,rid[c[1]])

                    idnum+=1
                    self.set_default_vtk_settings([child])
                    parent.addChild(child)
                    self.treeitems_by_id[id(child)]=child
        elif isinstance(value,str):
            child = QTreeWidgetItem()
            child.setText(0, value)
            if rid:
                cols=value.split(',') #kept in for generality
                c=cols[0].split('=')
                child.setText(1,rid[c[1]])
            idnum+=1
            self.set_default_vtk_settings([child])
            parent.addChild(child)
            self.treeitems_by_id[id(child)]=child

        return idnum

    def change_ruc_tab(self):
        """
        Callback function to change RUC tab in UI.

        Parameters:
            None. 

        Returns:
            None.
        """

        npp=NASMATPrePost()
        tabindex=self.tabWidget.currentIndex()
        if tabindex==0:
            self.actionSave_Video.setEnabled(False)
            self.selected_tree=self.treeWidget
            ind=self.mode_cb.findText('Materials')
            self.mode_cb.setCurrentIndex(ind)
        elif tabindex==1:
            self.actionSave_Video.setEnabled(True)
            self.selected_tree=self.treeWidget_Res
            res = npp.get('cur_result')
            field_ind = res['field']
            comp_ind = res['comp']
            mode_ind = res['mode']
            ind=self.mode_cb.findText('H5 Arrays')
            self.mode_cb.setCurrentIndex(ind)
            self.res_item_cb.setCurrentIndex(field_ind)
            self.res_comp_cb.setCurrentIndex(comp_ind)
            self.res_mode_cb.setCurrentIndex(mode_ind)

        self.selected_tree.setCurrentItem(npp.get('selected'))

    def select_solver(self):
        """
        Callback function to select NASMAT solver (executable).

        Parameters:
            None. 

        Returns:
            None.
        """

        solver_name = filedialog.askopenfilename(title="Select a NASMAT executable...")
        if solver_name:
            npp=NASMATPrePost()
            npps=npp.get('npp_settings')
            npps['NASMAT_SOLVER']=solver_name
            npp.set('npp_settings',npps)
            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

            if all(key in npps for key in self.runkeys):
                self.actionRun_NASMAT.setEnabled(True)

    def set_nasmat_shared_path(self):
        """
        Callback function to set NASMAT shared library path.

        Parameters:
            None. 

        Returns:
            None.
        """
        path = filedialog.askdirectory(title="Select the NASMAT shared library directory...")
        if path:
            npp=NASMATPrePost()
            npps=npp.get('npp_settings')
            npps['NASMAT_SHARED_PATH']=path
            npp.set('npp_settings',npps)

            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

            if all(key in npps for key in self.runkeys):
                self.actionRun_NASMAT.setEnabled(True)

    def set_intel_path(self):
        """
        Callback function to set Intel path to setvars.bat.

        Parameters:
            None. 

        Returns:
            None.
        """
        name = filedialog.askopenfilename(title="Select the Intel setvars script...")
        if name:
            npp=NASMATPrePost()
            npps=npp.get('npp_settings')
            npps['INTEL_PATH']=name
            npp.set('npp_settings',npps)

            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

            if all(key in npps for key in self.runkeys):
                self.actionRun_NASMAT.setEnabled(True)

    def set_intel_opts(self):
        """
        Callback function to set Intel command line options.

        Parameters:
            None. 

        Returns:
            None.
        """
        default = 'intel64 vs2022'
        user_input,ok_pressed = QInputDialog.getText(self,"Input",
                                    "Enter any options to pass with Intel setvars script:",
                                    text=default)
        if ok_pressed:
            npp=NASMATPrePost()
            npps=npp.get('npp_settings')
            npps['INTEL_OPTS']=user_input
            npp.set('npp_settings',npps)

            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

            if all(key in npps for key in self.runkeys):
                self.actionRun_NASMAT.setEnabled(True)

    def set_h5_path(self):
        """
        Callback function to set HDF5 bin path.

        Parameters:
            None. 

        Returns:
            None.
        """
        path = filedialog.askdirectory(title="Select the HDF5 bin directory...")
        if path:
            npp=NASMATPrePost()
            npps=npp.get('npp_settings')
            npps['HDF5_PATH']=path
            npp.set('npp_settings',npps)

            write_npp_settings(npp_settings=npps,env_file=os.path.join('.','NASMATPrePost.env'))

            if all(key in npps for key in self.runkeys):
                self.actionRun_NASMAT.setEnabled(True)


    def run_nasmat(self):
        """
        Callback function to run NASMAT.

        Parameters:
            None. 

        Returns:
            None.
        """

        npp=NASMATPrePost()
        env = npp.get('env')
        npps = npp.get('npp_settings')

        if env is None: #Update PATH variable first time only
            current_env = os.environ.copy()
            if 'CLEAR_CMD' in npps and npps['CLEAR_CMD'].upper().startswith('T'):
                current_env ={"PATH":''}

            h5p = npps["HDF5_PATH"]
            h5p = h5p if h5p.endswith(';') else h5p + ';'

            new_path =  h5p + current_env["PATH"] #Windows convention
            current_env["PATH"]=new_path

            if 'NASMAT_SHARED_PATH' in npps:
                ndll = npps['NASMAT_SHARED_PATH']
                ndll = ndll if ndll.endswith(';') else ndll + ';'
                new_path =  ndll + current_env["PATH"] #Windows convention
                current_env["PATH"]=new_path

            npp.set('env',current_env)

        nasmat = npp.get('nasmat')
        mac=nasmat[npp.get('cur_file')]['MACfileName']

        if mac.lower().endswith('.h5'):
            print('WARNING: h5 files not able to be run from NASMAT. Create an input file first.')
            return

        nm_exe=NASMAT(npps['NASMAT_SOLVER'],npps["HDF5_PATH"],npps['INTEL_PATH'],
                            npps['INTEL_OPTS'])
        nm_exe.run(mac=mac)


    def attach_h5(self):
        """
        Callback function to attach an h5 file to an opened MAC file.

        Parameters:
            None. 

        Returns:
            None.
        """

        filename = filedialog.askopenfilename(title="Select a NASMAT *.h5 output file...",
                                              filetypes=[("NASMAT H5 files","*.h5"),])
        if filename:
            npp=NASMATPrePost()
            nasmat = npp.get('nasmat')
            macfile = npp.get('cur_file')
            inp=nasmat[macfile]['input']
            inp['h5']=GetH5(h5name=filename)
            mac_tmp= inp['h5'].setup_mac()
            nasmat[macfile]['input']['0']['rucid']=mac_tmp['rucid']
            npp.set('nasmat',nasmat)
            self.results_opened = True
            self.mode_cb.setEnabled(True)
            self.ninc=inp['h5'].ninc
            self._update_hierarchy(update_res=True)
            self.treeWidget.setCurrentItem(npp.get('selected'))
            ind = self.res_item_cb.findText("Stress")
            if ind==-1:
                ind = 0
            self.res_item_cb.setCurrentIndex(ind)
            self.res_comp_cb.setCurrentIndex(0)

    def view_data_files(self):
        """
        Callback function to view NASMAT *.data file results.

        Parameters:
            None. 

        Returns:
            None.
        """

        npp=NASMATPrePost()
        xy = npp.get("xy_plots")

        if not xy:
            v=PltDialog()
        else:
            v=PltDialog(input_data=xy['data'],opts=xy['opts'],tooltips=xy['tooltips'])

        status=v.exec()
        if status:
            xyn = {'data':v.data, 'opts':{'plot':v.plotopts,'chart':v.chartopts},
                    'tooltips':v.tooltips}
            npp.set("xy_plots",xyn)

    def select_h5_results(self):
        """
        Callback function to select results based on mode_cb Combo Box in UI.

        Parameters:
            None. 

        Returns:
            None.
        """

        if not self.results_opened:
            return

        selected = self.mode_cb.currentText()
        self.res_item_cb.setEnabled(False)
        self.res_comp_cb.setEnabled(False)
        self.res_mode_cb.setEnabled(False)
        self.firstinc_pb.setEnabled(False)
        self.previnc_pb.setEnabled(False)
        self.nextinc_pb.setEnabled(False)
        self.lastinc_pb.setEnabled(False)
        self.stop_pb.setEnabled(False)
        self.auto_chk.setEnabled(False)
        self.speed_slider.setEnabled(False)
        self.inc_text.setEnabled(False)

        # self.res_item_cb.clear()
        self.res_comp_cb.clear()
        #Note: since a triggered signal is used for each of the result
        #      comboboxes, only one vtk update should be called once
        #      the four comboboxes are set.
        self.set_h5_flags=[False,False,False,False]#mode,item,comp,mode
        if selected == 'H5 Arrays':
            self.res_item_cb.setEnabled(True)
            npp=NASMATPrePost()
            nasmat = npp.get('nasmat')
            macfile = npp.get('cur_file')
            h5=nasmat[macfile]['input']['h5']

            selected,_,_=self.get_selected()
            if selected.startswith('MacroAPI'):
                items=h5.get_h5_fields_api()
            else:
                items=h5.get_h5_fields()

            self.res_item_cb.addItems(items)
            self.res_comp_cb.setEnabled(True)
            self.res_mode_cb.setEnabled(True)
            self.firstinc_pb.setEnabled(True)
            self.previnc_pb.setEnabled(True)
            self.nextinc_pb.setEnabled(True)
            self.lastinc_pb.setEnabled(True)
            self.stop_pb.setEnabled(True)
            self.auto_chk.setEnabled(True)
            self.speed_slider.setEnabled(True)
            self.inc_text.setEnabled(True)

            self.res_mode_cb.setCurrentIndex(0)
            #default result to view
            ind = self.res_item_cb.findText("Stress")
            if ind==-1:
                ind = self.res_item_cb.findText("S") #macroapi
                if ind==-1: #failsafe
                    ind = 0
            self.res_item_cb.setCurrentIndex(ind)
            self.res_comp_cb.setCurrentIndex(0)
            self.set_h5_flags=[True,True,True,True]
            self.update_h5_plot()
        else:
            self.plot_ruc()

        if selected=='H5 Arrays':
            incstr='1'
            npp=NASMATPrePost()
            nasmat = npp.get('nasmat')
            macfile = npp.get('cur_file')
            inp=nasmat[macfile]['input']
            times=inp['h5'].h5_struct['times']
            timestr=f"{times[0]}"
            self.time_text.setText(timestr)
            self.inc_text.blockSignals(True)
            self.inc_text.setText(incstr)
            self.inc_text.blockSignals(False)

    def set_h5_item(self):
        """
        Callback function to set h5 flags for a result array.

        Parameters:
            None. 

        Returns:
            None.
        """

        if self.mode_cb.currentText()!='H5 Arrays':
            self.plot_ruc()
            return

        var=self.res_item_cb.currentText()
        self.set_h5_comp_items(var)

        self.set_h5_flags[1]=True
        self.set_h5_flags[2]=True
        self.update_h5_plot()

    def set_h5_comp(self):
        """
        Callback function to set h5 flags for a result array component.

        Parameters:
            None. 

        Returns:
            None.
        """

        if self.mode_cb.currentText()!='H5 Arrays':
            return
        self.set_h5_flags[2]=True
        self.update_h5_plot()

    def set_h5_mode(self):
        """
        Callback function to set h5 flags for a result array plot mode.

        Parameters:
            None. 

        Returns:
            None.
        """

        if self.mode_cb.currentText()!='H5 Arrays':
            return
        self.set_h5_flags[3]=True
        self.update_h5_plot()

    def set_h5_comp_items(self,var):
        """
        Function to set array components Combo Box based on array.

        Parameters:
            var (str): array name contained within h5 file 

        Returns:
            None.
        """

        self.res_comp_cb.blockSignals(True)
        self.res_comp_cb.clear()
        self.res_comp_cb.blockSignals(False)
        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        macfile = npp.get('cur_file')
        h5=nasmat[macfile]['input']['h5']
        var=self.res_item_cb.currentText()
        items=h5.get_components(var)
        self.res_comp_cb.addItems(items)
        self.res_comp_cb.setCurrentIndex(0)


    def plot_h5_goto_firstinc(self):
        """
        Callback function to go to first increment in data.

        Parameters:
            None. 

        Returns:
            None. Calling self.plot_h5_change_inc to update.
        """

        return self.plot_h5_change_inc(0)

    def plot_h5_goto_previnc(self):
        """
        Callback function to go to previous increment in data.

        Parameters:
            None. 

        Returns:
            None.
        """
        self.inc_mode = -1
        if self.auto_chk.isChecked():
            self.timer.start(self.timer.interval())
        else:
            self.plot_h5_change_inc(1)

    def plot_h5_goto_nextinc(self):
        """
        Callback function to go to next increment in data.

        Parameters:
            None. 

        Returns:
            None.
        """

        self.inc_mode = 1
        if self.auto_chk.isChecked():
            self.timer.start(self.timer.interval())
        else:
            self.plot_h5_change_inc(2)

    def plot_h5_goto_lastinc(self):
        """
        Callback function to go to last increment in data.

        Parameters:
            None. 

        Returns:
            None. Calling self.plot_h5_change_inc to update.
        """

        return self.plot_h5_change_inc(3)

    def plot_h5_set_inc(self):
        """
        Callback function to go to user-input increment in data.

        Parameters:
            None. 

        Returns:
            None. Calling self.plot_h5_change_inc to update.
        """

        return self.plot_h5_change_inc(4)

    def plot_h5_play_inc(self):
        """
        Callback function to automatically increment in data.

        Parameters:
            None. 

        Returns:
            None. 
        """

        if self.inc_mode>=0:
            self.plot_h5_change_inc(2) #increase increment by 1
        else:
            self.plot_h5_change_inc(1) #decrease increment by 1

    def plot_h5_update_speed(self,value):
        """
        Callback function to adjust speed of increments.

        Parameters:
            value (int): current value of the speed_slider QSlider 
                        assumes slider min=1, max=100

        Returns:
            None. 
        """

        fast = 50     # fastest (ms)
        slow = 3000   # slowest (ms)
        # reverses direction so that slider min = slow
        t = (value - 1) / 99
        interval = slow * math.exp(
            -math.log(slow/fast)*t)
        self.timer.setInterval(int(interval))

    def plot_h5_stop_inc(self):
        """
        Callback function to stop auto incrementing.

        Parameters:
            None. 

        Returns:
            None. 
        """

        self.timer.stop()

    def plot_h5_change_inc(self,iopt):
        """
        Function to set h5 increment and update UI.

        Parameters:
            iopt (int): Value to define data increment. 0-first, 
                                                        1-decrease by 1, 
                                                        2-increase by 1, 
                                                        3-last, 
                                                        4-user selected

        Returns:
            None.
        """

        update=True
        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        if iopt==0: #set to first increment
            if vs[id(ci)]['ind']!=0:
                vs[id(ci)]['ind']=0
            else:
                update=False
        elif iopt==1: #decrease increment by 1
            if vs[id(ci)]['ind']!=0:
                vs[id(ci)]['ind']-=1
            else:
                update=False
        elif iopt==2: #increase increment by 1
            if vs[id(ci)]['ind']!=self.ninc-1:
                vs[id(ci)]['ind']+=1
            else:
                update=False
        elif iopt==3: #set to last increment
            if vs[id(ci)]['ind']!=self.ninc-1:
                vs[id(ci)]['ind']=self.ninc-1
            else:
                update=False
        elif iopt==4: #increment manually chosen
            try:
                inc=int(self.inc_text.text())
            except ValueError:
                inc=None

            if inc and inc<1:
                vs[id(ci)]['ind']=0
                self.inc_text.blockSignals(True)
                self.inc_text.setText("1")
                self.inc_text.blockSignals(False)
                QMessageBox.warning(None,"Warning",
                    f"Enter an integer value between 1 and {self.ninc}.")
            elif inc and inc>self.ninc:
                vs[id(ci)]['ind']=self.ninc-1
                self.inc_text.blockSignals(True)
                self.inc_text.setText(f"{self.ninc}")
                self.inc_text.blockSignals(False)
                QMessageBox.warning(None,"Warning",
                    f"Enter an integer value between 1 and {self.ninc}.")
            elif inc and 1<=inc<=self.ninc:
                vs[id(ci)]['ind']=inc-1
            else:
                update=False

        npp.set('vtk_settings',vs)


        if update:
            nasmat = npp.get('nasmat')
            macfile = npp.get('cur_file')
            inp=nasmat[macfile]['input']
            times=inp['h5'].h5_struct['times']
            timestr=f"{times[vs[id(ci)]['ind']]}"
            incstr=f"{vs[id(ci)]['ind']+1}"
            self.inc_text.blockSignals(True)
            self.inc_text.setText(incstr)
            self.inc_text.blockSignals(False)
            self.time_text.setText(timestr)
            self.update_h5_plot()
        else:
            self.timer.stop()

    def update_h5_plot(self):
        """
        Callback function to update plot based on selection in treeWidget_Res.

        Parameters:
            None. 

        Returns:
            None.
        """

        self.plot_h5=False
        if all(self.set_h5_flags):
            self.plot_h5=True
            self.plot_h5_results()

    def plot_h5_results(self):
        """
        Function to plot new results.

        Parameters:
            None. 

        Returns:
            None.
        """
        npp=NASMATPrePost()
        res=npp.get('cur_result')
        res['field']=self.res_item_cb.currentIndex()
        res['comp']=self.res_comp_cb.currentIndex()
        res['mode']=self.res_mode_cb.currentIndex()
        npp.set('cur_result',res)
        self._update_vtk()

    def plot_ruc(self,force_update=False):
        """
        Callback function to plot new RUC based on treeWidget selection.

        Parameters:
            force_update (bool): flag to force vtk to update graphics

        Returns:
            None. 
        """

        npp=NASMATPrePost()
        vs=npp.get('vtk_settings')
        ci=npp.get('selected')
        if ci:
            vs[id(ci)]['show_res']=False
            npp.set('vtk_settings',vs)
        self._update_vtk(force_update)


    def get_selected(self):
        """
        Function to get selected item information in treeWidget or treeWidget_Res.

        Parameters:
            None. 

        Returns:
            selected (str): text of selected item
            loc (str): string to indicate which tree item is contained in
            ci (QTreeWidgetItem): selected item
        """

        tabindex=self.tabWidget.currentIndex()
        loc=''
        if tabindex==0:
            self.selected_tree=self.treeWidget
            loc='kw'
        elif tabindex==1:
            self.selected_tree=self.treeWidget_Res
            loc='res'

        ci=self.selected_tree.currentItem()
        if not ci:
            ci=self.selected_tree.topLevelItem(0)
        selected=ci.text(0)

        return selected,loc,ci

    def _update_vtk(self,force_update=False):
        """
        Main function to update vtk graphics.

        Parameters:
            force_update (bool): flag to force vtk to update graphics 

        Returns:
            None. 
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        file = npp.get('cur_file')
        vs = npp.get('vtk_settings')
        old_selected=npp.get('selected')
        npps=npp.get('npp_settings')

        selected,_,ci=self.get_selected()
        npp.set('selected',ci)

        if old_selected==ci:
            update_res_only=False #disabling for now
        else:
            update_res_only=False

        if not old_selected or old_selected == ci:
            self.update_fields = False
        else:
            self.update_fields = True

        vtk_widget=self.findChild(QWidget, "vtk_widget")

        if selected.startswith('MacroAPI'):
            nasmat[file]['ruc_plot_opt']='MacroAPI'
            npp.set('nasmat',nasmat)
            npps = npp.get('npp_settings')
            if vtk_widget:
                if id(ci) not in vs:
                    vs[id(ci)]=get_default_vtk_settings()
                    vs[id(ci)]['PlotMode']='Main'
                    vs['show_res']=False
                    if 'SHOW_AXES' in npps and npps['SHOW_AXES'].upper()=='FALSE':
                        vs[id(ci)]['show_axes']=False
                    elif 'SHOW_AXES' in npps and npps['SHOW_AXES'].upper()=='TRUE':
                        vs[id(ci)]['show_axes']=True
                    if 'SHOW_TITLE' in npps and npps['SHOW_TITLE'].upper()=='FALSE':
                        vs[id(ci)]['show_title']=False
                    elif 'SHOW_TITLE' in npps and npps['SHOW_TITLE'].upper()=='TRUE':
                        vs[id(ci)]['show_title']=True
                if self.plot_h5:
                    if (not npp.get('updated_fields') and vtk_widget.grid) and self.update_fields:
                        vtk_widget.update_fields(macroapi=True)
                        npp.set('updated_fields',True)

                    resitem = self.res_item_cb.currentText()
                    vs[id(ci)]['var']=resitem
                    vs[id(ci)]['comp']=self.res_comp_cb.currentIndex()
                    vs[id(ci)]['show_res']=True
                    if self.res_mode_cb.currentText()=='Aligned with Material':
                        vs[id(ci)]['rotate_to_material']= True
                    else:
                        vs[id(ci)]['rotate_to_material']=False
                npp.set('vtk_settings',vs)
                npp.set('selected',ci)
                vs[id(ci)]['window_text']=selected
                vtk_widget.update(update_res_only=update_res_only)
                npp.set('updated_fields',False)
                return

        if self.res_mode_cb.currentText()=='Aligned with Material':
            vs[id(ci)]['rotate_to_material']= True
        else:
            vs[id(ci)]['rotate_to_material']=False

        vs[id(ci)]['window_text']=selected

        tabindex=self.tabWidget.currentIndex()
        if self.has_macroapi and tabindex==0:
            p=ci
            while not p.text(0).startswith('('):
                p=p.parent()
            deck = str(next(key for key, value in self.deck_map.items()
                            if p.text(0).startswith(value)))
        elif self.has_macroapi and tabindex==1:
            # p=ci.parent().text(0)
            # decknum=p.split('(deck:')[1][:-1]
            p=ci.text(0)
            citm=ci
            while ('(deck:' not in p) and p:
                citm=ci.parent()
                p=citm.text(0)
            decknum=p.split('(deck:')[1].split(')')[0]
            deck=str(decknum)
        else:
            deck=list(nasmat[file]['input'].keys())[0] #fix for now

        npp.set('cur_deck',deck)
        npp.set('nasmat',nasmat)

        if not self.has_macroapi:
            msm=selected.split(',')[0].split('M=')[1]
        else:
            if tabindex==0 and selected.startswith('('): #keyword input
                msm=selected.split(' - ')[2].split('M=')[1]
            else: #result input
                try:
                    msm=selected.split('-')[2].split(',')[0].split('M=')[1]
                except IndexError:
                    msm=selected.split(',')[0].split('M=')[1]

        inp=nasmat[file]['input'][deck]
        selected_ruc=inp['ruc_map'][msm]

        rucs=inp['ruc']['rucs']

        tstr=rucs[msm]['DIM']

        if tstr=='2D':
            nasmat[file]['ruc_plot_opt']='2DR'
        elif tstr=='3D':
            nasmat[file]['ruc_plot_opt']='3DR'
        else:
            nasmat[file]['ruc_plot_opt']='MT'

        if  (nasmat[file]['ruc_plot']!=selected_ruc) or self.plot_h5 or force_update:
            nasmat[file]['ruc_plot']=selected_ruc
            npp.set('nasmat',nasmat)
            hierarchy=npp.get('hierarchy')
            if vtk_widget:
                if self.plot_h5:
                    self.ruc_tree=[]
                    self._get_parents(self.treeWidget_Res.currentItem())

                    ci=self.treeWidget_Res.currentItem()
                    # print('cur item:', ci.text(0))
                    # print('cur index row:', self.treeWidget_Res.indexFromItem(ci).row())
                    # print('cur parent:', ci.parent().text(0))
                    updated_fields=npp.get('updated_fields')
                    if not updated_fields:
                        vtk_widget.update_fields(macroapi=False)

                    vs[id(ci)]['var']=self.res_item_cb.currentText()
                    vs[id(ci)]['comp']=self.res_comp_cb.currentIndex()
                    vs[id(ci)]['show_res']=True
                    txt = self.treeWidget_Res.currentItem().text(0)
                    if not self.has_macroapi:
                        vs[id(ci)]['lvl']=int(txt.split(',')[0].split(' ')[1])
                    else:
                        try:
                            vs[id(ci)]['lvl']=int(txt.split('-')[1].split(',')[0].split(' ')[2])
                        except IndexError:
                            vs[id(ci)]['lvl']=int(txt.split(',')[0].split(' ')[1])

                    ci_txt=ci.text(0)
                    rucid=ci_txt.split('RUCID:')[1]
                    if self.has_macroapi:
                        ci_itm=ci
                        while ci_itm and not ci_itm.text(0).startswith('Macro'):
                            ci_itm=ci_itm.parent()

                        newtxt=ci_itm.text(0)
                        tstr = newtxt.split(' - ')[0]
                        vs[id(ci)]['h5-parent']=tstr.split(' (')[0]

                        vs[id(ci)]['selected_result']=hierarchy['res'][tstr]['items'][rucid]
                    else:
                        vs[id(ci)]['selected_result']=hierarchy['res']['items'][rucid]
                        vs[id(ci)]['h5-parent']=None

                npp.set('vtk_settings',vs)
                vtk_widget.update(update_res_only=update_res_only)
                npp.set('updated_fields',False)

    def _get_parents(self,treeitem):
        """
        Recursive function to get parent of current item.

        Parameters:
            treeitem (QTreeWidgetItem): current item to get parent for 

        Returns:
            None. 
        """

        parent=treeitem.parent()
        if parent:
            self.ruc_tree.insert(0,parent.text(0))
            self._get_parents(parent)
        else:
            self.ruc_tree.insert(0,treeitem.text(0))

    def edit_mac_ui(self):
        """
        Callback function to opening MAC input UI.

        Parameters:
            None. 

        Returns:
            None. 
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr = npp.get('cur_file')
        nd=new_Dialog(self,mac_inp=nasmat[filestr]['input']['0'])
        status=nd.exec()
        if status and nd.mac:
            pass

    def edit_mac_text(self):
        """
        Callback function to opening MAC text input.

        Parameters:
            None. 

        Returns:
            None. 
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        filestr = npp.get('cur_file')

        raw_input=nasmat[filestr]['input']['0']['raw_input']

        d=Edit_text_dialog(self,file=nasmat[filestr]['MACfileName'],raw_input=raw_input)
        status=d.exec()
        if status:
            lines=d.text.split('\n')
            new_input=[line+'\n' for line in lines]
            nasmat[filestr]['MACfileName']=nasmat[filestr]['MACfileName'][:-4]+'_1.MAC'
            mi = mac_inp(name=nasmat[filestr]['MACfileName'],\
                     raw_input=new_input,echo=False)
            nasmat[filestr]['input']={}
            nasmat[filestr]['input']['0'] = mi.mac
            npp.set('nasmat',nasmat)
            #Update hierarchies in case data changed
            self._update_hierarchy()
            self.RUC_tab.adjustSize()
            self.Results_tab.adjustSize()
            self.tabWidget.adjustSize()
            self.plot_ruc(force_update=True)

    def sync_3d_cameras(self,by_ruc=False):
        """
        Callback function set sync 3D cameras.

        Parameters:
            by_ruc (bool): flag to sync cameras of all similar RUCs 

        Returns:
            None. 
        """

        vtk_widget=self.findChild(QWidget, "vtk_widget")
        if vtk_widget:
            pass

        npp=NASMATPrePost()
        vs = npp.get('vtk_settings')
        ci=npp.get('selected')
        cam_fp = vs[id(ci)]['camera-focal-point']
        cam_pos = vs[id(ci)]['camera-position']
        cam_up = vs[id(ci)]['camera-view-up']

        tree = ci.treeWidget().objectName()
        if tree=='treeWidget':
            current_ruc = ci.text(1)
        else:
            txt = ci.text(0)
            current_ruc = txt[txt.find("(") + 1 : txt.rfind(")")]

        for mem_id,item in self.treeitems_by_id.items():
            sync = False
            if item==ci: #skip current item
                continue

            sel_txt = item.text(0)
            if sel_txt.startswith('Macro E:'):
                dflag = sel_txt.split(' - ')[1].split(' ')[2]
            else:
                dflag = sel_txt.split(',')[0].split(' ')[2]

            if dflag=='MT':
                dflag='2D'

            current_tree = item.treeWidget().objectName()
            if by_ruc and dflag=='3D':
                if current_tree=='treeWidget':
                    ruc = item.text(1)
                else:
                    ruc = sel_txt[sel_txt.find("(") + 1 : sel_txt.rfind(")")]

                if ruc==current_ruc:
                    sync=True

            elif not by_ruc and dflag=='3D':
                sync=True

            if sync:
                vs[mem_id]['camera-focal-point'] = cam_fp
                vs[mem_id]['camera-position'] = cam_pos
                vs[mem_id]['camera-view-up'] = cam_up

    def sync_3d_cameras_by_ruc(self):
        """
        Callback function set sync 3D cameras by RUC.

        Parameters:
            None. 

        Returns:
            None. 
        """

        self.sync_3d_cameras(by_ruc=True)

    def set_colors(self):
        """
        Callback function set set UI colors.

        Parameters:
            None. 

        Returns:
            None. 
        """

        if self.colors:
            c=color_Dialog(self,colors=self.colors)
        else:
            c=color_Dialog(self,colors={'background':[0.8, 0.88, 0.92],'colormap':0})
        status=c.exec()
        if status: #dialog closed, can be used to do another action
            npp=NASMATPrePost()
            vs=npp.get('vtk_settings')
            ci=npp.get('selected')
            npps=npp.get('npp_settings')

            npps['COLORMAP']=c.colors['colormap']
            npps['BACKGROUND_COLOR']=c.colors['background']
            npp.set('npp_settings',npps)

            self.colors=c.colors
            vtk_widget=self.findChild(QWidget, "vtk_widget")
            vtk_widget.set_background_color(c.colors['background'])
            if vtk_widget and hasattr(self,'vtk_settings'):
                vs[id(ci)]['cmap']=c.colors['colormap']
                npp.set('vtk_settings',vs)
                #vtk_widget.update()

    def show_about_npp(self):
        """
        Callback function to display About NASMAT PrePost info.

        Parameters:
            None. 

        Returns:
            None. 
        """

        w=ShowMd(file="./README.md")
        status=w.exec()
        if status:
            pass

    def show_about_lic(self):
        """
        Callback function to display About License info.

        Parameters:
            None. 

        Returns:
            None. 
        """

        w=ShowMd(file="./LICENSE")
        status=w.exec()
        if status:
            pass

if __name__ == "__main__":

    app = QApplication([])
    widget = Main()
    widget.show()
    sys.exit(app.exec_())
