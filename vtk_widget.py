"""primary widget and functions to define vtk visualizations"""
# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle # pylint: disable=W0611
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2 # pylint: disable=W0611
from vtkmodules.vtkRenderingCore import vtkRenderer,vtkCellPicker # pylint: disable=E0611
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera # pylint: disable=E0611
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid # pylint: disable=E0611
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor # pylint: disable=E0401,E0611
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication,QTabWidget,QTreeWidget,QWidget,QComboBox # pylint: disable=E0611

from vtk_plot import VtkPlot
from Gen_VTK_Plot_2DWeave import Gen_VTK_Plot_2DWeave
from util.cell_id_to_indices import cell_id_to_indices

from NASMAT_PrePost import NASMATPrePost

class vtk_widget(QtWidgets.QWidget):  #pylint: disable=I1101,C0103,R0902
    """ used to create vtk visualizations and allow interactions"""
    arrow_picked = QtCore.pyqtSignal(float)  #pylint: disable=I1101

    def __init__(self, parent=None, sweep=None):
        """
        initialize class

        Parameters:
            parent (class): self from parent calling this class
        
        Returns:
            None.
        """

        super().__init__(parent)

        # Make the actual QtWidget a child so that it can be re parented
        interactor = QVTKRenderWindowInteractor()
        self.layout = QtWidgets.QHBoxLayout() #pylint: disable=I1101
        self.layout.addWidget(interactor, 0, QtCore.Qt.Alignment()) #pylint: disable=I1101
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.update_res_only=False
        #Add new variables for mapping as desired.
        #Primarily used for switching between NASMAT and MacroAPI results
        self.var_map = {'E':'Strain','S':'Stress','Strain':'E','Stress':'S'}

        renderer = vtkRenderer()
        render_window = interactor.GetRenderWindow()
        render_window.AddRenderer(renderer)
        if parent and parent.objectName()!='woven2d_dialog':
            self.from_main=True
        else:
            self.from_main=False

        self.style = MouseInteractorStyle(vtkw=self)
        interactor.SetInteractorStyle(self.style)

        self.cellpicker = vtkCellPicker()
        self.cellpicker.SetTolerance(0.001)
        interactor.SetPicker(self.cellpicker)

        self.grid=None
        self.vp = None
        self.clip_box_widget=None
        self.clip_box_actor=None
        self.clip_box_init=None

        render_window.SetInteractor(interactor)
        # renderer.SetBackground(0.2, 0.2, 0.2)
        renderer.SetBackground(0.80, 0.88, 0.92)

        self.renderer = renderer
        self.interactor = interactor
        self.interactor.Initialize()
        self.interactor.Start()
        if self.from_main:
            self.interactor.AddObserver('LeftButtonPressEvent',self.left_click_callback)
            self.interactor.AddObserver('RightButtonPressEvent',self.right_click_callback)
            self.interactor.AddObserver("KeyPressEvent", self.on_key_press)
            self.interactor.AddObserver("KeyReleaseEvent", self.on_key_release)

        self.render_window = render_window

    def update_fields(self,macroapi):
        """
        Function to update fields QComboBox when switching between levels.
        Primarily accounts for differences between NASMAT and MacroAPI field names.

        Parameters:
            macroapi (bool): flag to set variables based on MacroAPI input or NASMAT
        
        Returns:
            None.
        """

        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        file = npp.get('cur_file')
        parent=self.parent()

        res_item_cb=parent.findChild(QComboBox, "res_item_cb")
        res_item_cb.blockSignals(True)
        current_var=res_item_cb.currentText()
        res_item_cb.clear()
        h5=nasmat[file]['input']['h5']
        if macroapi:
            items=h5.get_h5_fields_api()
        else:
            items=h5.get_h5_fields()
        res_item_cb.addItems(items)

        selected = npp.get('selected')
        txt=selected.text(0)
        if txt.startswith('MacroAPI'):
            try:
                ind=res_item_cb.findText(self.var_map[current_var])
            except KeyError:
                ind=0
                print(f"Warning: Mapping for {current_var} not defined in var_map!")
        else:
            ind=res_item_cb.findText(current_var)
            if ind==-1:
                ind=res_item_cb.findText(self.var_map[current_var])

        res_item_cb.setCurrentIndex(ind)
        res_item_cb.blockSignals(False)

    def left_click_callback(self, _, __):
        """
        Function defining left-click behavior
        Go to lower level when cell is clicked if present

        Parameters:
            None.
        
        Returns:
            None.
        """

        click_pos = self.interactor.GetEventPosition()
        self.cellpicker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        picked_cell_id = self.cellpicker.GetCellId()
        # print('widget.py: picked cell: ', picked_cell_id)
        if picked_cell_id != -1:
            #account for case where edges are hovered over (vtkPolyData objects)
            dataset = self.cellpicker.GetDataSet()
            if not isinstance(dataset, vtkUnstructuredGrid):
                return

            npp=NASMATPrePost()
            vs = npp.get('vtk_settings')
            selected = npp.get('selected')
            # print('selected: ', selected)
            current_inc=vs[id(selected)]['ind']

            sel_txt=selected.text(0)
            macroapi=sel_txt.startswith('MacroAPI Mesh')

            #3 Cases selected[0] can start with: 1) MacroAPI Mesh selected, 2) Macro E:#, 3) Level #
            if sel_txt.startswith('MacroAPI Mesh'):
                dflag='3D'
            elif sel_txt.startswith('Macro E:'):
                dflag = sel_txt.split(' - ')[1].split(' ')[2]
            else:
                dflag = sel_txt.split(',')[0].split(' ')[2]

            if dflag=='MT':
                dflag='2D'

            parent=self.parent()
            tabwidget=parent.findChild(QTabWidget, "tabWidget")
            tabindex=tabwidget.currentIndex()
            key_input = True
            selected_tree = None
            if tabindex==0:
                selected_tree=tabwidget.findChild(QWidget, "RUC_tab").\
                                findChild(QTreeWidget, "treeWidget")
            elif tabindex==1:
                selected_tree=tabwidget.findChild(QWidget, "Results_tab").\
                                findChild(QTreeWidget, "treeWidget_Res")
                key_input=False

            #TODO: verify key_input logic
            # Grid=self.get_grid_from_renderer()
            cids=self.grid.GetCellData().GetArray('vtkOriginalCellIds')
            actual_cell_id=cids.GetValue(picked_cell_id)
            ix,iy,iz = cell_id_to_indices(actual_cell_id,self.grid,
                                        irregular=macroapi,key_input=key_input)


            if not macroapi and dflag=='2D':
                ind=[iz,iy,ix]
            elif not macroapi and dflag=='3D':
                ind=[ix,iy,iz]
            else:
                ind=ix
            # print('selected subvol indices: ', ind)

            nasmat = npp.get('nasmat')
            file = npp.get('cur_file')
            npp.set('updated_fields',False)

            if not macroapi:
                txt=selected.text(0)
                if 'RUCID:' in txt:
                    rucid=txt.split('RUCID:')[1]
                    rid=nasmat[file]['input']['0']['rucid'][rucid]
                    newrucid=rid[tuple(ind)]
                else:
                    if nasmat[file]['input']['0']['mat_map'][ix]>0:
                        newrucid=-1
                    else:
                        newrucid=ix

                if newrucid!=-1:
                    # selected_tree = None
                    for i in range(selected.childCount()):
                        item = selected.child(i)
                        item_txt=item.text(0)
                        if 'RUCID:' in item_txt:
                            rucid_chk = int(item_txt.split('RUCID:')[1])
                        elif item_txt.startswith('('):
                            rucid_chk=int(item_txt.split(')')[0][1:])
                        else:
                            m=int(item_txt.split('=')[1]) #get M
                            rucid_chk=nasmat[file]['input']['0']['rev_mat_map'][m]

                        if rucid_chk == newrucid:
                            vs[id(item)]['ind']=current_inc
                            npp.set('vtk_settings',vs)
                            if tabindex==1:
                                self.update_fields(macroapi=False)
                                npp.set('updated_fields',True)

                            selected_tree.setCurrentItem(item)
                            break
            else:

                for i in range(selected.childCount()):
                    item = selected.child(i)
                    first_cond=item.text(0).startswith(f"Macro E:{ind},IP: {1}")
                    sec_cond = item.text(0).startswith(f"({ind+1})")
                    if first_cond or sec_cond: #only setup for one int. pt.
                        vs[id(item)]['ind']=current_inc
                        npp.set('vtk_settings',vs)
                        if tabindex==1:
                            self.update_fields(macroapi=False)
                            npp.set('updated_fields',True)

                        selected_tree.setCurrentItem(item)
                        break

    def right_click_callback(self, _, __):
        """
        Function defining right-click behavior
        Go to previous level when cell is clicked

        Parameters:
            None.
        
        Returns:
            None.
        """

        parent=self.parent()
        tabwidget=parent.findChild(QTabWidget, "tabWidget")
        tabindex=tabwidget.currentIndex()
        selected_tree = None
        if tabindex==0:
            selected_tree=tabwidget.findChild(QWidget, "RUC_tab").\
                            findChild(QTreeWidget, "treeWidget")
        elif tabindex==1:
            selected_tree=tabwidget.findChild(QWidget, "Results_tab").\
                            findChild(QTreeWidget, "treeWidget_Res")

        item=selected_tree.currentItem()
        if item:
            parent=item.parent()
        else:
            parent=None

        npp=NASMATPrePost()
        npp.set('updated_fields',False)
        if parent:
            vs = npp.get('vtk_settings')
            vs[id(parent)]['ind']=vs[id(item)]['ind']
            npp.set('vtk_settings',vs)
            if tabindex==1:
                npp.set('selected',parent)
                if parent.text(0).startswith('MacroAPI'):
                    self.update_fields(macroapi=True)
                else:
                    self.update_fields(macroapi=False)
                npp.set('updated_fields',True)

            selected_tree.setCurrentItem(parent)

    def on_key_press(self, obj, _):
        """
        Function defining key-press behaviors

        Parameters:
            None.
        
        Returns:
            None.
        """

        key = obj.GetKeySym()
        if key in ("Alt_L","Alt_R"): #show the clipper widget
            self.clip_box_widget.On()
            self.clip_box_actor.VisibilityOn()
        elif key=='r': #reset the clipper widget
            if self.vp:
                self.clip_box_widget.PlaceWidget(self.clip_box_init)
                self.vp.set_clipper(new_bounds=self.clip_box_init)
        elif key=='1': #reset camera to default view
            if self.vp:
                npp=NASMATPrePost()
                vs = npp.get('vtk_settings')
                selected = npp.get('selected')
                renderer = self.render_window.GetRenderers().GetFirstRenderer()
                camera = renderer.GetActiveCamera()
                camera.DeepCopy(vs[id(selected)]['default_camera'])
                renderer.ResetCameraClippingRange()

        self.render_window.Render()

    def on_key_release(self, obj, _):
        """
        Function defining key-release behaviors

        Parameters:
            None.
        
        Returns:
            None.
        """

        key = obj.GetKeySym()
        if key in ("Alt_L","Alt_R"):  # Left or Right Alt key
            self.clip_box_widget.Off()  # Hide and deactivate the box widget
            self.clip_box_actor.VisibilityOff()  # Hide the outline actor
            self.render_window.Render()

    def update(self,update_res_only=False,sweep=None):
        """
        Primary functon to update vtk visualizations

        Parameters:
            update_res_only (bool): flag to only update array rather than re-create grids
            sweep (tuple): two ints used to define starting and stopping indices
                           for making videos
        Returns:
            None.
        """


        npp=NASMATPrePost()
        nasmat = npp.get('nasmat')
        file = npp.get('cur_file')
        deck = npp.get('cur_deck')
        vs = npp.get('vtk_settings')
        ci = npp.get('selected')

        self.update_res_only=update_res_only

        m1 = {}

        if vs[id(ci)]['PlotMode']=='Main':
            vs[id(ci)]['plot_opt']=nasmat[file]['ruc_plot_opt']

            if vs[id(ci)]['plot_opt']=='MacroAPI':
                m1['h5']=nasmat[file]['input']['h5']
                m1['HideMat'] = nasmat[file]['hide_mat']
                ruc={}
                self.vp=VtkPlot(opt=vs[id(ci)]['plot_opt'],ruc=ruc, h5=m1['h5'].file,
                                 hidemat=m1['HideMat'],rw=self.render_window, vs=vs[id(ci)],
                                 update_res_only=update_res_only,sweep=sweep)
                self.vp.start()
                self.vp.set_clipper(new_bounds=vs[id(ci)]['slicer-bounds'])
                self.grid=self.vp.grid
                self.clip_box_widget,self.clip_box_actor,self.clip_box_init=self.vp.get_clipper()

            else:
                m = nasmat[file]['input'][deck]
                vs[id(ci)]['ruc_plot']=nasmat[file]['ruc_plot']
                ruc_id=nasmat[file]['ruc_plot']
                for key, val in m['ruc_map'].items():
                    if val==ruc_id:
                        ruc_num=key
                        break

                m1['Ori'] = []

                if 'h5' in m:
                    h5 = m['h5']
                elif 'h5' in nasmat[file]['input'].keys():
                    h5=nasmat[file]['input']['h5']
                else:
                    h5=None

                ruc=m['ruc']['rucs'][ruc_num]

                if ruc['DIM']!='3D':
                    vs[id(ci)]['rotate_grid']=False #disable grid rotations

                self.vp=VtkPlot(opt=vs[id(ci)]['plot_opt'], ruc=ruc, h5=h5,
                                 hidemat=nasmat[file]['hide_mat'], rw=self.render_window,
                                 vs=vs[id(ci)],update_res_only=update_res_only,sweep=sweep)
                self.vp.start()
                self.vp.set_clipper(new_bounds=vs[id(ci)]['slicer-bounds'])
                self.grid=self.vp.grid
                self.clip_box_widget,self.clip_box_actor,self.clip_box_init=self.vp.get_clipper()

        elif vs[id(ci)]['PlotMode']=='Woven2D':
            vs[id(ci)]['rotate_grid']=False #disable grid rotations
            vp=Gen_VTK_Plot_2DWeave(vs[id(ci)]['tmp_2Dweave'], self.render_window,
                                    show_mats=vs[id(ci)]['show_mats'])
            self.grid=vp.grid

    def get_camera(self):
        """
        Function getting camera parameters

        Parameters:
            None.
        
        Returns:
            None.
        """

        renderer=self.render_window.GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        cam={}
        cam['camera-focal-point']=camera.GetFocalPoint()
        cam['camera-position']=camera.GetPosition()
        cam['camera-view-up']=camera.GetViewUp()
        return cam

    def set_background_color(self,color):
        """
        Function to set and update background color

        Parameters:
            color (list): 3 floats (RGB values) for color
        
        Returns:
            None.
        """
        self.renderer.SetBackground(*color)
        self.render_window.Render()
        self.interactor.Render()

    def closeEvent(self, event): #pylint: disable=C0103
        """
        Function defining close event behavior

        Parameters:
            event (QCloseEvent): pyqt close event
        
        Returns:
            None.
        """

        super().closeEvent(event)
        self.render_window.GetInteractor().ExitCallback()

#*****************************************************************************
class MouseInteractorStyle(vtkInteractorStyleTrackballCamera):
    """defining mouse interaction behavior for vtk_widget"""
    def __init__(self,vtkw=None):
        """
        initialize class

        Parameters:
            vtkw (vtk_widget): class passed in to have data access
        
        Returns:
            None.
        """

        self.vtkw=vtkw
        if self.vtkw.from_main:
            self.AddObserver("LeftButtonPressEvent", self.leftbuttonpressevent)
            self.AddObserver('LeftButtonReleaseEvent', self.leftbuttonreleaseevent)

    def leftbuttonpressevent(self, _, __):
        """
        Defines left-button press behavior to control camera rotations

        Parameters:
            None.
        
        Returns:
            None.
        """

        npp=NASMATPrePost()
        vs = npp.get('vtk_settings')
        item=id(npp.get('selected'))
        try:
            if vs[item]['rotate_grid']:
                self.OnLeftButtonDown()
        except KeyError:
            pass

    def leftbuttonreleaseevent(self, _, __):
        """
        Defines left-button release behavior to get/set camera parameters

        Parameters:
            None.
        
        Returns:
            None.
        """

        cam=self.vtkw.get_camera()
        # print('cam: ', cam)
        npp=NASMATPrePost()
        vs = npp.get('vtk_settings')
        item=id(npp.get('selected'))

        try:
            vs[item]['camera-focal-point']=cam['camera-focal-point']
            vs[item]['camera-position']=cam['camera-position']
            vs[item]['camera-view-up']=cam['camera-view-up']
        except KeyError:
            pass

        npp.set('vtk_settings',vs)
        self.OnLeftButtonUp()
#*****************************************************************************
if __name__ == "__main__":
    import sys

    # section will not work, no MAC input
    app = QApplication(sys.argv)
    w = vtk_widget()
    w.show()
    sys.exit()
